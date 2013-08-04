#!/usr/bin/python

from gi.repository import Gtk, GObject

from matplotlib.figure import Figure
from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas

import serial
import serial.tools.list_ports_posix

import math
import numpy as np
#from numpy import arange, sin, pi

# This is just for the GPIB-232CV-A -- may not apply for other GPIB
# interfaces
HP8903_BAUD = 38400

UI_INFO = """
<ui>
  <menubar name='MenuBar'>
    <menu action='FileMenu'>
    <separator />
      <menuitem action='FileQuit' />
    </menu>
  </menubar>
</ui>
"""

class HP8903BWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="HP 8903B Control")

        # Serial connection!
        self.ser = None
        self.devices = serial.tools.list_ports_posix.comports()
        
        # Menu Bar junk!
        action_group = Gtk.ActionGroup("my_actions")
        action_filemenu = Gtk.Action("FileMenu", "File", None, None)
        action_group.add_action(action_filemenu)
        action_filequit = Gtk.Action("FileQuit", None, None, Gtk.STOCK_QUIT)
        action_filequit.connect("activate", self.on_menu_file_quit)
        action_group.add_action(action_filequit)

        uimanager = self.create_ui_manager()
        uimanager.insert_action_group(action_group)

        menubar = uimanager.get_widget("/MenuBar")

        
        self.master_vbox = Gtk.Box(False, spacing = 2, orientation = 'vertical')
        self.master_vbox.pack_start(menubar, False, False, 0)
        master_hsep = Gtk.HSeparator()
        self.master_vbox.pack_start(master_hsep, False, False, 0)
        self.add(self.master_vbox)
        
        self.hbox = Gtk.Box(spacing = 2)
        self.master_vbox.pack_start(self.hbox, True, True, 0)

        bframe = Gtk.Frame(label = "Control")
        left_vbox = Gtk.Box(spacing = 2, orientation = 'vertical')
        self.box = Gtk.Box(spacing = 2)

        bframe.add(left_vbox)
        left_vbox.pack_start(self.box, False, False, 0)

        self.hbox.pack_start(bframe, False, False, 0)

        con_hbox = Gtk.Box(spacing = 2)
        self.con_button = Gtk.Button(label = "Connect")
        self.dcon_button = Gtk.Button(label = "Disconnect")

        self.con_button.connect("clicked", self.setup_serial)
        self.dcon_button.connect("clicked", self.close_serial)
        
        con_hbox.pack_start(self.con_button, False, False, 0)
        con_hbox.pack_start(self.dcon_button, False, False, 0)

        left_vbox.pack_start(con_hbox, False, False, 0)
        
        device_store = Gtk.ListStore(int, str)
        for i in range(len(self.devices)):
            device_store.append([i, self.devices[i][0]])
        self.device_combo = Gtk.ComboBox.new_with_model_and_entry(device_store)
        self.device_combo.set_entry_text_column(1)
        self.device_combo.set_active(0)

        device_label = Gtk.Label("Device: ")
        
        self.box.pack_start(device_label, False, False, 0)
        self.box.pack_start(self.device_combo, False, False, 0)

        hsep0 = Gtk.HSeparator()
        left_vbox.pack_start(hsep0, False, False, 2)
        
        #side_filler = Gtk.Box(spacing = 2, orientation = 'vertical')
        swconf = Gtk.Frame(label = "Sweep Control")
        swhbox = Gtk.Box(spacing = 2)
        swbox = Gtk.Box(spacing = 2, orientation = 'vertical')
        swconf.add(swbox)
        swhbox.pack_start(swconf, False, False, 0)
        left_vbox.pack_start(swhbox, False, False, 0)
        
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

        hsep1 = Gtk.HSeparator()
        left_vbox.pack_start(hsep1, False, False, 2)

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

        hsep2 = Gtk.HSeparator()
        left_vbox.pack_start(hsep2, False, False, 2)

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
        self.a.set_ylim((-90.0, 3.0))
        self.a.set_xlabel("Frequency (Hz)")
        self.a.set_ylabel("THD+n (%)")
        
        self.canvas = FigureCanvas(self.f)

        self.hbox.pack_start(self.canvas, True, True, 0)

    def setup_serial(self, button):
        print("serial!")
        model = self.device_combo.get_model()

        tree_iter = self.device_combo.get_active_iter()

        print(model[tree_iter][1])
        self.con_button.set_sensitive(False)
        self.device_combo.set_sensitive(False)

        try:
            self.ser = serial.Serial(model[tree_iter][1],
                                     HP8903_BAUD,
                                     bytesize = serial.SEVENBITS,
                                     stopbits = serial.STOPBITS_ONE,
                                     parity = serial.PARITY_NONE)

            self.ser.flushInput()
            
            self.run_button.set_sensitive(True)
            
            self.init_hp8903()

        except:
            Exception("Failed to open serial device")



    def close_serial(self, button):
        self.con_button.set_sensitive(True)
        self.device_combo.set_sensitive(True)

        if (self.ser != None):
            self.ser.close()

        self.run_button.set_sensitive(False)

    def run_test(self, button):
        self.run_button.set_sensitive(False)
        x = []
        y = []

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
        
        # print(step_size)
        # print(math.floor(math.log10(self.start_freq.get_value())))
        
        lsteps = np.logspace(strt_dec, stop_dec + 1, num_steps*(stop_dec - strt_dec + 1))
        lsteps = lsteps[(lsteps > strtf) & (lsteps < stopf)]
        
        for i in lsteps:
            meas = self.send_measurement(i, amp, filters)
            x.append(float(i))
            y.append(float(meas))
            self.update_plot(x, y)
            # plot new measures
            print(meas)

        self.run_button.set_sensitive(True)

    def update_plot(self, x, y):
        if (len(self.plt) < 1):
            self.plt = self.a.plot(x, y, marker = 'x')
        self.plt[0].set_data(x, y)
        ymin = min(y)
        ymax = max(y)
        self.a.set_ylim((ymin - ymin*0.10, ymax + ymax*0.10))
        self.canvas.draw()
            
    def init_hp8903(self):
        self.ser.flushInput()
        if (self.ser != None):
            self.ser.write("AP1VLM1LNL0LNT3")
        while (self.ser.inWaiting() < 12):
            while Gtk.events_pending():
                Gtk.main_iteration_do(False)

        meas = self.ser.read(self.ser.inWaiting())
        print(meas)
        print(float(meas))
        print("HP 8903B Initialized")
        
        
    def send_measurement(self, freq, amp, filters):
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

        source_freq = ("FR%.4EHZ" % freq)
        source_ampl = ("AP%.4EVL" % amp)
        filter_s = fs1 + fs2

        payload = source_freq + source_ampl + "M3LN" + filter_s + "LNT3"
        #print(payload)
        #print("FR%.4EHZAP1VLM1LNL0LNT3" % freq)
        #print("FR%.4EHZAP%.4EVLM3LNL0LNT3" % (freq, amp))
        #self.ser.write(("FR%.4EHZAP%.4EVLM3LNL2LNT3" % (freq, amp)))
        self.ser.write(payload)
        while (self.ser.inWaiting() < 12):
            #print(ser.inWaiting())
            while Gtk.events_pending():
                 Gtk.main_iteration_do(False)
        return self.ser.read(self.ser.inWaiting())

    def freq_callback(self, spinb):
        if (self.start_freq.get_value() > self.stop_freq.get_value()):
            self.start_freq.set_value(self.stop_freq.get_value())

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
        if (self.ser != None):
            self.ser.close()
        Gtk.main_quit()

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
