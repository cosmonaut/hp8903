#!/usr/bin/python

from gi.repository import Gtk, GObject

from matplotlib.figure import Figure
from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas
from matplotlib.backends.backend_gtk3 import NavigationToolbar2GTK3 as NavigationToolbar

from datetime import datetime

import serial
import serial.tools.list_ports as list_ports

import math
import numpy as np
import time
from datetime import datetime


UI_INFO = """
<ui>
  <menubar name='MenuBar'>
    <menu action='FileMenu'>
      <menuitem action='FileSave' />
    <separator />
      <menuitem action='FileQuit' />
    </menu>
  </menubar>
</ui>
"""

HP8903_errors = {10: "Reading too large for display.",
                 11: "Calculated value out of range.",
                 13: "Notch cannot tune to input.",
                 14: "Input level exceeds instrument specifications.",
                 17: "Internal voltmeter cannot make measurement.",
                 18: "Source cannot tune as requested.",
                 19: "Cannot confirm source frequency.",
                 20: "Entered value out of range.",
                 21: "Invalid key sequence",
                 22: "Invalid Special Function prefix.",
                 23: "Invalid Special Function suffix.",
                 24: "Invalid HP-IB code.",
                 25: "Top and bottom plotter limits are identical.",
                 26: "RATIO not allowd in present mode.",
                 30: "Input overload detector tripped in range plot.",
                 31: "Cannot make measurement.",
                 32: "More than 255 points total in a sweep.",
                 96: "No signal sensed at input."}
                 

HP8903_filters = ["30 kHz Low Pass",
                  "80 kHz Low Pass",
                  "Left Plug-in Filter",
                  "Right Plug-in Filter"]


class GPIBDevice():
    def __init__(self, gpib_addr = None):
        """Initiazlize GPIB device class"""
        self.dev = None
        self.dev_name = None
        self.ser = None
        # GPIB address of HP 8903
        self.gpib_addr = gpib_addr

    def open(self, dev_name):
        """Open device"""
        # Impossible to open generic device!
        return(False)

    def is_open(self):
        """Test to see if GPIB communication device is open"""
        # Impossible to open generic device!
        return(False)

    def _set_dev_name(self, dev_name):
        device_name = str(dev_name)
        self.dev_name = device_name

    def close(self):
        """Close device"""
        pass

    def write(self, data):
        """Write to GPIB endpoint"""
        pass

    # Blocking with timeout
    def read(self, msg_len = 0, timeout = 500, end_char = '\n'):
        """Read data from GPIB device

        If msg_len is 0, read until end_char with timeout.
        If msg_len > 0 read until msg_len chars are received or until timeout."""
        return('')

    def flush_input(self):
        """Flush device input buffer"""
        pass

    def _command(self, cmd):
        """Write a command to the GPIB communication device"""
        pass

    def test(self):
        """Test GPIB communication device"""
        return(True)

    def status(self):
        """Get GPIB communication device status"""
        pass

    def name(self):
        """Name of GPIB communication device"""
        return("Generic GPIB device""")

    def implements_addr(self):
        """Does this implement GPIB address setting?"""
        return(False)


class NI_GPIB_232CV_A(GPIBDevice):
    def __init__(self, gpib_addr = None):
        # Address on this device only set by dip switches (lame!)

        self.dev_name = None
        self.ser = None
        # Fastest baud this device can do...
        self.baud = 38400
        self.buffer = ''
        self.gpib_addr = gpib_addr

    def open(self, dev_name):
        self._set_dev_name(dev_name)

        print("Connecting to: %s" % self.dev_name)

        self.ser = serial.Serial(self.dev_name,
                                 self.baud,
                                 bytesize = serial.SEVENBITS,
                                 stopbits = serial.STOPBITS_ONE,
                                 parity = serial.PARITY_NONE,
                                 timeout = 0)

        if (self.is_open()):
            self.ser.flushInput()
        else:
            return(False)

        return(True)

    def is_open(self):
        if (self.ser):
            if (self.ser.isOpen()):
                return(True)
            else:
                return(False)

        return(False)

    def close(self):
        if (self.is_open()):
            self.ser.close()

        return(True)

    def write(self, data):
        if (self.is_open()):
            ret = self.ser.write(data)
        else:
            # Error!
            print("%s failed write" % self.name())
            return(0)

        return(ret)

    def read(self, msg_len = 0, timeout = 500, end_char = '\n'):
        if (not self.is_open()):
            return((False, None))

        self.buffer = ''

        start = datetime.now()
        if (msg_len <= 0):
            while(True):
                # read... until newline
                w = self.ser.inWaiting()
                if (w > 0):
                    for i in range(w):
                        c = self.ser.read(1)
                        if (c == end_char):
                            # done!
                            self.buffer += c
                            temp_buf = self.buffer
                            self.buffer = ''
                            return((True, temp_buf))
                        else:
                            self.buffer += c

                delta = datetime.now() - start
                if ((delta.total_seconds()*1000.0) >= timeout):
                    return((False, None))

                # Keep GUI active
                while Gtk.events_pending():
                    Gtk.main_iteration_do(False)

        else:
            r = 0
            while(True):
                w = self.ser.inWaiting()
                if (w > 0):
                    if (w >= msg_len):
                        self.buffer = self.ser.read(msg_len)
                        return((True, self.buffer))
                    else:
                        self.buffer += self.ser.read(w)
                        r += w
                        if (r >= msg_len):
                            # Received complete message
                            temp_buf = self.buffer[0:msg_len]
                            self.buffer = ''
                            return((True, temp_buf))

                delta = datetime.now() - start
                if ((delta.total_seconds()*1000.0) >= timeout):
                    return((False, None))

                # Keep GUI active
                while Gtk.events_pending():
                    Gtk.main_iteration_do(False)

    def flush_input(self):
        if (self.is_open()):
            self.ser.flushInput()

        return(True)

    # Can't implement command...
    def _command(self, cmd):
        return(False)

    def test(self):
        # Not much to do on this device...
        return(self.is_open())

    def status(self):
        if (self.is_open()):
            return((True, "Serial device open"))
        else:
            return((False, "Serial device not open"))

    def name(self):
        return("National Instruments GPIB-232CV-A")


