#!/usr/bin/env python
#------------------------------------------------
# Filename: GUI.py
#   Author: Arnav Sankaran
#    Email: arnavsankaran@gmail.com
#
# Copyright (c) 2016 Arnav Sankaran
#------------------------------------------------
from PyQt4.QtGui import *
from PyQt4.QtCore import *

import pyqtgraph as pg

import sys
import os
import webbrowser

from seismodata import getWaveDataSetFromSacItem
from algiccs import ccWeightStack, checkCoverage
from algmccc import eventListName, mccc
from sacpickle import taperWindow, saveData
from qualsort import seleSeis, sortSeisQual, sortSeisHeader, sortSeisHeaderDiff
import filtering
import utils

import numpy as np
from numpy import nan


class mainGUI(object):
	def __init__(self, sacgroup, opts):
		self.application = QApplication(sys.argv)
		self.window = QWidget()
		self.window.setWindowTitle('ttpick')
		self.window.show()
		self.layout = QGridLayout(self.window)

		self.sacgroup = sacgroup
		self.opts = opts

		if not hasattr(self.sacgroup, 'selist'):
			self.sacgroup.selist = []
			self.sacgroup.delist = []
			for sacitem in self.sacgroup.saclist:
				self.sacgroup.selist.append(sacitem)

		self.stkdh = None
		self.stackedPlot = None

		self.plotList = []

		self.gfxWidget = None

	def setupGUI(self):
		self.gfxWidget = self.getPlotGraphicsLayoutWindow(1800, 100 * len(self.sacgroup.saclist))
		scrollArea = QScrollArea()
		scrollArea.setWidget(self.gfxWidget)
		self.addWidget(scrollArea, 1, 0, xSpan = 1, ySpan = 10)
		self.putButtons()

		self.opts.sortby = 'all'
		self.sortSeis()
		self.reorderPlots()

		self.gfxWidget.scene().sigMouseClicked.connect(self.mouseClickEvents)

		# Set mouse mode so user can drag a box on the stacked plot to select cross correlation window
		stackedVB = self.stackedPlot.getViewBox()
		stackedVB.setMouseMode(stackedVB.RectMode)
		stackedVB.sigXRangeChanged.connect(self.setWindow)

	def setWindow(self, arg):
		timewindow = arg.state['viewRange'][0]
		self.scalePlotYRange(self.stackedPlot)

		# Don't update window if plot is autosizing to fit all data
		waveData = getWaveDataSetFromSacItem(self.stkdh, self.opts).x
		if timewindow[1] - timewindow[0] > waveData[-1] - waveData[0]:
			return
		# Don't update window if plot is autosizing to fit around t2
		hdrini, hdrmed, hdrfin = self.opts.qcpara.ichdrs
		if self.stkdh.gethdr(hdrfin) != -12345.0:
			if self.stkdh.gethdr(hdrfin) - 30 - 5 <= timewindow[0] <= self.stkdh.gethdr(hdrfin) - 30 + 5:
				return
			elif self.stkdh.gethdr(hdrfin) + 30 - 5 <= timewindow[1] <= self.stkdh.gethdr(hdrfin) + 30 + 5:
				return

		twh0, twh1 = self.opts.pppara.twhdrs
		self.stkdh.sethdr(twh0, timewindow[0])
		self.stkdh.sethdr(twh1, timewindow[1])

		out = 'File {:s}: set time window to {:s} and {:s}: {:6.1f} - {:6.1f} s'
		print(out.format(self.stkdh.filename, twh0, twh1, timewindow[0], timewindow[1]))

	def getPlotGraphicsLayoutWindow(self, xSize, ySize):
		gfxWidget = pg.GraphicsLayoutWidget()
		gfxWidget.resize(xSize, ySize)
		gfxWidget.ci.setSpacing(0)

		# Create stacked plot
		hdrini, hdrmed, hdrfin = self.opts.qcpara.ichdrs
		if 'stkdh' in self.sacgroup.__dict__:
			stkdh = self.sacgroup.stkdh
		else:
			self.opts.ccpara.cchdrs = [hdrini, hdrmed]
			self.twcorr = self.opts.ccpara.twcorr
			self.opts.ipick = hdrini
			self.opts.twcorr = self.opts.ccpara.twcorr
			checkCoverage(self.sacgroup, self.opts)
			stkdh, stkdata, quas = ccWeightStack(self.sacgroup.saclist, self.opts)
		
		self.stkdh = stkdh
		dataSet = getWaveDataSetFromSacItem(stkdh, self.opts)
		plt = gfxWidget.addPlot(title = dataSet.name)
		plt.plot(dataSet.x, dataSet.y, fillLevel = 0, fillBrush = utils.convertToRGBA(self.opts.pppara.colorwave, 75))
		plt.curves[0].selected = True
		plt.hideAxis('bottom')
		plt.hideAxis('left')
		plt.sacdh = stkdh
		plt.sacdh.selected = True

		self.addTimePick(plt, stkdh.gethdr(hdrini), hdrini)
		self.addTimePick(plt, stkdh.gethdr(hdrmed), hdrmed)
		if stkdh.gethdr(hdrfin) != -12345.0:
			self.addTimePick(plt, stkdh.gethdr(hdrfin), hdrfin)
			plt.setXRange(self.opts.ccpara.twcorr[0] + plt.sacdh.gethdr(hdrfin), self.opts.ccpara.twcorr[1] + plt.sacdh.gethdr(hdrfin))

		plt.setXRange(stkdh.gethdr(hdrmed) + self.opts.xlimit[0], stkdh.gethdr(hdrmed) + self.opts.xlimit[1])
		self.scalePlotYRange(plt)

		plt.setTitle(plt.titleLabel.text, color = utils.convertToRGBA(self.opts.pppara.colorwave, 75))

		self.stackedPlot = plt

		gfxWidget.nextRow()

		# Create plots for other seismograms
		index = 0
		for sacitem in self.sacgroup.saclist:
			dataSet = getWaveDataSetFromSacItem(sacitem, self.opts)
			plt = gfxWidget.addPlot(title = dataSet.name)

			brush = None
			isSelected = None

			if sacitem in self.sacgroup.selist:
				brush = utils.convertToRGBA(self.opts.pppara.colorwave, 75)
				isSelected = True

				plt.setTitle(plt.titleLabel.text, color = utils.convertToRGBA(self.opts.pppara.colorwave, 75))
			else:
				brush = utils.convertToRGBA(self.opts.pppara.colorwavedel, 75)
				isSelected = False

				plt.setTitle(plt.titleLabel.text, color = utils.convertToRGBA(self.opts.pppara.colorwavedel, 75))

			plt.plot(dataSet.x, dataSet.y, fillLevel = 0, fillBrush = brush)
			plt.curves[0].selected = isSelected
			plt.index = index
			plt.hideAxis('bottom')
			plt.hideAxis('left')
			plt.sacdh = sacitem
			plt.sacdh.selected = isSelected

			self.addTimePick(plt, sacitem.gethdr(hdrini), hdrini)
			self.addTimePick(plt, sacitem.gethdr(hdrmed), hdrmed)
			if sacitem.gethdr(hdrfin) != -12345.0:
				self.addTimePick(plt, sacitem.gethdr(hdrfin), hdrfin)
				plt.setXRange(self.opts.ccpara.twcorr[0] + plt.sacdh.gethdr(hdrfin), self.opts.ccpara.twcorr[1] + plt.sacdh.gethdr(hdrfin))

			plt.setXRange(sacitem.gethdr(hdrmed) + self.opts.xlimit[0], sacitem.gethdr(hdrmed) + self.opts.xlimit[1])
			self.scalePlotYRange(plt)

			gfxWidget.nextRow()
			index += 1
			self.plotList.append(plt)
		self.window.resize(xSize + 55, ySize)

		return gfxWidget

	def addWidget(self, widget, xLoc, yLoc, xSpan = 1, ySpan = 1):
		self.layout.addWidget(widget, xLoc, yLoc, xSpan, ySpan)

	def putButtons(self):
		alignbtn = QPushButton('Align')
		syncbtn = QPushButton('Sync')
		refinebtn = QPushButton('Refine')
		finalizebtn = QPushButton('Finalize')
		savebtn = QPushButton('Save')
		quitbtn = QPushButton('Quit')
		sacp2btn = QPushButton('Sac P2')
		sortbtn = QPushButton('Sort')
		filterbtn = QPushButton('Filter')
		mapstationsbtn = QPushButton('Map Stations')

		alignbtn.clicked.connect(self.alignButtonClicked)
		syncbtn.clicked.connect(self.syncButtonClicked)
		refinebtn.clicked.connect(self.refineButtonClicked)
		finalizebtn.clicked.connect(self.finalizeButtonClicked)
		quitbtn.clicked.connect(self.quitButtonClicked)
		savebtn.clicked.connect(self.saveButtonClicked)
		sortbtn.clicked.connect(self.sortButtonClicked)
		sacp2btn.clicked.connect(self.sacp2ButtonClicked)
		filterbtn.clicked.connect(self.filterButtonClicked)
		mapstationsbtn.clicked.connect(self.mapstationsButtonClicked)

		self.addWidget(alignbtn, 0, 1)
		self.addWidget(syncbtn, 0, 2)
		self.addWidget(refinebtn, 0, 3)
		self.addWidget(finalizebtn, 0, 4)
		self.addWidget(savebtn, 0, 8)
		self.addWidget(quitbtn, 0, 9)
		self.addWidget(sacp2btn, 0, 6)
		self.addWidget(sortbtn, 0, 5)
		self.addWidget(filterbtn, 0, 0)
		self.addWidget(mapstationsbtn, 0, 7)

	def mouseClickEvents(self, event):
		plotItemClicked = None
		for item in self.gfxWidget.scene().items(event.scenePos()):
			if isinstance(item, pg.graphicsItems.PlotItem.PlotItem):
				plotItemClicked = item

		# If double click add t2 time
		hdrini, hdrmed, hdrfin = self.opts.qcpara.ichdrs
		if event.double():
			plotVB = plotItemClicked.getViewBox()
			xpoint = plotVB.mapToView(event.pos()).x()
			self.addTimePick(plotItemClicked, xpoint, hdrfin)

			if plotItemClicked is self.stackedPlot:
				hdrini, hdrmed, hdrfin = self.opts.qcpara.ichdrs
				self.stkdh.sethdr(hdrfin, xpoint)
			else:
				plotItemClicked.sacdh.thdrs[2] = xpoint
				plotItemClicked.sacdh.sethdr(hdrfin, xpoint)

		# If single click select / deselect a plot
		if plotItemClicked is self.stackedPlot:
			return

		if plotItemClicked.sacdh.selected:
			for curve in plotItemClicked.curves:
				curve.setFillBrush(utils.convertToRGBA(self.opts.pppara.colorwavedel, 75))
				curve.selected = False
			plotItemClicked.setTitle(plotItemClicked.titleLabel.text, color = utils.convertToRGBA(self.opts.pppara.colorwavedel, 75))
			plotItemClicked.sacdh.selected = False
			self.sacgroup.selist.remove(plotItemClicked.sacdh)
			self.sacgroup.delist.append(plotItemClicked.sacdh)
		else:
			for curve in plotItemClicked.curves:
				curve.setFillBrush(utils.convertToRGBA(self.opts.pppara.colorwave, 75))
				curve.selected = True
			plotItemClicked.setTitle(plotItemClicked.titleLabel.text, color = utils.convertToRGBA(self.opts.pppara.colorwave, 75))
			plotItemClicked.sacdh.selected = True
			self.sacgroup.delist.remove(plotItemClicked.sacdh)
			self.sacgroup.selist.append(plotItemClicked.sacdh)

	def scalePlotYRange(self, plt):
		# Set plot y range to min and max y values on the visual x range
		xRange = plt.viewRange()[0]
		dataSet = getWaveDataSetFromSacItem(plt.sacdh, self.opts)
		startXIndex = 0
		endXIndex = len(dataSet.x)
		for index in xrange(0, len(dataSet.x)):
			startXIndex = index
			if dataSet.x[index] > xRange[0]:
				break
		for index in xrange(len(dataSet.x) - 1, -1, -1):
			endXIndex = index
			if dataSet.x[index] < xRange[1]:
				break
		yData = dataSet.y[startXIndex : endXIndex]
		plt.setYRange(min(yData), max(yData))

	def alignButtonClicked(self):
		hdrini, hdrmed, hdrfin = self.opts.qcpara.ichdrs
		self.opts.ccpara.cchdrs = hdrini, hdrmed

		self.getWindow(self.opts.ccpara.cchdrs[0])
		self.ccStack()
		self.getPicks()

		# Recreate stacked plot
		self.stackedPlot.clearPlots()
		dataSet = getWaveDataSetFromSacItem(self.stkdh, self.opts)
		self.stackedPlot.plot(dataSet.x, dataSet.y, fillLevel = 0, fillBrush = utils.convertToRGBA(self.opts.pppara.colorwave, 75))
		self.stackedPlot.curves[0].selected = True
		self.stackedPlot.hideAxis('bottom')
		self.stackedPlot.hideAxis('left')

		hdrini, hdrmed, hdrfin = self.opts.qcpara.ichdrs
		self.addTimePick(self.stackedPlot, self.stkdh.gethdr(hdrini), hdrini)
		self.addTimePick(self.stackedPlot, self.stkdh.gethdr(hdrmed), hdrmed)
		for plt in self.plotList:
			self.addTimePick(plt, plt.sacdh.gethdr(hdrini), hdrini)
			self.addTimePick(plt, plt.sacdh.gethdr(hdrmed), hdrmed)

	def syncButtonClicked(self):
		hdrini, hdrmed, hdrfin = self.opts.qcpara.ichdrs
		wh0, wh1 = self.opts.qcpara.twhdrs
		if self.stkdh.gethdr(hdrfin) == -12345.:
			print '*** hfinal %s is not defined. Pick at array stack first! ***' % hdrfin
			return

		self.syncPick()
		self.syncWindow()

		self.stackedPlot.setXRange(self.stkdh.gethdr(hdrfin) + self.opts.xlimit[0], self.stkdh.gethdr(hdrfin) + self.opts.xlimit[1])

		twfin = self.opts.ccpara.twcorr
		for plt in self.plotList:
			sacdh = plt.sacdh
			tfin = sacdh.gethdr(hdrfin)
			ipk = int(hdrfin[1])
			# tpk = tfin - sacdh.reftime
			tpk = tfin
			self.addTimePick(plt, tpk, hdrfin)
			th0 = tfin + twfin[0]
			th1 = tfin + twfin[1]
			wh0, wh1 = self.opts.qcpara.twhdrs
			w0 = sacdh.gethdr(wh0)
			w1 = sacdh.gethdr(wh1)
			plt.setXRange(w0, w1)
		print '--> Sync final time picks and time window... You can now run CCFF to refine final picks.'

	def refineButtonClicked(self):
		hdrini, hdrmed, hdrfin = self.opts.qcpara.ichdrs

		if self.stkdh.gethdr(hdrfin) == -12345.:
			print '*** hfinal %s is not defined. Sync first! ***' % hdrfin
			return

		self.opts.ccpara.cchdrs = hdrfin, hdrfin
		self.getWindow(self.opts.ccpara.cchdrs[0])
		self.getPicks()
		self.ccStack()
		stkdh = self.stkdh
		stkdh.sethdr(hdrini, self.tini)
		stkdh.sethdr(hdrmed, self.tmed)

	def finalizeButtonClicked(self):
		self.getWindow(self.opts.mcpara.ipick)
		tw = self.opts.ccpara.twcorr[1] - self.opts.ccpara.twcorr[0]
		taperwindow = taperWindow(self.opts.ccpara.twcorr, self.opts.mcpara.taperwidth)
		self.opts.mcpara.timewindow = self.opts.ccpara.twcorr
		self.opts.mcpara.taperwindow = taperwindow
		evline, mcname = eventListName(self.sacgroup.event, self.opts.mcpara.phase)
		self.opts.mcpara.evline = evline
		self.opts.mcpara.mcname = mcname
		self.opts.mcpara.kevnm = self.sacgroup.kevnm

		# move stkdh into sacgroup
		self.sacgroup.stkdh = self.stkdh

		solution, solist_LonLat, delay_times = mccc(self.sacgroup, self.opts.mcpara)
		self.sacgroup.solist_LonLat = solist_LonLat
		self.sacgroup.delay_times = delay_times

		wpk = int(self.opts.mcpara.wpick[1])
		if self.opts.reltime != wpk:
			out = '\n--> change opts.reltime from %i to %i'
			print out % (self.opts.reltime, wpk)
		self.opts.reltime = wpk

	def saveButtonClicked(self):
		# move stacked sacfile into sacgroup
		self.sacgroup.stkdh = self.stkdh

		# write params to user headers of sac files
		for sacdh in self.sacgroup.saclist: 
			sacdh.user0 = self.opts.filterParameters['lowFreq']
			sacdh.user1 = self.opts.filterParameters['highFreq']
			sacdh.kuser0 = self.opts.filterParameters['band']
			sacdh.kuser1 = self.opts.filterParameters['order']
		if 'stkdh' in self.sacgroup.__dict__:
			self.sacgroup.stkdh.user0 = self.opts.filterParameters['lowFreq']
			self.sacgroup.stkdh.user1 = self.opts.filterParameters['highFreq']
			self.sacgroup.stkdh.kuser0 = self.opts.filterParameters['band']
			self.sacgroup.stkdh.kuser1 = self.opts.filterParameters['order']

		saveData(self.sacgroup, self.opts)

	def quitButtonClicked(self):
		self.application.closeAllWindows()

	def sortButtonClicked(self):
		# Bug generates warning message
		# https://bugreports.qt.io/browse/QTBUG-37699
		sortDiag = QMessageBox()
		sortDiag.setText('Choose a sort:')
		sortDiag.addButton(QString('Header'), QMessageBox.AcceptRole) # userInput = 0
		sortDiag.addButton(QString('Quality'), QMessageBox.AcceptRole) # userInput = 1
		sortDiag.addButton(QString('File'), QMessageBox.AcceptRole) # userInput = 2
		userInput = sortDiag.exec_()
		
		if userInput == 0:
			print 'Sort by Header'
			sortDiag = QMessageBox()
			sortDiag.setText('Choose a sort:')
			sortDiag.addButton(QString('GCARC'), QMessageBox.AcceptRole) # userInput = 0
			sortDiag.addButton(QString('BAZ'), QMessageBox.AcceptRole) # userInput = 1
			sortDiag.addButton(QString('AZ'), QMessageBox.AcceptRole) # userInput = 2
			sortDiag.addButton(QString('Dist'), QMessageBox.AcceptRole) # userInput = 3
			sortDiag.addButton(QString('STLO'), QMessageBox.AcceptRole) # userInput = 4
			sortDiag.addButton(QString('STLA'), QMessageBox.AcceptRole) # userInput = 5
			sortDiag.addButton(QString('Delta'), QMessageBox.AcceptRole) # userInput = 6
			sortDiag.addButton(QString('E'), QMessageBox.AcceptRole) # userInput = 7
			sortDiag.addButton(QString('B'), QMessageBox.AcceptRole) # userInput = 8
			sortDiag.addButton(QString('NPTS'), QMessageBox.AcceptRole) # userInput = 9
			userInput2 = sortDiag.exec_()

			if userInput2 == 0:
				print 'Sort by GCARC'
				self.opts.sortby = 'gcarc'
			elif userInput2 == 1:
				print 'Sort by BAZ'
				self.opts.sortby = 'baz'
			elif userInput2 == 2:
				print 'Sort by AZ'
				self.opts.sortby = 'az'
			elif userInput2 == 3:
				print 'Sort by Dist'
				self.opts.sortby = 'dist'
			elif userInput2 == 4:
				print 'Sort by STLO'
				self.opts.sortby = 'stlo'
			elif userInput2 == 5:
				print 'Sort by STLA'
				self.opts.sortby = 'stla'
			elif userInput2 == 6:
				print 'Sort by Delta'
				self.opts.sortby = 'delta'
			elif userInput2 == 7:
				print 'Sort by E'
				self.opts.sortby = 'e'
			elif userInput2 == 8:
				print 'Sort by B'
				self.opts.sortby = 'b'
			elif userInput2 == 9:
				print 'Sort by NPTS'
				self.opts.sortby = 'npts'
			else:
				pass
		elif userInput == 1:
			print 'Sort by Quality'
			sortDiag = QMessageBox()
			sortDiag.setText('Choose a sort:')
			sortDiag.addButton(QString('COH'), QMessageBox.AcceptRole) # userInput = 0
			sortDiag.addButton(QString('SNR'), QMessageBox.AcceptRole) # userInput = 1
			sortDiag.addButton(QString('CCC'), QMessageBox.AcceptRole) # userInput = 2
			sortDiag.addButton(QString('All'), QMessageBox.AcceptRole) # userInput = 3
			userInput2 = sortDiag.exec_()
			
			if userInput2 == 0:
				print 'Sort by COH'
				self.opts.sortby = '3'
			elif userInput2 == 1:
				print 'Sort by SNR'
				self.opts.sortby = '2'
			elif userInput2 == 2:
				print 'Sort by CCC'
				self.opts.sortby = '1'
			elif userInput2 == 3:
				print 'Sort by All'
				self.opts.sortby = 'all'
			else:
				pass
		elif userInput == 2:
			print 'Sort by File'
			self.opts.sortby = 'i'
		else:
			print 'Not a valid sort.'

		self.sortSeis()
		self.reorderPlots()

	def sacp2ButtonClicked(self):
		self.sacp2Window = sacp2GUI(self.sacgroup, self.opts)
		self.sacp2Window.start()

	def filterButtonClicked(self):
		self.filterWindow = filterGUI(self.sacgroup, self.stkdh, self.opts)
		self.filterWindow.start()
		self.filterWindow.applyButton.clicked.connect(self.redrawPlots)
		self.filterWindow.unapplyButton.clicked.connect(self.redrawPlots)

	def mapstationsButtonClicked(self):
		stationEntries = ''

		index = 1
		for sacdh in self.sacgroup.saclist:
			stationEntries += '[\'' + str(sacdh.netsta) + '\',' + str(sacdh.stla) + ',' + str(sacdh.stlo) + ',' + str(index) + '],\n'
			index += 1
		stationEntries = stationEntries[:-2]

		__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

		with open(os.path.join(__location__, 'gmapstemplate.html'), 'r') as templateFile:
			htmlMap = templateFile.read()
		htmlMap = htmlMap % (stationEntries)
		with open(os.path.join(os.path.expanduser('~'), 'tmpfile.html'), 'w+') as tmpfile:
			tmpfile.write(htmlMap)

		webbrowser.open('file://' + os.path.join(os.path.expanduser('~'), 'tmpfile.html'), new = 1)

	def addTimePick(self, plot, xVal, pick):
		hdrini, hdrmed, hdrfin = self.opts.qcpara.ichdrs

		if pick == hdrini:
			if hasattr(plot, 't0Line'):
				plot.removeItem(plot.t0Line)
			plot.t0Line = plot.addLine(x = xVal, pen = {'color' : utils.convertToRGB(self.opts.pppara.pickcolors[0]), 'width' : 2})
		elif pick == hdrmed:
			if hasattr(plot, 't1Line'):
				plot.removeItem(plot.t1Line)
			plot.t1Line = plot.addLine(x = xVal, pen = {'color' : utils.convertToRGB(self.opts.pppara.pickcolors[1]), 'width' : 2})
		elif pick == hdrfin:
			if hasattr(plot, 't2Line'):
				plot.removeItem(plot.t2Line)
			plot.t2Line = plot.addLine(x = xVal, pen = {'color' : utils.convertToRGB(self.opts.pppara.pickcolors[2]), 'width' : 2})
		else:
			plot.addLine(x = xVal, pen = {'color' : (255, 255, 255), width : 2})

	def getWindow(self, hdr):
		twh0, twh1 = self.opts.pppara.twhdrs
		tw0 = self.stkdh.gethdr(twh0)
		tw1 = self.stkdh.gethdr(twh1)
		if tw0 == -12345.0:
			tw0 = getWaveDataSetFromSacItem(stkdh, self.opts).x[0]
		if tw1 == -12345.0:
			tw0 = getWaveDataSetFromSacItem(stkdh, self.opts).x[-1]
		# self.calculateRefTime()
		# tw0 -= self.stkdh.reftime
		# tw1 -= self.stkdh.reftime

		t0 = self.stkdh.gethdr(hdr)
		if t0 == -12345.0:
			print ('Header {0:s} not defined'.format(hdr))
			return
		twcorr = [tw0 - t0, tw1 - t0]
		self.opts.ccpara.twcorr = twcorr

	def calculateRefTime(self):
		reltime = self.opts.reltime
		if reltime >= 0:
			reftime = self.stkdh.thdrs[reltime]
			if reftime == -12345.0:
				out = 'Time pick T{0:d} is not defined in SAC file {1:s} of station {2:s}'
				print(out.format(reltime, self.stkdh.filename, self.stkdh.netsta))
				sys.exit()
			else:
				self.stkdh.reftime = reftime
		else:
			self.stkdh.reftime = 0.

	def ccStack(self):
		hdr0, hdr1 = int(self.opts.ccpara.cchdrs[0][1]), int(self.opts.ccpara.cchdrs[1][1])
		stkdh, stkdata, quas = ccWeightStack(self.sacgroup.selist, self.opts)
		stkdh.sethdr(self.opts.qcpara.hdrsel, 'True    ')
		self.stkdh = stkdh
		if self.opts.reltime != hdr1:
			out = '\n--> change opts.reltime from %i to %i'
			print out % (self.opts.reltime, hdr1)
		self.opts.reltime = hdr1

	def getPicks(self):
		hdrini, hdrmed, hdrfin = self.opts.qcpara.ichdrs
		self.tini = self.stkdh.gethdr(hdrini)
		self.tmed = self.stkdh.gethdr(hdrmed)
		self.tfin = self.stkdh.gethdr(hdrfin)

	def syncPick(self):
		self.getPicks()
		tshift = self.tfin - self.tmed
		hdrini, hdrmed, hdrfin = self.opts.qcpara.ichdrs
		for sacdh in self.sacgroup.saclist:
			tfin = sacdh.gethdr(hdrmed) + tshift
			sacdh.sethdr(hdrfin, tfin)

	def syncWindow(self):
		wh0, wh1 = self.opts.qcpara.twhdrs
		hdrini, hdrmed, hdrfin = self.opts.qcpara.ichdrs
		self.getWindow(hdrfin)
		twfin = self.opts.ccpara.twcorr
		for sacdh in self.sacgroup.saclist:
			tfin = sacdh.gethdr(hdrfin)
			# th0 = tfin + twfin[0]
			# th1 = tfin + twfin[1]
			th0 = tfin + self.opts.xlimit[0]
			th1 = tfin + self.opts.xlimit[1]
			sacdh.sethdr(wh0, th0)
			sacdh.sethdr(wh1, th1)

	def sortSeis(self):
		sortincrease = True

		if self.opts.sortby == 'i':
			self.sacgroup.selist, self.sacgroup.delist = seleSeis(self.sacgroup.saclist)
		elif self.opts.sortby == 't':
			ipick = self.opts.qcpara.ichdrs[0]
			wpick = 't' + str(self.opts.reltime)
			if ipick == wpick:
				print ('Same time pick: {0:s} and {1:s}. Exit'.format(ipick, wpick))
				sys.exit()
			self.sacgroup.selist, self.sacgroup.delist = sortSeisHeaderDiff(self.sacgroup.saclist, ipick, wpick, sortincrease)
		elif self.opts.sortby.isdigit() or self.opts.sortby in self.opts.qheaders + ['all',]:
			if self.opts.sortby == '1' or self.opts.sortby == 'ccc':
				self.opts.qweights = [1, 0, 0]
			elif self.opts.sortby == '2' or self.opts.sortby == 'snr':
				self.opts.qweights = [0, 1, 0]
			elif self.opts.sortby == '3' or self.opts.sortby == 'coh':
				self.opts.qweights = [0, 0, 1]
			self.sacgroup.selist, self.sacgroup.delist = sortSeisQual(self.sacgroup.saclist, self.opts.qheaders, self.opts.qweights, self.opts.qfactors, sortincrease)
		else:
			self.sacgroup.selist, self.sacgroup.delist = sortSeisHeader(self.sacgroup.saclist, self.opts.sortby, sortincrease)

	def reorderPlots(self):
		# Basically runs a selection sort on the plots where you compare the plot's sacobj to the sort list of sacobjs

		def swap(itemList, index1, index2):
			tmp = itemList[index1]
			itemList[index1] = itemList[index2]
			itemList[index2] = tmp
			del tmp

		# remove all plots from gfxwidget first
		for plot in self.plotList:
			self.gfxWidget.removeItem(plot)

		# rearange plots to match sacgroup.selist and sacgroup.delist
		for i in xrange(0, len(self.sacgroup.selist)):
			matchingPlotIndex = i
			for j in xrange(i, len(self.plotList)):
				if self.plotList[j].sacdh is self.sacgroup.selist[i]:
					matchingPlotIndex = j
					break
			swap(self.plotList, i, matchingPlotIndex)

		for i in xrange(len(self.sacgroup.selist), len(self.sacgroup.selist) + len(self.sacgroup.delist)):
			matchingPlotIndex = i
			for j in xrange(i, len(self.plotList)):
				if self.plotList[j].sacdh is self.sacgroup.delist[i - len(self.sacgroup.selist)]:
					matchingPlotIndex = j
					break
			swap(self.plotList, i, matchingPlotIndex)

		# put all plots back into gfxwidget
		for plot in self.plotList:
			self.gfxWidget.addItem(plot)
			self.gfxWidget.nextRow()

	def redrawPlots(self, event):
		dataSet = getWaveDataSetFromSacItem(self.stackedPlot.sacdh, self.opts)
		for curve in self.stackedPlot.curves:
			curve.clear()
		self.stackedPlot.plot(dataSet.x, dataSet.y, fillLevel = 0, fillBrush = utils.convertToRGBA(self.opts.pppara.colorwave, 75))
		self.scalePlotYRange(self.stackedPlot)

		for plt in self.plotList:
			dataSet = getWaveDataSetFromSacItem(plt.sacdh, self.opts)
			for curve in plt.curves:
				curve.clear()
			if plt.sacdh.selected:
				plt.plot(dataSet.x, dataSet.y, fillLevel = 0, fillBrush = utils.convertToRGBA(self.opts.pppara.colorwave, 75))
			else:
				plt.plot(dataSet.x, dataSet.y, fillLevel = 0, fillBrush = utils.convertToRGBA(self.opts.pppara.colorwavedel, 75))
			self.scalePlotYRange(plt)



