#!/usr/bin/python

from gi.repository import Gtk, GObject

from matplotlib.figure import Figure
from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas

import serial
import serial.tools.list_ports_posix
    
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

        hsep = Gtk.HSeparator()
        left_vbox.pack_start(hsep, False, False, 0)

        self.run_button = Gtk.Button(label = "Start Sequence")
        self.run_button.set_sensitive(False)
        left_vbox.pack_start(self.run_button, False, False, 0)

        self.run_button.connect("clicked", self.run_test)
        
        device_store = Gtk.ListStore(int, str)
        for i in range(len(self.devices)):
            device_store.append([i, self.devices[i][0]])
        self.device_combo = Gtk.ComboBox.new_with_model_and_entry(device_store)
        self.device_combo.set_entry_text_column(1)
        self.device_combo.set_active(0)

        device_label = Gtk.Label("Device: ")
        
        self.box.pack_start(device_label, False, False, 0)
        self.box.pack_start(self.device_combo, False, False, 0)

        side_filler = Gtk.Box(spacing = 2, orientation = 'vertical')
        
        
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
        for i in (20.0, 40.0, 100.0, 500.0, 1000.0, 2000.0, 3000.0, 4000.0, 5000.0, 6000.0, 7000.0, 8000.0, 9000.0, 18000.0, 20000.0, 22000.0):
            meas = self.send_measurement(i)
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
            pass

        meas = self.ser.read(self.ser.inWaiting())
        print(meas)
        print(float(meas))
        print("HP 8903B Initialized")
        
        
    def send_measurement(self, freq):
        #print("FR%.4EHZAP1VLM1LNL0LNT3" % freq)
        self.ser.write(("FR%.4EHZAP1VLM3LNL0LNT3" % freq))
        while (self.ser.inWaiting() < 12):
            while Gtk.events_pending():
                 Gtk.main_iteration_do(False)
            pass
        return self.ser.read(self.ser.inWaiting())

    
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