class Galvant_GPIB_USB(GPIBDevice):
    def __init__(self, gpib_addr = 0):
        self.gpib_addr = int(gpib_addr)
        self.dev_name = None
        self.ser = None
        self.baud = 460800

    def open(self, dev_name):
        self._set_dev_name(dev_name)

        print("Connecting to: %s" % self.dev_name)

        self.ser = serial.Serial(self.dev_name,
                                 self.baud,
                                 bytesize = serial.EIGHTBITS,
                                 stopbits = serial.STOPBITS_ONE,
                                 parity = serial.PARITY_NONE)

        if (self.is_open()):
            self.ser.flushInput()

            # Note \n's are added by write()

            self._command("++auto 0")
            time.sleep(0.02)
            # The 8903 can be quite slow...
            self._command("++read_tmo_ms 2500")
            time.sleep(0.02)
            # Set \r\n to be appended to output, read will look for this in data.
            self._command("++eos 0")
            time.sleep(0.02)
            self._command("++ifc")
            time.sleep(0.02)
            # Set HP 8903 address address
            addr_command = "++addr " + str(self.gpib_addr)
            self._command(addr_command)
            time.sleep(0.1)
            # remote addressed mode
            self._command("++llo")
            print(addr_command)
        else:
            return(False)

        return(True)

    def is_open(self):
        if (self.ser):
            if (self.ser.isOpen()):
                return(True)
            else:
                return(False)

        return(False)

    def close(self):
        if (self.is_open()):
            # clearage
            self._command("++ifc")
            # Return instrument to local control
            self._command("++loc")

            self.ser.close()

        return(True)

    def write(self, data):
        # Galvant device requires a \n after any write to controller
        data += "\n"

        if (self.is_open()):
            ret = self.ser.write(data)
        else:
            # Error!
            print("%s failed write" % self.name())
            return(0)

        return(ret)

    def read(self, msg_len = 0, timeout = 500, end_char = '\r'):
        if (not self.is_open()):
            return((False, None))

        self.buffer = ''

        # Command adapter to read until EOS is reached
        self._command("++read\n")

        start = datetime.now()
        if (msg_len <= 0):
            while(True):
                # read... until newline
                w = self.ser.inWaiting()
                if (w > 0):
                    for i in range(w):
                        c = self.ser.read(1)
                        if (c == end_char):
                            # done!
                            self.buffer += c
                            temp_buf = self.buffer
                            self.buffer = ''
                            return((True, temp_buf))
                        else:
                            self.buffer += c

                delta = datetime.now() - start
                if ((delta.total_seconds()*1000.0) >= timeout):
                    return((False, None))

                # Keep GUI active
                while Gtk.events_pending():
                    Gtk.main_iteration_do(False)

        else:
            r = 0
            while(True):
                w = self.ser.inWaiting()
                if (w > 0):
                    if (w >= msg_len):
                        self.buffer = self.ser.read(msg_len)
                        return((True, self.buffer))
                    else:
                        self.buffer += self.ser.read(w)
                        r += w
                        if (r >= msg_len):
                            # Received complete message
                            temp_buf = self.buffer[0:msg_len]
                            self.buffer = ''
                            return((True, temp_buf))

                delta = datetime.now() - start
                if ((delta.total_seconds()*1000.0) >= timeout):
                    return((False, None))

                # Keep GUI active
                while Gtk.events_pending():
                    Gtk.main_iteration_do(False)

    def _command(self, cmd):
        ret = self.write(cmd)
        return(ret)

    def test(self):
        r = self._command("++ver")
        if (r != 6):
            return(False)

        # if first 7 chars are "Version" pass!
        status, msg = self.read(timeout = 1000, end_char = '\r')
        print("%s Version: %s" % (self.name(), msg))
        if (status):
            if (len(msg) >= 7):
                if (msg[0:7] == "Version"):
                    return(True)

        return(False)

    def status(self):
        # Not implemented here for now...
        return(True)

    def name(self):
        return("Galvant GPIB USB Adapter")

    def implements_addr(self):
        return(True)


# Add thisto HP8903BWindow
HP8903_GPIB_devices = [(Galvant_GPIB_USB, "Galvant GPIB USB Adapter"),
                       (NI_GPIB_232CV_A, "National Instruments GPIB-232CV-A")]