class sacp2GUI(object):
	def __init__(self, sacgroup, opts):
		self.sacgroup = sacgroup
		self.opts = opts

	def start(self):
		sacp2Window = QWidget()
		sacp2Window.setWindowTitle('SAC P2')
		sacp2Window.show()
		sacp2layout = QGridLayout(sacp2Window)

		sacp2gfxWidget = pg.GraphicsLayoutWidget()
		sacp2gfxWidget.resize(1800, 1200)


		plot1 = sacp2gfxWidget.addPlot(title = 'Plot T0')
		sacp2gfxWidget.nextRow()
		plot2 = sacp2gfxWidget.addPlot(title = 'Plot T1')
		sacp2gfxWidget.nextRow()
		plot3 = sacp2gfxWidget.addPlot(title = 'Plot T2')
		sacp2gfxWidget.nextRow()
		plot4 = sacp2gfxWidget.addPlot(title = 'Plot T3')
		sacp2gfxWidget.nextRow()

		hdrini, hdrmed, hdrfin = self.opts.qcpara.ichdrs

		for sacdh in self.sacgroup.selist:
			dataSet = getWaveDataSetFromSacItem(sacdh, self.opts)

			shiftT0 = sacdh.gethdr(hdrini)
			shiftT1 = sacdh.gethdr(hdrmed)
			shiftT2 = sacdh.gethdr(hdrfin)
			shiftT3 = sacdh.gethdr(self.opts.mcpara.wpick)

			shiftedXT0 = [val - shiftT0 for val in dataSet.x]
			shiftedXT1 = [val - shiftT1 for val in dataSet.x]
			shiftedXT2 = [val - shiftT2 for val in dataSet.x]
			shiftedXT3 = [val - shiftT3 for val in dataSet.x]

			pltItem1 = plot1.plot(shiftedXT0, dataSet.y)
			pltItem2 = plot2.plot(shiftedXT1, dataSet.y)
			pltItem3 = plot3.plot(shiftedXT2, dataSet.y)
			pltItem4 = plot4.plot(shiftedXT3, dataSet.y)

			pltItem1.curve.opts['name'] = dataSet.name
			pltItem2.curve.opts['name'] = dataSet.name
			pltItem3.curve.opts['name'] = dataSet.name
			pltItem4.curve.opts['name'] = dataSet.name

		if self.sacgroup.selist[0].gethdr(hdrfin) != -12345.0:
			plot1.setXRange(self.opts.xlimit[0], self.opts.xlimit[1])
			plot2.setXRange(self.opts.xlimit[0], self.opts.xlimit[1])
			plot3.setXRange(self.opts.xlimit[0], self.opts.xlimit[1])
			plot4.setXRange(self.opts.xlimit[0], self.opts.xlimit[1])

		plot1.hideAxis('bottom')
		plot1.hideAxis('left')
		plot2.hideAxis('bottom')
		plot2.hideAxis('left')
		plot3.hideAxis('bottom')
		plot3.hideAxis('left')
		plot4.hideAxis('bottom')
		plot4.hideAxis('left')


		sacp2layout.addWidget(sacp2gfxWidget, 0, 0, 1, 1)
		sacp2Window.resize(1800, 1200)

		# write to class varable so garage collector doesn't delete window
		self.sacp2Window = sacp2Window
		self.sacp2gfxWidget = sacp2gfxWidget

		for curve in plot1.curves + plot2.curves + plot3.curves + plot4.curves:
			curve.curve.setClickable(True)
			curve.curve.sigClicked.connect(self.mouseClickEvents)

		self.sacp2Window.show()

	def mouseClickEvents(self, event):
		print event.name()


