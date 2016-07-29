#!/usr/bin/env python
#------------------------------------------------
# Filename: ttpick.py
#   Author: Arnav Sankaran
#    Email: arnavsankaran@gmail.com
#
# Copyright (c) 2016 Arnav Sankaran
#------------------------------------------------
from pysmo.aimbat_qt.GUI import mainGUI
from pysmo.aimbat_qt.seismodata import getDataOpts

import pyqtgraph as pg

sacgroup, opts = getDataOpts()

gui = mainGUI(sacgroup, opts)
gui.setupGUI()

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if sys.flags.interactive != 1 or not hasattr(QtCore, 'PYQT_VERSION'):
        pg.QtGui.QApplication.exec_()