#!/usr/bin/env python
from pysmo.aimbat_qt.GUI import mainGUI
from pysmo.aimbat_qt.seismodata import getDataSet

import pyqtgraph as pg

sacgroup, opts = getDataSet()

gui = mainGUI(sacgroup, opts)
gui.setupGUI()

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if sys.flags.interactive != 1 or not hasattr(QtCore, 'PYQT_VERSION'):
        pg.QtGui.QApplication.exec_()