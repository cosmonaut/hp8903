hp8903
======

Acquisition and plotting software for the HP 8903 Audio Analyzer.

This program is designed to interface with a serial device
directly. It is expected that GPIB is handled after this. It is
currently tested and used with a National Instruments GPIB-232CV-A but
it should also work with the nicer (and cheaper!) Prologix GPIB-USB
converter.

Currently only linux is tested and supported. Other operating systems
should be able to user this software soon.

Dependencies
=====

* matplotlib
* numpy
* pyserial
* gobject (for GTK3)
