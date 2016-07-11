from aimbat.GUI import mainGUI
from aimbat.seismodata import DataItem, getDataSet

import sys

import pyqtgraph as pg

if len(sys.argv) == 1:
	sys.argv.append('/Users/geophysics/Documents/20110915.19310408.bhz.pkl')
sacgroup, opts = getDataSet()


gui = mainGUI(sacgroup, opts)
gui.setupGUI()

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if sys.flags.interactive != 1 or not hasattr(QtCore, 'PYQT_VERSION'):
        pg.QtGui.QApplication.exec_()