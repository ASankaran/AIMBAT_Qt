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
	x = linspace(b, b + npts * delta, npts)
	y = array(sacitem.data)

	if hasattr(opts, 'filterParameters') and opts.filterParameters['apply']:
		originalTime = x
		originalSignalTime = y
		filteredSignalTime, filteredSignalFreq, adjusted_w, adjusted_h = filtering.filtering_time_freq(originalTime, originalSignalTime, opts.delta, opts.filterParameters['band'], opts.filterParameters['highFreq'], opts.filterParameters['lowFreq'], opts.filterParameters['order'], opts.filterParameters['reversepass'])
		return DataItem(x, filteredSignalTime, sacitem.filename)

	return DataItem(x, y, sacitem.filename)