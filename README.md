hp8903
======

Acquisition and plotting software for the HP 8903 Audio Analyzer.

This software operates the HP 8903 and automates much of the work
needed to do a variety of sweep measurements.

This software currently has limited GPIB controller hardware
support. Support could be added to interface with other GPIB
communication devices. Any GPIB controller that already easily
interfaces with python would be simple to support.

This software is currently only tested with Linux but should work on
Windows and Mac OS X as well.

This software was motivated by Pete Millett's HP 8903 software
(http://www.pmillett.com/hp_8903_software.htm) which only supports
Windows. 

Dependencies
=====

* python (>= 2.7)
* matplotlib
* numpy
* pyserial
* gobject (for GTK3)

Supported GPIB Hardware
=====

* Galvant GPIB USB converter (http://galvant.ca/shop/gpibusb/)
* National Instruments GPIB-232-CV-A

I would like to add support for the Prologix devices (perhaps someone
wants to donate one?). Supporting VISA devices is also a goal.

Some short quick hardware test programs are included in the folder
"hardware_tests."

Usage
=====

1. Turn off HP 8903 and GPIB controller.
2. Connect GPIB cable to controller and HP 8903.
3. Turn on HP 8903.
4. Turn on GPIB controller and/or connect to computer.
5. Open hp8903 software.
6. Select GPIB controller and GPIB address (if applicable). Note that
you must set this via dip switch with the GPIB-232CV-A.
7. Select the comport/device of the controller on the computer
(e.g. /dev/ttyUSB0).
8. Click "Connect."

If successful the status bar should show that the unit is initialized
and ready for measurements. Now a measurement can be selected, sweep
parameters can be set, and hitting the start button will run a sweep.

Features
=====

* THD+n vs frequency
* Amplitude vs frequency
* Ratio-type sweeps
* Save plots and raw data
* Control of filters

Future features may include: 

* THD+n vs Power and THD+n vs voltage.
* pyvisa support (Installing VISA in linux is a pain! slow progress..)


