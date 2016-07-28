#!/usr/bin/env python
#------------------------------------------------
# Filename: seismodata.py
#   Author: Arnav Sankaran
#    Email: arnavsankaran@gmail.com
#
# Copyright (c) 2016 Arnav Sankaran
#------------------------------------------------
from sacpickle import readPickle
from pysmo.sac.sacio import sacfile
from numpy import linspace, array
from scipy import signal

from qualctrl import getDataOpts

from algiccs import ccWeightStack
import filtering


class DataItem(object):
	def __init__(self, xPts, yPts, name):
		self.x = xPts
		self.y = yPts
		self.name = name


def getDataSet():
	# data = []

	# read sac file for aimbat waves:
	sacgroup, opts = getDataOpts()
	return sacgroup, opts

	# hdrini, hdrmed, hdrfin = opts.qcpara.ichdrs
	# opts.ccpara.cchdrs = [hdrini, hdrmed]
	# stkdh, stkdata, quas = ccWeightStack(sacgroup.saclist, opts)

	# sacgroup.saclist.insert(0, stkdh)


	# for sacitem in sacgroup.saclist:
	# 	b = sacitem.b
	# 	npts = sacitem.npts
	# 	delta = sacitem.delta
	# 	x = linspace(b, b + npts * delta, npts)
	# 	y = array(sacitem.data)
	# 	data.append(DataItem(x, y, sacitem.filename))

	# return data

def getWaveDataSetFromSacItem(sacitem, opts):
	b = sacitem.b
	npts = sacitem.npts
	delta = sacitem.delta
	x = linspace(b, b + (npts - 1) * delta, npts)
	y = array(sacitem.data)

	if hasattr(opts, 'filterParameters') and opts.filterParameters['apply']:
		originalTime = x
		originalSignalTime = y
		filteredSignalTime, filteredSignalFreq, adjusted_w, adjusted_h = filtering.filtering_time_freq(originalTime, originalSignalTime, opts.delta, opts.filterParameters['band'], opts.filterParameters['highFreq'], opts.filterParameters['lowFreq'], opts.filterParameters['order'], opts.filterParameters['reversepass'])
		return DataItem(x, filteredSignalTime, sacitem.netsta)

	twh0, twh1 = opts.pppara.twhdrs
	tw0 = sacitem.gethdr(twh0)
	tw1 = sacitem.gethdr(twh1)
	twindow = [tw0, tw1]

	if opts.ynorm > 0:
		if opts.ynormtwin_on:
			try:
				indmin, indmax = numpy.searchsorted(x, twindow)
				indmax = min(len(x) - 1, indmax)
				thisd = y[indmin : indmax + 1]
				dnorm = dataNorm(thisd)
			except:
				dnorm = dataNorm(y)
		else:
			dnorm = dataNorm(y)
		dnorm = 1 / dnorm * opts.ynorm * .5
	else:
		dnorm = 1
	y = y * dnorm

	return DataItem(x, y, sacitem.netsta)

def dataNorm(d, w=0.05):
	dmin, dmax = d.min(), d.max()
	dnorm = max(-dmin, dmax) * (1+w)
	return dnorm