class filterGUI(object):
	def __init__(self, sacgroup, stkdh, opts):
		self.sacgroup = sacgroup
		self.opts = opts
		self.stkdh = stkdh

		self.filterWindow = QWidget()
		self.filterWindow.setWindowTitle('Filtering')
		self.filterWindow.show()
		self.filterlayout = QGridLayout(self.filterWindow)

		self.filtergfxWidget = None

		self.applyButton = None
		self.unapplyButton = None

		self.signaltimePlot = None
		self.freqampPlot = None
		self.signaltimeLegend = None
		self.freqampLegend = None

	def start(self):
		self.initGUI()

		self.filtergfxWidget.scene().sigMouseClicked.connect(self.mouseClickEvents)

		self.filterWindow.show()

	def initGUI(self):
		orderButtonWidget = QGroupBox('Order:')
		orderButtonLayout = QVBoxLayout()
		orderButtonWidget.setLayout(orderButtonLayout)

		orderRadioButtons = [QRadioButton('1'), QRadioButton('2'), QRadioButton('3'), QRadioButton('4')]
		orderButtonGroup = QButtonGroup()
		for i in xrange(0, len(orderRadioButtons)):
			orderButtonGroup.addButton(orderRadioButtons[i])
			orderButtonLayout.addWidget(orderRadioButtons[i])
		orderRadioButtons[['1', '2', '3', '4'].index(str(self.opts.filterParameters['order']))].setChecked(True)
		orderButtonGroup.buttonClicked[QAbstractButton].connect(self.orderChanged)

		filterButtonWidget = QGroupBox('Filter Type:')
		filterButtonLayout = QVBoxLayout()
		filterButtonWidget.setLayout(filterButtonLayout)

		filterTypeRadioButtons = [QRadioButton('bandpass'), QRadioButton('lowpass'), QRadioButton('highpass')]
		filterTypeButtonGroup = QButtonGroup()
		for i in xrange(0, len(filterTypeRadioButtons)):
			filterTypeButtonGroup.addButton(filterTypeRadioButtons[i])
			filterButtonLayout.addWidget(filterTypeRadioButtons[i])
		filterTypeRadioButtons[['bandpass', 'lowpass', 'highpass'].index(self.opts.filterParameters['band'])].setChecked(True)
		filterTypeButtonGroup.buttonClicked[QAbstractButton].connect(self.filterTypeChanged)

		runReverseButtonWidget = QGroupBox('Run Reverse:')
		runReverseButtonLayout = QVBoxLayout()
		runReverseButtonWidget.setLayout(runReverseButtonLayout)

		runReverseRadioButtons = [QRadioButton('yes'), QRadioButton('no')]
		runReverseButtonGroup = QButtonGroup()
		for i in xrange(0, len(runReverseRadioButtons)):
			runReverseButtonGroup.addButton(runReverseRadioButtons[i])
			runReverseButtonLayout.addWidget(runReverseRadioButtons[i])
		runReverseRadioButtons[['yes', 'no'].index('yes' if self.opts.filterParameters['reversepass'] else 'no')].setChecked(True)
		runReverseButtonGroup.buttonClicked[QAbstractButton].connect(self.runReverseChanged)

		self.addWidget(orderButtonWidget, 0, 0)
		self.addWidget(filterButtonWidget, 0, 1)
		self.addWidget(runReverseButtonWidget, 0, 2)

		applyWidget = QGroupBox('Apply / Unapply:')
		applyLayout = QVBoxLayout()
		applyWidget.setLayout(applyLayout)

		self.applyButton = QPushButton('Apply')
		self.unapplyButton = QPushButton('Unapply')
		applyLayout.addWidget(self.applyButton)
		applyLayout.addWidget(self.unapplyButton)
		self.applyButton.clicked.connect(self.applyClicked)
		self.unapplyButton.clicked.connect(self.unapplyClicked)

		self.addWidget(applyWidget, 0, 3)

		settingsWidget = QGroupBox('Settings:')
		settingsLayout = QVBoxLayout()
		settingsWidget.setLayout(settingsLayout)

		self.lowFreqLabel = QLabel('Low Freq: ')
		self.highFreqLabel = QLabel('High Freq: ')
		self.orderLabel = QLabel('Order: ')
		settingsLayout.addWidget(self.lowFreqLabel)
		settingsLayout.addWidget(self.highFreqLabel)
		settingsLayout.addWidget(self.orderLabel)

		self.addWidget(settingsWidget, 0, 4)

		self.filtergfxWidget = pg.GraphicsLayoutWidget()
		self.filtergfxWidget.resize(1800, 1200)

		self.signaltimePlot = self.filtergfxWidget.addPlot(title = 'Signal vs. Time')
		self.filtergfxWidget.nextRow()
		self.freqampPlot = self.filtergfxWidget.addPlot(title = 'Frequency vs Amplitude')

		self.addWidget(self.filtergfxWidget, 6, 0, 15, 5)

		self.filterWindow.resize(1800, 1200)

		# Write buttongroups to class variable so they don't get garbage collected and kill the signal
		self.orderButtonGroup = orderButtonGroup
		self.filterTypeButtonGroup = filterTypeButtonGroup
		self.runReverseButtonGroup = runReverseButtonGroup

		self.updateLabels()

		self.signaltimeLegend = self.signaltimePlot.addLegend()
		self.freqampLegend = self.freqampPlot.addLegend()
		self.signaltimeLegend.anchor(itemPos = (1, 0), parentPos = (1, 0), offset = (-30, 30))
		self.freqampLegend.anchor(itemPos = (1, 0), parentPos = (1, 0), offset = (-30, 30))

		self.runFilter()

	def addWidget(self, widget, xLoc, yLoc, xSpan = 1, ySpan = 1):
		self.filterlayout.addWidget(widget, xLoc, yLoc, xSpan, ySpan)

	def mouseClickEvents(self, event):
		plotItemClicked = None
		for item in self.filtergfxWidget.scene().items(event.scenePos()):
			if isinstance(item, pg.graphicsItems.PlotItem.PlotItem):
				plotItemClicked = item

		if plotItemClicked is self.freqampPlot:
			plotVB = plotItemClicked.getViewBox()
			xpoint = plotVB.mapToView(event.pos()).x()

			if self.opts.filterParameters['advance']:
				self.opts.filterParameters['highFreq'] = xpoint
				if self.opts.filterParameters['lowFreq'] < self.opts.filterParameters['highFreq']:
					self.opts.filterParameters['advance'] = False
					self.runFilter()
				else:
					print 'Value chose must be higher than lower frequency of %f' % self.opts.filterParameters['lowFreq']
			else:
				self.opts.filterParameters['lowFreq'] = xpoint
				self.opts.filterParameters['advance'] = True


	def orderChanged(self, event):
		self.opts.filterParameters['order'] = int(event.text())
		self.updateLabels()
		self.runFilter()

	def filterTypeChanged(self, event):
		self.opts.filterParameters['band'] = event.text()
		if event.text() == 'bandpass':
			self.opts.filterParameters['lowFreq'] = 0.05
			self.opts.filterParameters['highFreq'] = 0.25
			self.opts.filterParameters['advance'] = False
		elif event.text() == 'lowpass':
			self.opts.filterParameters['lowFreq'] = 0.05
			self.opts.filterParameters['highFreq'] = nan
			self.opts.filterParameters['advance'] = False
		elif event.text() == 'highpass':
			self.opts.filterParameters['lowFreq'] = nan
			self.opts.filterParameters['highFreq'] = 0.25
			self.opts.filterParameters['advance'] = False
		self.updateLabels()
		self.runFilter()

	def runReverseChanged(self, event):
		if event.text() == 'yes':
			self.opts.filterParameters['reversepass'] = True
		elif event.text() == 'no':
			self.opts.filterParameters['reversepass'] = False
		self.runFilter()

	def applyClicked(self, event):
		self.opts.filterParameters['apply'] = True

	def unapplyClicked(self, event):
		self.opts.filterParameters['apply'] = False

	def updateLabels(self):
		self.lowFreqLabel.setText('Low Freq: ' + str(self.opts.filterParameters['lowFreq']))
		self.highFreqLabel.setText('High Freq: ' + str(self.opts.filterParameters['highFreq']))
		self.orderLabel.setText('Order: ' + str(self.opts.filterParameters['order']))

	def runFilter(self):
		data = getWaveDataSetFromSacItem(self.stkdh, self.opts)
		originalTime = data.x
		originalSignalTime = data.y

		originalFreq, originalSignalFreq = filtering.time_to_freq(originalTime, originalSignalTime, self.opts.delta)
		filteredSignalTime, filteredSignalFreq, adjusted_w, adjusted_h = filtering.filtering_time_freq(originalTime, originalSignalTime, self.opts.delta, self.opts.filterParameters['band'], self.opts.filterParameters['highFreq'], self.opts.filterParameters['lowFreq'], self.opts.filterParameters['order'], self.opts.filterParameters['reversepass'])

		# remove old curve and curve names from plot
		signaltimeCurveNames = [curve.name() for curve in self.signaltimePlot.curves]
		freqampCurveNames = [curve.name() for curve in self.freqampPlot.curves]
		for name in signaltimeCurveNames:
			self.signaltimeLegend.removeItem(name)
		for name in freqampCurveNames:
			self.freqampLegend.removeItem(name)
		self.signaltimePlot.clear()
		self.freqampPlot.clear()

		# self.signaltimePlot.setXRange(-30.0, 30.0)
		self.freqampPlot.setXRange(0, 1.50, padding = 0)

		self.signaltimePlot.plot(originalTime, originalSignalTime, pen = (0, 0, 255), name = 'Original')
		self.signaltimePlot.plot(originalTime, filteredSignalTime, pen = (0, 255, 0), name = 'Filtered')

		self.freqampPlot.plot(originalFreq, np.abs(originalSignalFreq), pen = (0, 0, 255), name = 'Original')
		self.freqampPlot.plot(originalFreq, np.abs(filteredSignalFreq), pen = (0, 255, 0), name = 'Filtered')
		self.freqampPlot.plot(adjusted_w, adjusted_h, pen = (255, 0, 0), name = 'Butterworth Filter')
		