class HP8903BWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="HP 8903B Control")

        # Serial connection!
        self.ser = None
        self.gpib_dev = None
        self.devices = list_ports.comports()
        
        # Menu Bar junk!
        action_group = Gtk.ActionGroup("my_actions")
        action_filemenu = Gtk.Action("FileMenu", "File", None, None)
        action_group.add_action(action_filemenu)
        self.action_filesave = Gtk.Action("FileSave", "Save Data", None, None)
        
        action_filequit = Gtk.Action("FileQuit", None, None, Gtk.STOCK_QUIT)
        action_filequit.connect("activate", self.on_menu_file_quit)
        action_group.add_action(self.action_filesave)
        action_group.add_action(action_filequit)
        self.action_filesave.set_sensitive(False)
        self.action_filesave.connect('activate', self.save_data)

        
        uimanager = self.create_ui_manager()
        uimanager.insert_action_group(action_group)

        menubar = uimanager.get_widget("/MenuBar")

        self.status_bar = Gtk.Statusbar()
        self.status_bar.push(0, "HP 8903 Audio Analyzer Control")
        
        self.master_vbox = Gtk.Box(False, spacing = 2, orientation = 'vertical')
        self.master_vbox.pack_start(menubar, False, False, 0)
        master_hsep = Gtk.HSeparator()
        self.master_vbox.pack_start(master_hsep, False, False, 0)
        self.add(self.master_vbox)

        self.hbox = Gtk.Box(spacing = 2)
        self.master_vbox.pack_start(self.hbox, True, True, 0)

        self.master_vbox.pack_start(self.status_bar, False, False, 0)

        # Begin controls
        bframe = Gtk.Frame(label = "Control")
        left_vbox = Gtk.Box(spacing = 2, orientation = 'vertical')
        self.box = Gtk.Box(spacing = 2)

        bframe.add(left_vbox)

        # GPIB device selector
        gpib_frame = Gtk.Frame(label = "GPIB Communication Device")
        self.gpib_big_box = Gtk.Box(spacing = 2)
        gpib_frame.add(self.gpib_big_box)
        self.gpib_box = Gtk.Box(spacing = 2)
        self.gpib_vbox = Gtk.Box(spacing = 2, orientation = 'vertical')
        gpib_label = Gtk.Label("GPIB Device: ")
        self.gpib_box.pack_start(gpib_label, False, False, 0)

        gpib_store = Gtk.ListStore(int, str)
        for n, g_dev in enumerate(HP8903_GPIB_devices):
            gpib_store.append([n, g_dev[1]])
        self.gpib_combo = Gtk.ComboBox.new_with_model_and_entry(gpib_store)
        self.gpib_combo.set_entry_text_column(1)
        self.gpib_combo.set_active(0)

        self.gpib_box.pack_start(self.gpib_combo, False, False, 0)

        gpib_addr_box = Gtk.Box(spacing = 2)

        self.gpib_addr = Gtk.SpinButton()
        self.gpib_addr.set_range(0, 30)
        self.gpib_addr.set_digits(0)
        self.gpib_addr.set_value(0)
        self.gpib_addr.set_increments(1.0, 1.0)


        gpib_addr_label = Gtk.Label("GPIB Address: ")
        gpib_addr_box.pack_start(gpib_addr_label, False, False, 0)
        gpib_addr_box.pack_start(self.gpib_addr, False, False, 0)

        self.gpib_vbox.pack_start(self.gpib_box, False, False, 0)
        self.gpib_vbox.pack_start(gpib_addr_box, False, False, 0)

        self.gpib_big_box.pack_start(self.gpib_vbox, False, False, 0)

        left_vbox.pack_start(gpib_frame, False, False, 0)

        # Device items
        left_vbox.pack_start(self.box, False, False, 0)

        self.hbox.pack_start(bframe, False, False, 0)

        con_hbox = Gtk.Box(spacing = 2)
        self.con_button = Gtk.Button(label = "Connect")
        self.dcon_button = Gtk.Button(label = "Disconnect")

        self.con_button.connect("clicked", self.setup_gpib)
        self.dcon_button.connect("clicked", self.close_gpib)
        
        con_hbox.pack_start(self.con_button, False, False, 0)
        con_hbox.pack_start(self.dcon_button, False, False, 0)

        left_vbox.pack_start(con_hbox, False, False, 0)
        
        device_store = Gtk.ListStore(int, str)

        for i, dev in enumerate(self.devices):
            device_store.append([i, dev[0]])
        self.device_combo = Gtk.ComboBox.new_with_model_and_entry(device_store)
        self.device_combo.set_entry_text_column(1)
        self.device_combo.set_active(0)

        device_label = Gtk.Label("Device: ")
        
        self.box.pack_start(device_label, False, False, 0)
        self.box.pack_start(self.device_combo, False, False, 0)

        hsep0 = Gtk.HSeparator()
        left_vbox.pack_start(hsep0, False, False, 2)

        # Measurement Selection
        mframe = Gtk.Frame(label = "Measurement Selection")
        meas_box = Gtk.Box(spacing = 2)
        meas_vbox = Gtk.Box(spacing = 2)

        mframe.add(meas_box)
        meas_box.pack_start(meas_vbox, False, False, 0)

        meas_store = Gtk.ListStore(int, str)
        meas_dict = {0: "THD+n",
                     1:"Frequency Response",
                     2: "THD+n (Ratio)",
                     3: "Frequency Response (Ratio)",
                     4: "Ouput Level"}
        for k, v in meas_dict.iteritems():
            meas_store.append([k, v])
        self.meas_combo = Gtk.ComboBox.new_with_model_and_entry(meas_store)
        self.meas_combo.set_entry_text_column(1)
        self.meas_combo.set_active(0)

        self.meas_combo.connect("changed", self.meas_changed)
        
        meas_vbox.pack_start(self.meas_combo, False, False, 0)
        left_vbox.pack_start(mframe, False, False, 0)


        units_frame = Gtk.Frame(label = "Units")
        units_box = Gtk.Box(spacing = 2)
        units_vbox = Gtk.Box(spacing = 2)

        units_frame.add(units_box)
        units_box.pack_start(units_vbox, False, False, 0)

        self.thd_units_store = Gtk.ListStore(int, str)
        self.ampl_units_store = Gtk.ListStore(int, str)
        self.thdr_units_store = Gtk.ListStore(int, str)
        self.amplr_units_store = Gtk.ListStore(int, str)
        self.optlvl_units_store = Gtk.ListStore(int, str)
        thd_units_dict = {0: "%", 1: "dB"}
        ampl_units_dict = {0: "V", 1: "dBm"}
        thdr_units_dict = {0: "%", 1: "dB"}
        amplr_units_dict = {0: "%", 1:"dB"}
        optlvl_units_dict = {0: "V"}

        for k, v in thd_units_dict.iteritems():
            self.thd_units_store.append([k, v])
        for k, v in ampl_units_dict.iteritems():
            self.ampl_units_store.append([k, v])
        for k, v in thdr_units_dict.iteritems():
            self.thdr_units_store.append([k, v])
        for k, v in amplr_units_dict.iteritems():
            self.amplr_units_store.append([k, v])
        for k, v in optlvl_units_dict.iteritems():
            self.optlvl_units_store.append([k, v])

            
        self.units_combo = Gtk.ComboBox.new_with_model_and_entry(self.thd_units_store)
        self.units_combo.set_entry_text_column(1)
        self.units_combo.set_active(0)

        self.units_combo.connect("changed", self.units_changed)
        
        units_vbox.pack_start(self.units_combo, False, False, 0)
        left_vbox.pack_start(units_frame, False, False, 0)
        
        # units_combo.set_model(ampl_units_store)
        # units_combo.set_active(0)
        #left_vbox.pack_start(units_combo, False, False, 0)
        
        
        
        hsep1 = Gtk.HSeparator()
        left_vbox.pack_start(hsep1, False, False, 2)

        # Frequency Sweep Control
        #side_filler = Gtk.Box(spacing = 2, orientation = 'vertical')
        swconf = Gtk.Frame(label = "Frequency Sweep Control")
        swhbox = Gtk.Box(spacing = 2)
        swbox = Gtk.Box(spacing = 2, orientation = 'vertical')
        swconf.add(swhbox)
        swhbox.pack_start(swbox, False, False, 0)
        
        left_vbox.pack_start(swconf, False, False, 0)
        
        startf = Gtk.Frame(label = "Start Frequency (Hz)")
        
        self.start_freq = Gtk.SpinButton()
        self.start_freq.set_range(20.0, 100000.0)
        self.start_freq.set_digits(5)
        self.start_freq.set_value(20.0)
        self.start_freq.set_increments(100.0, 1000.0)

        startf.add(self.start_freq)
        #left_vbox.pack_start(startf, False, False, 0)
        swbox.pack_start(startf, False, False, 0)
        self.start_freq.connect("value_changed", self.freq_callback)
        
        stopf = Gtk.Frame(label = "Stop Frequency (Hz)")
        
        self.stop_freq = Gtk.SpinButton()
        self.stop_freq.set_range(20.0, 100000.0)
        self.stop_freq.set_digits(5)
        self.stop_freq.set_value(30000.0)
        self.stop_freq.set_increments(100.0, 1000.0)

        stopf.add(self.stop_freq)
        #left_vbox.pack_start(stopf, False, False, 0)
        swbox.pack_start(stopf, False, False, 0)
        self.stop_freq.connect("value_changed", self.freq_callback)

        stepsf = Gtk.Frame(label = "Steps per Decade")
        
        self.steps = Gtk.SpinButton()
        self.steps.set_range(1.0, 1000.0)
        self.steps.set_digits(1)
        self.steps.set_value(10.0)
        self.steps.set_increments(1.0, 10.0)

        stepsf.add(self.steps)
        swbox.pack_start(stepsf, False, False, 0)
        #left_vbox.pack_start(stepsf, False, False, 0)

        hsep2 = Gtk.HSeparator()
        left_vbox.pack_start(hsep2, False, False, 2)

        # Freq Control

        freqf = Gtk.Frame(label = "Frequency")
        freqbox = Gtk.Box(spacing = 2)
        freqhbox = Gtk.Box(spacing = 2, orientation = 'vertical')

        freqf.add(freqhbox)
        freqhbox.pack_start(freqbox, False, False, 0)

        self.freq = Gtk.SpinButton()
        self.freq.set_range(20.0, 100000.0)
        self.freq.set_digits(5)
        self.freq.set_value(1000.0)
        self.freq.set_increments(100.0, 1000.0)

        self.freq.set_sensitive(False)
        
        freqbox.pack_start(self.freq, False, False, 0)
        left_vbox.pack_start(freqf, False, False, 0)

        freqhsep = Gtk.HSeparator()
        left_vbox.pack_start(freqhsep, False, False, 2)
        
        # Source Control
        sourcef = Gtk.Frame(label = "Source Control (V RMS)")
        source_box = Gtk.Box(spacing = 2)
        sourcef.add(source_box)
        
        self.source = Gtk.SpinButton()
        self.source.set_range(0.0006, 6.0)
        self.source.set_digits(4)
        self.source.set_value(0.5)
        self.source.set_increments(0.5, 1.0)
        source_box.pack_start(self.source, False, False, 0)
        left_vbox.pack_start(sourcef, False, False, 0)

        hsep3 = Gtk.HSeparator()
        left_vbox.pack_start(hsep3, False, False, 2)


        vswconf = Gtk.Frame(label = "Voltage Sweep Control")
        vswhbox = Gtk.Box(spacing = 2)
        vswbox = Gtk.Box(spacing = 2, orientation = 'vertical')
        vswconf.add(vswhbox)
        vswhbox.pack_start(vswbox, False, False, 0)
        
        left_vbox.pack_start(vswconf, False, False, 0)
        
        startv = Gtk.Frame(label = "Start Voltage (V)")
        
        self.start_v = Gtk.SpinButton()
        self.start_v.set_range(0.0006, 6.0)
        self.start_v.set_digits(5)
        self.start_v.set_value(0.1)
        self.start_v.set_increments(0.1, 1)

        startv.add(self.start_v)
        #left_vbox.pack_start(startf, False, False, 0)
        vswbox.pack_start(startv, False, False, 0)
        self.start_v.connect("value_changed", self.volt_callback)
        
        stopv = Gtk.Frame(label = "Stop Voltage (V)")
        
        self.stop_v = Gtk.SpinButton()
        self.stop_v.set_range(0.0006, 6.0)
        self.stop_v.set_digits(5)
        self.stop_v.set_value(1.0)
        self.stop_v.set_increments(0.1, 1.0)

        stopv.add(self.stop_v)
        #left_vbox.pack_start(stopf, False, False, 0)
        vswbox.pack_start(stopv, False, False, 0)
        self.stop_v.connect("value_changed", self.volt_callback)

        stepsv = Gtk.Frame(label = "Total Samples")
        
        self.stepsv = Gtk.SpinButton()
        self.stepsv.set_range(1.0, 1000.0)
        self.stepsv.set_digits(1)
        self.stepsv.set_value(10.0)
        self.stepsv.set_increments(1.0, 10.0)

        stepsv.add(self.stepsv)
        vswbox.pack_start(stepsv, False, False, 0)
        #left_vbox.pack_start(stepsf, False, False, 0)

        hsepsv = Gtk.HSeparator()
        left_vbox.pack_start(hsepsv, False, False, 2)



        
        filterf = Gtk.Frame(label = "Filters")
        filterb = Gtk.Box(spacing = 2)
        filtervb = Gtk.Box(spacing = 2, orientation = 'vertical')
        filterf.add(filterb)
        filterb.pack_start(filtervb, False, False, 0)

        self.f30k = Gtk.CheckButton("30 kHz LP")
        self.f80k = Gtk.CheckButton("80 kHz LP")

        self.lpi = Gtk.CheckButton("Left Plug-in filter")
        self.rpi = Gtk.CheckButton("Right Plug-in filter")

        self.f30k.connect("toggled", self.filter1_callback)
        self.f80k.connect("toggled", self.filter1_callback)

        self.lpi.connect("toggled", self.filter2_callback)
        self.rpi.connect("toggled", self.filter2_callback)
        
        filtervb.pack_start(self.f30k, False, False, 0)
        filtervb.pack_start(self.f80k, False, False, 0)
        filtervb.pack_start(self.lpi, False, False, 0)
        filtervb.pack_start(self.rpi, False, False, 0)

        left_vbox.pack_start(filterf, False, False, 0)
        
        hsep = Gtk.HSeparator()
        left_vbox.pack_start(hsep, False, False, 2)
        
        self.run_button = Gtk.Button(label = "Start Sequence")
        self.run_button.set_sensitive(False)
        left_vbox.pack_start(self.run_button, False, False, 0)
        self.run_button.connect("clicked", self.run_test)
        
        
        self.f = Figure(figsize=(5,4), dpi=100)
        self.a = self.f.add_subplot(111)
        #self.plt = self.a.plot(20,-90, marker = 'x')
        self.plt = self.a.plot(marker = 'x')
        self.a.grid(True)
        self.a.set_xscale('log')
        self.a.set_xlim((10.0, 30000.0))
        self.a.set_ylim((0.0005, 0.01))
        self.a.set_xlabel("Frequency (Hz)")
        self.a.set_ylabel("THD+n (%)")
        
        self.canvas = FigureCanvas(self.f)

        toolbar = NavigationToolbar(self.canvas, self)

        plot_vbox = Gtk.Box(spacing = 2, orientation = 'vertical')
        plot_vbox.pack_start(self.canvas, True, True, 0)
        plot_vbox.pack_start(toolbar, False, False, 0)
        
        #self.hbox.pack_start(self.canvas, True, True, 0)
        self.hbox.pack_start(plot_vbox, True, True, 0)

        # Groups of widgets
        self.measurement_widgets = [self.meas_combo, self.units_combo]
        self.freq_sweep_widgets = [self.start_freq, self.stop_freq, self.steps]
        self.source_widgets = [self.source]
        self.filter_widgets = [self.f30k, self.f80k, self.lpi, self.rpi]
        self.vsweep_widgets = [self.start_v, self.stop_v, self.stepsv]
        
        for w in self.measurement_widgets:
            w.set_sensitive(False)
        for w in self.freq_sweep_widgets:
            w.set_sensitive(False)
        for w in self.source_widgets:
            w.set_sensitive(False)
        for w in self.filter_widgets:
            w.set_sensitive(False)
        for w in self.vsweep_widgets:
            w.set_sensitive(False)

        
        self.meas_string = "THD+n (%)"
        self.units_string = "%"
        self.measurements = None

    def setup_gpib(self, button):
        # Get GPIB info
        gpib_model = self.gpib_combo.get_model()
        gpib_tree_iter = self.gpib_combo.get_active_iter()

        # Get address
        gpib_addr = self.gpib_addr.get_value_as_int()

        # Instantiate GPIB Device class
        self.gpib_dev = HP8903_GPIB_devices[gpib_model[gpib_tree_iter][0]][0](gpib_addr = gpib_addr)
        print("Using GPIB Device: %s" % self.gpib_dev.name())
        print("Using GPIB Address: %s" % str(gpib_addr))

        if (not self.gpib_dev.implements_addr()):
            print("Warning: this GPIB communication device does not implement")
            print("    address setting, check your hardware's settings!")

        # Get device info
        model = self.device_combo.get_model()

        tree_iter = self.device_combo.get_active_iter()

        print("Device: %s" % model[tree_iter][1])
        dev_name = model[tree_iter][1]

        # Disable gpib and devices buttons
        self.con_button.set_sensitive(False)
        self.device_combo.set_sensitive(False)
        self.gpib_combo.set_sensitive(False)
        self.gpib_addr.set_sensitive(False)


        if(not self.gpib_dev.open(dev_name)):
            # Make into warning window?
            print("Failed to open GPIB Device: %s at %s" % (self.gpib_dev.name(), dev_name))
            print("Verify hardware setup and try to connect again")

            self.con_button.set_sensitive(True)
            self.device_combo.set_sensitive(True)
            self.gpib_combo.set_sensitive(True)
            self.gpib_addr.set_sensitive(True)

            return(False)

        # Do test?
        if (not self.gpib_dev.test()):
            print("GPIB device failed self test: %s at %s" % (self.gpib_dev.name(), dev_name))
            print("Verify hardware setup and try to connect again")

            self.con_button.set_sensitive(True)
            self.device_combo.set_sensitive(True)
            self.gpib_combo.set_sensitive(True)
            self.gpib_addr.set_sensitive(True)

            return(False)


        if (self.gpib_dev.is_open()):
            self.gpib_dev.flush_input()
            # Initialize the HP 8903
            status = self.init_hp8903()
            if (not status):
                print("Failed to initialize HP 8903")
                print("Verify hardware setup and try to connect again")

                self.gpib_dev.close()

                self.con_button.set_sensitive(True)
                self.device_combo.set_sensitive(True)
                self.gpib_combo.set_sensitive(True)
                self.gpib_addr.set_sensitive(True)

                return(False)

        else:
            print("Failed to use GPIB device")
            print("Verify hardware setup and try to connect again")

            self.gpib_dev.close()

            self.con_button.set_sensitive(True)
            self.device_combo.set_sensitive(True)
            self.gpib_combo.set_sensitive(True)
            self.gpib_addr.set_sensitive(True)

            return(False)

        # Enable measurement controls
        self.run_button.set_sensitive(True)
        for w in self.measurement_widgets:
            w.set_sensitive(True)
        for w in self.freq_sweep_widgets:
            w.set_sensitive(True)
        for w in self.source_widgets:
            w.set_sensitive(True)
        for w in self.filter_widgets:
            w.set_sensitive(True)
        for w in self.vsweep_widgets:
            w.set_sensitive(False)


        self.status_bar.push(0, "Connected to  HP 8903, ready for measurements")

    def close_gpib(self, button):
        if (self.gpib_dev):
            self.gpib_dev.close()

        # Activate device/connection buttons
        self.con_button.set_sensitive(True)
        self.device_combo.set_sensitive(True)
        self.gpib_combo.set_sensitive(True)
        self.gpib_addr.set_sensitive(True)

        # Disable measurement controls
        for w in self.measurement_widgets:
            w.set_sensitive(False)
        for w in self.freq_sweep_widgets:
            w.set_sensitive(False)
        for w in self.source_widgets:
            w.set_sensitive(False)
        for w in self.filter_widgets:
            w.set_sensitive(False)
        for w in self.vsweep_widgets:
            w.set_sensitive(False)

        self.freq.set_sensitive(False)

        self.run_button.set_sensitive(False)

    def run_test(self, button):
        # Disable all control widgets during sweep
        self.run_button.set_sensitive(False)
        self.action_filesave.set_sensitive(False)

        for w in self.measurement_widgets:
            w.set_sensitive(False)
        for w in self.freq_sweep_widgets:
            w.set_sensitive(False)
        for w in self.source_widgets:
            w.set_sensitive(False)
        for w in self.filter_widgets:
            w.set_sensitive(False)
        for w in self.vsweep_widgets:
            w.set_sensitive(False)

        self.freq.set_sensitive(False)

        
        self.x = []
        self.y = []
        
        # 30, 80, LPI, RPI
        filters = [False, False, False, False]
        filters[0] = self.f30k.get_active()
        filters[1] = self.f80k.get_active()
        filters[2] = self.lpi.get_active()
        filters[3] = self.rpi.get_active()
        #print(filters)

        amp = self.source.get_value()
        
        strtf = self.start_freq.get_value()
        stopf = self.stop_freq.get_value()
        
        num_steps = self.steps.get_value_as_int()
        step_size = 10**(1.0/num_steps)

        strt_dec = math.floor(math.log10(strtf))
        stop_dec = math.floor(math.log10(stopf))

        meas = self.meas_combo.get_active()
        units = self.units_combo.get_active()

        lsteps = []
        vsteps = []
        if ((meas < 4) and (meas >= 0)):
            decs = math.log10(stopf/strtf)
            npoints = int(decs*num_steps)

            for n in range(npoints + 1):
                lsteps.append(strtf*10.0**(float(n)/float(num_steps)))
                
            self.a.set_xlim((lsteps[0]*10**(-2.0/10.0), lsteps[-1]*10**(2.0/10.0)))
            self.a.set_xscale('log')
        elif (meas == 4):
            start_amp = self.start_v.get_value()
            stop_amp = self.stop_v.get_value()
            num_vsteps = self.stepsv.get_value()
            vsteps = np.linspace(start_amp, stop_amp, num_vsteps)
            amp_buf = ((stop_amp - start_amp)*0.1)/2.0
            print(amp_buf)
            self.a.set_xlim(((start_amp - amp_buf), (stop_amp + amp_buf)))
            self.a.set_xscale('linear')
            # print(start_amp)
            # print(stop_amp)
            # print(num_vsteps)


        center_freq = self.freq.get_value()
            
        # center freq...
        self.measurements = [amp, filters, meas, units, self.meas_string, self.units_string]
        
        if ((meas == 0) or (meas == 1)):
            #pass
            pt = self.send_measurement(meas, units, center_freq, amp, filters, ratio = 2)
        elif ((meas == 2) or (meas == 3)):
            pt = self.send_measurement(meas, units, center_freq, amp, filters)
            #print(pt)
            pt = self.send_measurement(meas, units, center_freq, amp, filters, ratio = 1)
            #print("PT: %s" % pt)
        elif (meas == 4):
            pt = self.send_measurement(meas, units, center_freq, start_amp, filters, ratio = 2)

        if ((meas < 4) and (meas >= 0)):
            for i in lsteps:
                meas_point = self.send_measurement(meas, units, i, amp, filters)
                self.x.append(float(i))
                self.y.append(float(meas_point))
                print(float(meas_point))
                self.update_plot(self.x, self.y)
                # plot new measures
                #print(meas_point)
        elif (meas == 4):
            #pass
            for v in vsteps:
                meas_point = self.send_measurement(meas, units, center_freq, v, filters)
                self.x.append(v)
                self.y.append(float(meas_point))
                print("in: %f, out %f" % (v, float(meas_point)))
                self.update_plot(self.x, self.y)
        

        for w in self.measurement_widgets:
            w.set_sensitive(True)
        for w in self.filter_widgets:
            w.set_sensitive(True)

        if ((meas < 4) and (meas >= 0)):
            for w in self.freq_sweep_widgets:
                w.set_sensitive(True)
            for w in self.source_widgets:
                w.set_sensitive(True)
        if (meas == 4):
            for w in self.vsweep_widgets:
                w.set_sensitive(True)

        if (meas > 1):
            self.freq.set_sensitive(True)

        self.run_button.set_sensitive(True)
        self.action_filesave.set_sensitive(True)

    def update_plot(self, x, y):
        if (len(self.plt) < 1):
            self.plt = self.a.plot(x, y, marker = 'x')
        self.plt[0].set_data(x, y)
        ymin = min(y)
        ymax = max(y)

        
        # if (ymin == 0.0):
        #     ymin = -0.01
        # if (ymax == 0.0):
        #     ymax = 0.01

        sep = abs(ymax - ymin)
        sep = sep/10.0

        if (sep == 0.0):
            sep = 0.01

        #self.a.set_ylim((ymin - abs(ymin*0.10), ymax + abs(ymax*0.10)))
        self.a.set_ylim((ymin - abs(sep), ymax + abs(sep)))
        self.canvas.draw()
            
    def init_hp8903(self):
        self.gpib_dev.flush_input()
        # Arbitrary but simple measurement to check device
        self.gpib_dev.write("FR1000.0HZAP0.100E+00VLM1LNL0LNT3")
        status, meas = self.gpib_dev.read(msg_len = 12, timeout = 5000)

        if (status):
            print(meas)
        else:
            print("Failed to initialize HP8903!")
            print(status, meas)
            return(False)

        return(True)
        
    def send_measurement(self, meas, unit, freq, amp, filters, ratio = 0):
        # Store parameters for saving after any measure
        #self.measurements = [amp, filters, meas, unit]
        measurement = ""
        meas_unit = ""
        
        if (filters[0]):
            fs1 = "L1"
        elif (filters[1]):
            fs1 = "L2"
        else:
            fs1 = "L0"

        if (filters[2]):
            fs2 = "H1"
        elif (filters[3]):
            fs2 = "H2"
        else:
            fs2 = "H0"

        if ((meas == 0) or (meas == 2)):
            measurement = "M3"
        elif ((meas == 1) or (meas == 3) or (meas == 4)):
            measurement = "M1"

        if (unit == 0):
            meas_unit = "LN"
        elif (unit == 1):
            meas_unit = "LG"
            
        source_freq = ("FR%.4EHZ" % freq)
        source_ampl = ("AP%.4EVL" % amp)
        filter_s = fs1 + fs2

        rat = ""
        if (ratio == 1):
            rat = "R1"
        elif (ratio == 2):
            rat = "R0"
        
        #payload = source_freq + source_ampl + "M3LN" + filter_s + "LNT3"
        payload = source_freq + source_ampl + measurement + filter_s + meas_unit + rat + "T3"
        #print(payload)
        #print("FR%.4EHZAP1VLM1LNL0LNT3" % freq)
        #print("FR%.4EHZAP%.4EVLM3LNL0LNT3" % (freq, amp))
        #self.ser.write(("FR%.4EHZAP%.4EVLM3LNL2LNT3" % (freq, amp)))

        # Send and read measurement via GPIB controller
        self.gpib_dev.write(payload)
        status, samp = self.gpib_dev.read(timeout = 2500)
        if (status):
            sampf = float(samp)
        else:
            sampf = np.NAN
            print("Failed to get sample")

        if (sampf > 4.0e9):
            print(("Error: %s" % samp[4:6]) + " " + HP8903_errors[int(samp[4:6])])
            samp = np.NAN

        self.status_bar.push(0, "Freq: %f, Amp: %f, Return: %f,    GPIB: %s" % (freq, amp, sampf, payload))
            
        return(samp)

    def save_data(self, button):
        fname = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        fid = open(fname + '.txt', 'w')

        # Write source voltage info
        source_v = str(self.measurements[0])
        fid.write("# Measurement: " + self.measurements[4] + "\n")
        fid.write("# Source Voltage: " + source_v + " V RMS\n")
        # write filter info
        for n, f in enumerate(self.measurements[1]):
            if f:
                fid.write("# " + HP8903_filters[n] + " active\n")

        fid.write("# Frequency (Hz)    " + self.measurements[5] + "\n")
        n = np.array([np.array(self.x), np.array(self.y)])
        np.savetxt(fid, n.transpose(), fmt = ["%f", "%f"])
        fid.close()
        
        
    def freq_callback(self, spinb):
        if (self.start_freq.get_value() > self.stop_freq.get_value()):
            self.start_freq.set_value(self.stop_freq.get_value())

    def volt_callback(self, spinb):
        if (self.start_v.get_value() > self.stop_v.get_value()):
            self.start_v.set_value(self.stop_v.get_value())

    # 30k/80k toggle
    def filter1_callback(self, cb):
        if (cb.get_active()):
            if (cb.get_label() == "30 kHz LP"):
                self.f80k.set_active(False)
            elif (cb.get_label() == "80 kHz LP"):
                self.f30k.set_active(False)

    # left plugin/right plugin toggle
    def filter2_callback(self, cb):
        if (cb.get_active()):
            if (cb.get_label() == "Left Plug-in filter"):
                self.rpi.set_active(False)
            elif (cb.get_label() == "Right Plug-in filter"):
                self.lpi.set_active(False)

    def on_menu_file_quit(self, widget):
        if (self.gpib_dev):
            self.gpib_dev.close()
        Gtk.main_quit()

    def meas_changed(self, widget):
        meas_ind = self.meas_combo.get_active()
        if (meas_ind == 0):
            self.units_combo.set_model(self.thd_units_store)
            self.units_combo.set_active(0)
            self.a.set_ylabel("THD+n (%)")
            self.a.set_xlabel("Frequency (Hz)")            
            self.canvas.draw()
            self.freq.set_sensitive(False)
            self.source.set_sensitive(True)
            for w in self.freq_sweep_widgets:
                w.set_sensitive(True)
            for w in self.vsweep_widgets:
                w.set_sensitive(False)
        elif (meas_ind == 1):
            self.units_combo.set_model(self.ampl_units_store)
            self.units_combo.set_active(0)
            self.a.set_ylabel("AC Level (V RMS)")
            self.a.set_xlabel("Frequency (Hz)")            
            self.canvas.draw()
            self.freq.set_sensitive(False)
            self.source.set_sensitive(True)
            for w in self.freq_sweep_widgets:
                w.set_sensitive(True)
            for w in self.vsweep_widgets:
                w.set_sensitive(False)
        elif (meas_ind == 2):
            self.units_combo.set_model(self.thdr_units_store)
            self.units_combo.set_active(0)
            self.a.set_ylabel("THD+n Ratio (%)")
            self.a.set_xlabel("Frequency (Hz)")
            self.canvas.draw()
            self.freq.set_sensitive(True)
            self.source.set_sensitive(True)
            for w in self.freq_sweep_widgets:
                w.set_sensitive(True)
            for w in self.vsweep_widgets:
                w.set_sensitive(False)
        elif (meas_ind == 3):
            self.units_combo.set_model(self.amplr_units_store)
            self.units_combo.set_active(0)
            self.a.set_ylabel("AC Level Ratio (%)")
            self.a.set_xlabel("Frequency (Hz)")
            self.canvas.draw()
            self.freq.set_sensitive(True)
            self.source.set_sensitive(True)
            for w in self.freq_sweep_widgets:
                w.set_sensitive(True)
            for w in self.vsweep_widgets:
                w.set_sensitive(False)
        elif (meas_ind == 4):
            self.units_combo.set_model(self.optlvl_units_store)
            self.units_combo.set_active(0)
            self.a.set_ylabel("Output Level (V)")
            self.a.set_xlabel("Input Level (V)")
            self.canvas.draw()
            self.freq.set_sensitive(True)
            self.source.set_sensitive(False)
            for w in self.freq_sweep_widgets:
                w.set_sensitive(False)
            for w in self.vsweep_widgets:
                w.set_sensitive(True)


            


    def units_changed(self, widget):
        meas_ind = self.meas_combo.get_active()
        units_ind = self.units_combo.get_active()
        #print("meas ind: %d units ind: %d" % (meas_ind, units_ind))
        # Set units on plot
        meas = ""
        if (meas_ind == 0):
            meas = "THD+n "
            if (units_ind == 0):
                meas += "(%)"
                self.units_string = "%"
            elif (units_ind == 1):
                meas += "(dB)"
                self.units_string = "dB"
        elif (meas_ind == 1):
            meas = "AC Level "
            if (units_ind == 0):
                meas += "(V RMS)"
                self.units_string = "V RMS"
            elif (units_ind == 1):
                meas += "(dB V)"
                self.units_string = "dB V"
        elif (meas_ind == 2):
            meas = "THD+n (Ratio) "
            if (units_ind == 0):
                meas += "(%)"
                self.units_string = "%"
            elif (units_ind == 1):
                meas += "(dB)"
                self.units_string = "dB"
        elif (meas_ind == 3):
            meas = "AC Level (Ratio) "
            if (units_ind == 0):
                meas += "(%)"
                self.units_string = "%"
            elif (units_ind == 1):
                meas += "(dB)"
                self.units_string = "dB"

        # Save text info about units
        self.meas_string = meas
        # Updated plot
        self.a.set_ylabel(meas)
        self.canvas.draw()

    # menu bar junk
    def create_ui_manager(self):
        uimanager = Gtk.UIManager()

        # Throws exception if something went wrong
        uimanager.add_ui_from_string(UI_INFO)

        # Add the accelerator group to the toplevel window
        accelgroup = uimanager.get_accel_group()
        self.add_accel_group(accelgroup)
        return uimanager

if __name__ == '__main__':
    win = HP8903BWindow()
    win.connect("delete-event", Gtk.main_quit)
    win.show_all()
    Gtk.main()
