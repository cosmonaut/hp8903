#!/usr/bin/python

import sys
import serial
import time

# Test settings for the Galvant GPIB USB controller with the HP 8903

# Note: for use with python 2.X

# Hardware setup:
# Turn off HP 8903 and Galvant Adapter
# Connect GPIB cable from galvant to HP 8903
# Turn on HP 8903
# Plug in Galvant USB cable (turning on the device)
# The 8903 should do it's typical turn-on click and screen cycle
# Then, run this program (e.g. python2 galvant.py /dev/ttyUSB0 28)
# If it works you should get one measurement from the 8903 (e.g. +00262E-07)

# The "addressed" light on the HP 8903 will go off until more commands
# are sent with this device. However, all functions should still work.

def main(dev_name, gpib_addr):

    gpib_addr = int(gpib_addr)
    if ((gpib_addr < 0) or (gpib_addr > 30)):
        print("GPIB address must be between 0 and 30")
        print("Got address: %s" % str(gpib_addr))
    
    s = serial.Serial(dev_name,
                      460800,
                      bytesize = serial.EIGHTBITS,
                      stopbits = serial.STOPBITS_ONE,
                      parity = serial.PARITY_NONE)

    s.flushInput()

    # Turn off auto mode
    s.write("++auto 0\n")

    # Check version...
    s.write("++ver\n")
    n = s.inWaiting()
    msg = s.read(n)
    print("Galvant GPIB USB: %s" % msg)

    # Turn debug on for hardware test
    s.write("++debug 1\n")
    time.sleep(0.02)
    # Set long timeout (8903 has trigger with settle measurements)
    s.write("++read_tmo_ms 2000\n")
    time.sleep(0.02)
    
    # Set \r\n as outgoing and incoming terminator
    s.write("++eos 0\n")
    time.sleep(0.02)
    
    # Set GPIB address
    ga = str(gpib_addr)
    s.write("++addr " + ga + "\n")
    time.sleep(0.2)
    # Remote mode
    s.write("++llo\n")
    time.sleep(0.02)

    # Run a test!
    s.write("FR1000.0HZAP0.100E+00VLM1LNL0LNT3\n")
    time.sleep(0.01)
    
    # Read data
    s.write("++read\n")

    
    for i in range(2000):
        n = s.inWaiting()
        if (n > 0):
            msg = s.read(n)
            print(msg)
            
        time.sleep(0.002)


        
    s.close()

if __name__ == '__main__':
    if (len(sys.argv) > 2):
        main(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python galvant.py <usb_device_name> <gpib_address>")
