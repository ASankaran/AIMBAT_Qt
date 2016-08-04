AIMBAT_Qt 
=========
 
Copyright
---------
[GNU General Public License](http://www.gnu.org/licenses/gpl.html), Version 3 (GPLv3) 

Copyright (c) 2016 Arnav Sankaran

Copyright (c) 2009-2012 Xiaoting Lou


Overview
--------
AIMBAT (Automated and Interactive Measurement of Body-wave Arrival Times) is an open-source software package for efficiently measuring teleseismic body wave arrival times for large seismic arrays [Lou et al., 2013](http://www.earth.northwestern.edu/~xlou/aimbat_files/Lou_etal_2013_SRL_AIMBAT.pdf). It is 
based on a widely used method called MCCC (multi-channel cross-correlation) developed by [VanDecar and Crosson (1990)](http://bssa.geoscienceworld.org/content/80/1/150.abstract). The package is automated in the sense of initially aligning seismograms for MCCC which is achieved by an ICCS (iterative cross-correlation and stack) algorithm. Meanwhile, a graphical user interface is built to perform seismogram quality control interactively. Therefore, user processing time is reduced while valuable input from a user's expertise is retained. As a byproduct, SAC [Goldstein et al., 2003](http://oasis.crs.inogs.it/static/doc/GoldsteinEtAl_2003_iaspei_sac.pdf) plotting and phase picking functionalities are replicated and enhanced.

For more informaton visit the [project website](http://www.earth.northwestern.edu/~xlou/aimbat.html) or the [Pysmo repository](https://github.com/pysmo).

Documentation
-------------
Read about the features and their usage in the latest version of AIMBAT-Qt on github [here](https://github.com/ASankaran/AIMBAT_Qt/wiki).

Additionally you will find valuable information in the documentation written for the original version of AIMBAT [here](http://aimbat.readthedocs.org/en/latest/index.html).

Dependencies
------------
* [Python](http://www.python.org/)
* [Numpy](http://www.numpy.org/)
* [Scipy](http://www.scipy.org/)
* [pysmo.sac](https://github.com/pysmo/sac)
* [pyqtgraph](http://www.pyqtgraph.org/)
* [GFortran](https://gcc.gnu.org/wiki/GFortranBinaries)
* [GMT](http://gmt.soest.hawaii.edu/) (Optional: Only needed for plotting stations)

Building
--------

Each time you make changes to any of the files in this repository, run

	sudo python setup.py build --fcompiler=gfortran
	sudo python setup.py install
	
To build again and allow the changes to take place.
