#!/usr/bin/python

import sys
import serial
import time

# Test settings for the NI GPIB-232CV-A controller with the HP 8903

# Note: for use with python 2.X

# Hardware setup:
# Turn off HP 8903 and NI Controller
# Connect GPIB cable from GPIB-232CV-A to HP 8903
# Turn on HP 8903
# Connect serial line to GPIB-232CV-A and turn on its power switch
# After a short period of time the "Remote" and "Addressed" lights should be on
# Then, run this program (e.g. python2 nigpib232cva.py /dev/ttyUSB0)
# If it works you should get one measurement from the 8903 (e.g. +00252E-07)

def main(dev_name):
        
    s = serial.Serial(dev_name,
                      38400,
                      bytesize = serial.SEVENBITS,
                      stopbits = serial.STOPBITS_ONE,
                      parity = serial.PARITY_NONE)

    s.flushInput()

    time.sleep(0.2)
    
    # Run a test!
    s.write("FR1000.0HZAP0.100E+00VLM1LNL0LNT3")
    time.sleep(0.01)

    buf = ''
    # Read data
    for i in range(2000):
        n = s.inWaiting()
        if (n > 0):
            msg = s.read(n)
            #print(msg.rstrip('\r\n'))
            buf += msg.rstrip('\r\n')
            
        time.sleep(0.002)

    print(buf)

        
    s.close()

if __name__ == '__main__':
    if (len(sys.argv) > 1):
        main(sys.argv[1])
    else:
        print("Usage: python galvant.py <usb_device_name>")

