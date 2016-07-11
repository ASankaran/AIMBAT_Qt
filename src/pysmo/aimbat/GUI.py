from PyQt4.QtGui import *
from PyQt4.QtCore import *

import pyqtgraph as pg

import sys

from seismodata import getWaveDataSetFromSacItem
from algiccs import ccWeightStack
from algmccc import eventListName, mccc
from sacpickle import taperWindow, saveData
from qualsort import seleSeis, sortSeisQual, sortSeisHeader, sortSeisHeaderDiff


class mainGUI(object):
	def __init__(self, sacgroup, opts):
		self.application = QApplication(sys.argv)
		self.window = QWidget()
		self.window.setWindowTitle('Seismic Plots')
		self.window.show()
		self.layout = QGridLayout(self.window)

		self.sacgroup = sacgroup
		self.opts = opts

		self.stkdh = None
		self.stackedPlot = None
		self.originalStackedPlotRanges = {'x' : [0, 0], 'y' : [0, 0]}

		self.selectedWindow = [0, 0]
		self.t2pick = 0

		self.plotList = []

		self.selectedIndexes = []

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

		self.stackedPlot.enableAutoRange('x', True)
		self.originalStackedPlotRanges['x'] = self.stackedPlot.viewRange()[0]
		self.originalStackedPlotRanges['y'] = self.stackedPlot.viewRange()[1]
		self.stackedPlot.enableAutoRange('x', True)

		# print self.originalStackedPlotRanges

		# hdrini, hdrmed, hdrfin = self.opts.qcpara.ichdrs
		# self.addTimePick(self.stackedPlot, self.stkdh.gethdr(hdrini), 't0') # fix to pass hdrini var
		# self.addTimePick(self.stackedPlot, self.stkdh.gethdr(hdrmed), 't1') # fix to pass hdrini var
		# for plt in self.plotList:
		# 	self.addTimePick(plt, plt.sacdh.gethdr(hdrini), 't0') # fix to pass hdrini var
		# 	self.addTimePick(plt, plt.sacdh.gethdr(hdrmed), 't1') # fix to pass hdrini var

		stackedVB = self.stackedPlot.getViewBox()
		stackedVB.setMouseMode(stackedVB.RectMode)
		stackedVB.sigXRangeChanged.connect(self.setWindow)

	def setWindow(self, arg):
		timewindow = arg.state['viewRange'][0]
		self.stackedPlot.setYRange(*self.originalStackedPlotRanges['y'])
		self.selectedWindow = timewindow
		# confirmDiag = QMessageBox()
		# confirmDiag.setText("Set selected area as window?")
		# confirmDiag.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
		# confirmDiag.setDefaultButton(QMessageBox.Save)
		# userInput = confirmDiag.exec_()

		# if userInput == QMessageBox.Save:
		# 	print 'Set Timewindow:', timewindow
		# elif userInput == QMessageBox.Cancel:
		# 	pass

		twh0, twh1 = self.opts.pppara.twhdrs
		self.stkdh.sethdr(twh0, timewindow[0])
		self.stkdh.sethdr(twh1, timewindow[1])

		# print 'Set Timewindow:', timewindow

	def getPlotGraphicsLayoutWindow(self, xSize, ySize):
		gfxWidget = pg.GraphicsLayoutWidget()
		gfxWidget.resize(xSize, ySize)

		# Create stacked plot
		hdrini, hdrmed, hdrfin = self.opts.qcpara.ichdrs
		self.opts.ccpara.cchdrs = [hdrini, hdrmed]
		stkdh, stkdata, quas = ccWeightStack(self.sacgroup.saclist, self.opts)
		self.stkdh = stkdh
		dataSet = getWaveDataSetFromSacItem(stkdh)
		plt = gfxWidget.addPlot(title = dataSet.name)
		plt.plot(dataSet.x, dataSet.y, fillLevel = 0, fillBrush = (255, 0, 0, 75))
		plt.curves[0].selected = True
		plt.hideAxis('bottom')
		plt.hideAxis('left')
		plt.sacdh = stkdh
		plt.sacdh.selected = True

		self.stackedPlot = plt

		gfxWidget.nextRow()

		# Create plots for other seismograms
		index = 0
		for sacitem in self.sacgroup.saclist:
			dataSet = getWaveDataSetFromSacItem(sacitem)
			plt = gfxWidget.addPlot(title = dataSet.name)
			plt.plot(dataSet.x, dataSet.y, fillLevel = 0, fillBrush = (255, 0, 0, 75))
			plt.curves[0].selected = True
			plt.index = index
			self.selectedIndexes.append(index)
			plt.hideAxis('bottom')
			plt.hideAxis('left')
			plt.sacdh = sacitem
			plt.sacdh.selected = True
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

		self.addWidget(alignbtn, 0, 0)
		self.addWidget(syncbtn, 0, 1)
		self.addWidget(refinebtn, 0, 2)
		self.addWidget(finalizebtn, 0, 3)
		self.addWidget(savebtn, 0, 4)
		self.addWidget(quitbtn, 0, 5)
		self.addWidget(sacp2btn, 0, 6)
		self.addWidget(sortbtn, 0, 7)
		self.addWidget(filterbtn, 0, 8)
		self.addWidget(mapstationsbtn, 0, 9)

	def mouseClickEvents(self, event):
		plotItemClicked = None
		for item in self.gfxWidget.scene().items(event.scenePos()):
			if isinstance(item, pg.graphicsItems.PlotItem.PlotItem):
				plotItemClicked = item

		#If double click add t2 time
		hdrini, hdrmed, hdrfin = self.opts.qcpara.ichdrs
		if event.double():
			plotVB = plotItemClicked.getViewBox()
			xpoint = plotVB.mapToView(event.pos()).x()
			self.addTimePick(plotItemClicked, xpoint, hdrfin)
			self.t2pick = xpoint

			hdrini, hdrmed, hdrfin = self.opts.qcpara.ichdrs
			self.stkdh.sethdr(hdrfin, self.t2pick)
			return

		#If single click select / deselect a plot
		if plotItemClicked is self.stackedPlot:
			return

		if plotItemClicked.curves[0].selected:
			plotItemClicked.curves[0].setFillBrush((0, 255, 0, 75))
			plotItemClicked.curves[0].selected = False
			self.selectedIndexes.remove(plotItemClicked.index)
			plotItemClicked.sacdh.selected = False
			self.sacgroup.selist.remove(plotItemClicked.sacdh)
			self.sacgroup.delist.append(plotItemClicked.sacdh)
		else:
			plotItemClicked.curves[0].setFillBrush((255, 0, 0, 75))
			plotItemClicked.curves[0].selected = True
			self.selectedIndexes.append(plotItemClicked.index)
			plotItemClicked.sacdh.selected = True
			self.sacgroup.delist.remove(plotItemClicked.sacdh)
			self.sacgroup.selist.append(plotItemClicked.sacdh)
		#plotItemClicked.curves[0].setFillBrush((0, 255, 0, 75))
		#self.gfxWidget.removeItem(plotItemClicked)

	def alignButtonClicked(self):
		hdrini, hdrmed, hdrfin = self.opts.qcpara.ichdrs
		self.opts.ccpara.cchdrs = hdrini, hdrmed

		self.getWindow(self.opts.ccpara.cchdrs[0])
		self.ccStack()
		self.getPicks()

		# Recreate stacked plot
		self.stackedPlot.clearPlots()
		dataSet = getWaveDataSetFromSacItem(self.stkdh)
		self.stackedPlot.plot(dataSet.x, dataSet.y, fillLevel = 0, fillBrush = (255, 0, 0, 75))
		self.stackedPlot.curves[0].selected = True
		self.stackedPlot.hideAxis('bottom')
		self.stackedPlot.hideAxis('left')

		hdrini, hdrmed, hdrfin = self.opts.qcpara.ichdrs
		self.addTimePick(self.stackedPlot, self.stkdh.gethdr(hdrini), hdrini) # fix to pass hdrini var
		self.addTimePick(self.stackedPlot, self.stkdh.gethdr(hdrmed), hdrmed) # fix to pass hdrini var
		for plt in self.plotList:
			self.addTimePick(plt, plt.sacdh.gethdr(hdrini), hdrini) # fix to pass hdrini var
			self.addTimePick(plt, plt.sacdh.gethdr(hdrmed), hdrmed) # fix to pass hdrini var

	def syncButtonClicked(self):
		hdrini, hdrmed, hdrfin = self.opts.qcpara.ichdrs
		wh0, wh1 = self.opts.qcpara.twhdrs
		if self.stkdh.gethdr(hdrfin) == -12345.:
			print '*** hfinal %s is not defined. Pick at array stack first! ***' % hdrfin
			return

		self.syncPick()
		self.syncWindow()

		twfin = self.opts.ccpara.twcorr
		for plt in self.plotList:
			sacdh = plt.sacdh
			tfin = sacdh.gethdr(hdrfin)
			ipk = int(hdrfin[1])
			# tpk = tfin - sacdh.reftime
			tpk = tfin
			# pp.timepicks[ipk].set_xdata(tpk)
			self.addTimePick(plt, tpk, hdrfin)
			th0 = tfin + twfin[0]
			th1 = tfin + twfin[1]
			# pp.twindow = [th0, th1]
			plt.setXRange(th0, th1)
			# pp.resetWindow()
		print '--> Sync final time picks and time window... You can now run CCFF to refine final picks.'

		# hdrini, hdrmed, hdrfin = self.opts.qcpara.ichdrs
		# self.addTimePick(self.stackedPlot, self.stkdh.gethdr(hdrini), 't0') # fix to pass hdrini var
		# self.addTimePick(self.stackedPlot, self.stkdh.gethdr(hdrmed), 't1') # fix to pass hdrini var
		# for plt in self.plotList:
		# 	self.addTimePick(plt, plt.sacdh.gethdr(hdrini), 't0') # fix to pass hdrini var
		# 	self.addTimePick(plt, plt.sacdh.gethdr(hdrmed), 't1') # fix to pass hdrini var

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
		# self.replot()
		# print self.tini, self.tmed, self.tfin

	def finalizeButtonClicked(self):
		print 'Finalize Clicked'
		self.getWindow(self.opts.mcpara.ipick)
		tw = self.opts.ccpara.twcorr[1] - self.opts.ccpara.twcorr[0]
		taperwindow = taperWindow(self.opts.ccpara.twcorr, self.opts.mcpara.taperwidth)
		self.opts.mcpara.timewindow = self.opts.ccpara.twcorr
		self.opts.mcpara.taperwindow = taperwindow
		evline, mcname = eventListName(self.sacgroup.event, self.opts.mcpara.phase)
		self.opts.mcpara.evline = evline
		self.opts.mcpara.mcname = mcname
		self.opts.mcpara.kevnm = self.sacgroup.kevnm

		# Move a bunch of data to the location that the mccc function expects it
		selectedList = []
		deselectedList = []
		for x in xrange(0, len(self.sacgroup.saclist)):
			if x in self.selectedIndexes:
				selectedList.append(self.sacgroup.saclist[x])
			else:
				deselectedList.append(self.sacgroup.saclist[x])
		self.sacgroup.selist = selectedList
		self.sacgroup.delist = deselectedList
		self.sacgroup.stkdh = self.stkdh

		solution, solist_LonLat, delay_times = mccc(self.sacgroup, self.opts.mcpara)
		self.sacgroup.solist_LonLat = solist_LonLat
		self.sacgroup.delay_times = delay_times

		wpk = int(self.opts.mcpara.wpick[1])
		if self.opts.reltime != wpk:
			out = '\n--> change opts.reltime from %i to %i'
			print out % (self.opts.reltime, wpk)
		self.opts.reltime = wpk
		# self.replot()

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
		# print 'SAC P2 Clicked'
		# sacp2Window = QWidget()
		# sacp2Window.setWindowTitle('SAC P2')
		# sacp2Window.show()
		# sacp2layout = QGridLayout(sacp2Window)

		# sacp2gfxWidget = pg.GraphicsLayoutWidget()
		# sacp2gfxWidget.resize(1800, 1200)


		# plot1 = sacp2gfxWidget.addPlot(title = 'Plot T0')
		# sacp2gfxWidget.nextRow()
		# plot2 = sacp2gfxWidget.addPlot(title = 'Plot T1')
		# sacp2gfxWidget.nextRow()
		# plot3 = sacp2gfxWidget.addPlot(title = 'Plot T2')
		# sacp2gfxWidget.nextRow()
		# plot4 = sacp2gfxWidget.addPlot(title = 'Plot T3')
		# sacp2gfxWidget.nextRow()

		# for sacdh in self.sacgroup.selist:
		# 	dataSet = getWaveDataSetFromSacItem(sacdh)

		# 	hdrini, hdrmed, hdrfin = self.opts.qcpara.ichdrs

		# 	shiftT0 = sacdh.gethdr(hdrini)
		# 	shiftT1 = sacdh.gethdr(hdrmed)
		# 	shiftT2 = sacdh.gethdr(hdrfin)
		# 	shiftT3 = sacdh.gethdr(self.opts.mcpara.wpick)

		# 	shiftedXT0 = [val - shiftT0 for val in dataSet.x]
		# 	shiftedXT1 = [val - shiftT1 for val in dataSet.x]
		# 	shiftedXT2 = [val - shiftT2 for val in dataSet.x]
		# 	shiftedXT3 = [val - shiftT3 for val in dataSet.x]

		# 	plot1.plot(shiftedXT0, dataSet.y)
		# 	plot2.plot(shiftedXT1, dataSet.y)
		# 	plot3.plot(shiftedXT2, dataSet.y)
		# 	plot4.plot(shiftedXT3, dataSet.y)

		# plot1.hideAxis('bottom')
		# plot1.hideAxis('left')
		# plot2.hideAxis('bottom')
		# plot2.hideAxis('left')
		# plot3.hideAxis('bottom')
		# plot3.hideAxis('left')
		# plot4.hideAxis('bottom')
		# plot4.hideAxis('left')


		# sacp2layout.addWidget(sacp2gfxWidget, 0, 0, 1, 1)
		# sacp2Window.resize(1800, 1200)

		# # write to class varable so garage collector doesn't delete window
		# self.sacp2Window = sacp2Window

		# self.sacp2Window.show()

		self.sacp2Window = sacp2GUI(self.sacgroup, self.opts)
		self.sacp2Window.start()

	def addTimePick(self, plot, xVal, pick):
		hdrini, hdrmed, hdrfin = self.opts.qcpara.ichdrs

		if pick == hdrini:
			plot.addLine(x = xVal, pen = (255, 255, 0))
		elif pick == hdrmed:
			plot.addLine(x = xVal, pen = (0, 0, 255))
		elif pick == hdrfin:
			plot.addLine(x = xVal, pen = (255, 140, 0))
		else:
			plot.addLine(x = xVal, pen = (255, 255, 255))
		# plot.addLine(x = xVal)

	def getWindow(self, hdr):
		twh0, twh1 = self.opts.pppara.twhdrs
		tw0 = self.stkdh.gethdr(twh0)
		tw1 = self.stkdh.gethdr(twh1)
		if tw0 == -12345.0:
			tw0 = getWaveDataSetFromSacItem(stkdh).x[0]
		if tw1 == -12345.0:
			tw0 = getWaveDataSetFromSacItem(stkdh).x[-1]
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

		print self.stkdh.reftime

	def ccStack(self):
		hdr0, hdr1 = int(self.opts.ccpara.cchdrs[0][1]), int(self.opts.ccpara.cchdrs[1][1])
		selectedList = []
		for index in self.selectedIndexes:
			selectedList.append(self.sacgroup.saclist[index])
		stkdh, stkdata, quas = ccWeightStack(selectedList, self.opts)
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
			th0 = tfin + twfin[0]
			th1 = tfin + twfin[1]
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

		# print 'Selected Seismograms'
		# for sacdh in self.sacgroup.selist:
		# 	data = getWaveDataSetFromSacItem(sacdh)
		# 	print data.name
		# print 'Deselected Seismograms'
		# for sacdh in self.sacgroup.delist:
		# 	data = getWaveDataSetFromSacItem(sacdh)
		# 	print data.name

	def reorderPlots(self):

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

		# self.printQuals()

	# def printQuals(self):
	# 	for plot in self.plotList:
	# 		hdrcc, hdrsn, hdrco = self.opts.qheaders[:3]
	# 		cc = plot.sacdh.gethdr(hdrcc)
	# 		sn = plot.sacdh.gethdr(hdrsn)
	# 		co = plot.sacdh.gethdr(hdrco)
	# 		print 'qual={0:4.2f}/{1:.1f}/{2:4.2f}'.format(cc, sn, co)


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

		for sacdh in self.sacgroup.selist:
			dataSet = getWaveDataSetFromSacItem(sacdh)

			hdrini, hdrmed, hdrfin = self.opts.qcpara.ichdrs

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

			pltItem1.curve.opts['name'] = getWaveDataSetFromSacItem(sacdh).name
			pltItem2.curve.opts['name'] = getWaveDataSetFromSacItem(sacdh).name
			pltItem3.curve.opts['name'] = getWaveDataSetFromSacItem(sacdh).name
			pltItem4.curve.opts['name'] = getWaveDataSetFromSacItem(sacdh).name

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
		