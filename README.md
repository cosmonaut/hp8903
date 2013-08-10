hp8903
======

Acquisition and plotting software for the HP 8903 Audio Analyzer.

This program is currently designed to interface with a serial device
directly. It is expected that GPIB is handled after this. It is
currently tested and used with a National Instruments
GPIB-232CV-A. Support could be added to interface with other GPIB
communication devices. Ideally I'd like to add support for both the
Prologix GPIB-USB and GPIB-Ethernet devices. Support could be added
for any other GPIB devices that can easily be interfaced with in
python.

This software is currently only tested with Linux but should work on
Windows and Mac OS X as well.

Dependencies
=====

* python (>= 2.7)
* matplotlib
* numpy
* pyserial
* gobject (for GTK3)

Features
=====

* THD+n vs frequency
* Amplitude vs frequency

Future features should include THD+n vs Power and THD+n vs
voltage. Ratio-type relative measurements are also planned.


