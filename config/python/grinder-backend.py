#!/usr/bin/python3

import threading
import hal
import linuxcnc
import time
import traceback
from axis import Axis
from grinderhal import GrinderHal
from hal_glib import GStat
from kthread import KThread

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib

linear_units_inch = 0.3937007874015748
linear_units_mm = 1.0

class GrinderMotion():
    def __init__(self):
        self.status = linuxcnc.stat()
        self.error_chan = linuxcnc.error_channel()
        self.thread = None
        # Initialize HAL and LinuxCNC
        self.initialize_hal()
        self.pos = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.is_running = False
        self.is_on = False
        self.is_estop = True
        self.is_ready = False
        self.units = linear_units_inch
        self.last_units = linear_units_inch

    def __del__(self):
        print("GrinderMotion cleaned up")

    def shutdown(self):
        print("Shutdown signal recvd")
        quit()

    def onModeChanged(self):
        running = bool(GrinderHal.get_hal("is_running"))

        if self.is_running != running:
            self.is_running = running
            if running:
                print("Start request recieved by Grinder Backend")
                self.start()
            else:
                print("Stop request recieved by Grinder Backend")
                self.stop()

    def start(self, obj = None):
        # print("READY:", self.is_ready)
        if not self.is_ready:
            if self.is_running:
                GrinderHal.set_hal("is_running", False)
                self.is_running = False
            return
        
        self.thread = KThread(target = self.main_sequence, name = "MainLoop")
        self.thread.start()

    def stopThread(self):
        try:
            if self.thread != None:
                self.thread.terminate()
        except threading.ThreadError:
            print("BE thread already stopped")

    def stop(self, obj = None):
        print("Stopping Grinder Backend")
        
        self.c.abort()
        self.stopThread()

    def update_pos(self):
        pos = self.status.position
        offset = self.status.g5x_offset

        for i in range(len(pos)):
            self.pos[i] = pos[i] - offset[i]

    def get_pos(self, axis):
        return round(self.pos[axis.to_int()], GrinderHal.get_rounding_tolerance())

    

        self.status.poll()

        self.units = self.status.linear_units
        # print("Initial units", self.units)

    # Main logic sequence

    def print_mode(self):
        
        self.status.poll()
        if self.status.task_mode == linuxcnc.MODE_MANUAL:
            print("Current mode: Manual")
        elif self.status.task_mode == linuxcnc.MODE_AUTO:
            print("Current mode: Auto")
        elif self.status.task_mode == linuxcnc.MODE_MDI:
            print("Current mode: MDI")


    def print_error(self, error):
        print(f"Linuxcnc error returned: {error}")

    def print_mdi_error(self, thing):
            self.c.abort()
            GrinderHal.set_hal("is_running", False)
            self.c.mode(linuxcnc.MODE_MANUAL)
            self.c.wait_complete()
            self.status.poll()

            e = linuxcnc.error_channel()
            error = e.poll()

            if error:
                kind, text = error
                if kind in (linuxcnc.NML_ERROR, linuxcnc.OPERATOR_ERROR):
                    typus = "error"
                else:
                    typus = "info"
                print(typus, text)
            
    def get_max_wait(self):
        return 30 #max(x_time_sec, max(y_time_sec, z_time_sec))

    def update_is_ready(self):
        estop = self.status.estop
        if estop != self.is_estop:
            self.is_estop = estop

            if self.is_estop:
                if self.is_running:
                    self.stop()
                self.is_ready = False
                self.is_running = False;
                GrinderHal.set_hal("is_running", False)

        on = self.status.enabled
        if on != self.is_on:
            self.is_on = on

            if not self.is_on:
                if self.is_running:
                    self.stop();
                self.is_ready = False;
                GrinderHal.set_hal("is_running", False)

        if ((not self.is_estop) and (self.is_on)):
            # print("Machine is ready")
            self.is_ready = True

    def convert_units(self):
        # Get all the min/max values
        x_min = float(GrinderHal.get_hal("x_min"))
        x_max = float(GrinderHal.get_hal("x_max"))
        y_min = float(GrinderHal.get_hal("y_min"))
        y_max = float(GrinderHal.get_hal("y_max"))
        z_min = float(GrinderHal.get_hal("z_min"))
        z_max = float(GrinderHal.get_hal("z_max"))

        # print(self.units, self.last_units)

        # Convert each value using the ratio of units
        conversion = self.units / self.last_units
        x_min *= conversion 
        x_max *= conversion
        y_min *= conversion
        y_max *= conversion
        z_min *= conversion
        z_max *= conversion

        # Set the converted values back to HAL
        GrinderHal.set_hal("x_min", str(x_min))
        GrinderHal.set_hal("x_max", str(x_max))
        GrinderHal.set_hal("y_min", str(y_min))
        GrinderHal.set_hal("y_max", str(y_max))
        GrinderHal.set_hal("z_min", str(z_min))
        GrinderHal.set_hal("z_max", str(z_max))

    def updateLinearUnits(self):
        updated_units = self.status.linear_units

        if self.units == 0 or self.last_units == 0:
            if updated_units != 0:
                self.units = updated_units
                self.last_units = updated_units
                return

        if abs(updated_units - self.units) > 0.0001:
            # print(updated_units, self.units)
            self.last_units = self.units
            self.units = updated_units

            self.convert_units()

            self.last_units = self.units

    def updateErrors(self):
        error = self.error_chan.poll();
        if error:
            kind, text = error
            if kind in (linuxcnc.NML_ERROR, linuxcnc.OPERATOR_ERROR):
                typus = "error"
            else:
                typus = "info"
            print(typus, text)

    def update(self):
        self.status.poll()
        self.update_is_ready()
        self.update_pos()
        self.onModeChanged()
        self.updateLinearUnits()
        self.updateErrors()

        if not self.is_running:
            if GrinderHal.get_hal("downfeed_now"):
                self.downfeed_now()

    def main_loop(self) :
        exit = True
        while(exit):
            # print("START UPDATE")
            time.sleep(0.1)
            try:
                self.update();

                # print("UPDATE COMPLETE")
                
                # time.sleep(1)
            except linuxcnc.error as detail:
                print("error", detail)
                self.stop()
                return

    def reset_downfeed_trigger(self):
        GrinderHal.set_hal("downfeed_now", False)

    def downfeed_now(self):
        self.c.mode(linuxcnc.MODE_MDI)
        self.c.wait_complete()
        y_pos = self.get_pos(Axis.Y)
        y_max = float(GrinderHal.get_hal("y_max"))
        y_min = float(GrinderHal.get_hal("y_min"))
        y_downfeed = float(GrinderHal.get_hal("y_downfeed"))

        new_y_pos = y_pos - y_downfeed

        if new_y_pos < y_min:
            GrinderHal.set_hal("y_min", new_y_pos)

        mdi = f"G1 Y{new_y_pos}"
        self.c.mdi(mdi)
        self.c.wait_complete(self.get_max_wait())

        self.reset_downfeed_trigger()

    def main_sequence(self):
        print("Started Grind Sequence")  

        try:
            self.status.poll() # an early test to see if linuxcnc is still running      

            if bool(GrinderHal.get_hal("downfeed_now")):
                self.reset_downfeed_trigger()

            self.c.mode(linuxcnc.MODE_MDI)
            self.c.wait_complete()

            x_pos = self.get_pos(Axis.X)
            x_max = float(GrinderHal.get_hal("x_max"))
            x_min = float(GrinderHal.get_hal("x_min"))
            y_pos = self.get_pos(Axis.Y)
            y_max = float(GrinderHal.get_hal("y_max"))
            y_min = float(GrinderHal.get_hal("y_min"))
            z_pos = self.get_pos(Axis.Z)
            z_max = float(GrinderHal.get_hal("z_max"))
            z_min = float(GrinderHal.get_hal("z_min"))

#check if limits make sense
            # if x_min > x_max + 0.00001 and bool(GrinderHal.get_hal("enable_x")):
                


#move into limits
            if x_pos > x_max + 0.00001 and bool(GrinderHal.get_hal("enable_x")):
                mdi = f"G0 X{x_max}"
                self.c.mdi(mdi)
                self.c.wait_complete(self.get_max_wait())

            if y_pos > y_max + 0.00001 and bool(GrinderHal.get_hal("enable_y")):
                mdi = f"G0 Y{y_max}"
                self.c.mdi(mdi)
                self.c.wait_complete(self.get_max_wait())

            if z_pos > z_max + 0.00001 and bool(GrinderHal.get_hal("enable_z")):
                mdi = f"G0 Z{z_max}"
                self.c.mdi(mdi)
                self.c.wait_complete(self.get_max_wait())

            if x_pos < x_min - 0.00001 and bool(GrinderHal.get_hal("enable_x")):
                mdi = f"G0 X{x_min}"
                self.c.mdi(mdi)
                self.c.wait_complete(self.get_max_wait())

            if y_pos < y_min - 0.00001 and bool(GrinderHal.get_hal("enable_y")):
                mdi = f"G0 Y{y_min}"
                self.c.mdi(mdi)
                self.c.wait_complete(self.get_max_wait())

            if z_pos < z_min - 0.00001 and bool(GrinderHal.get_hal("enable_z")):
                mdi = f"G0 Z{z_min}"
                self.c.mdi(mdi)
                self.c.wait_complete(self.get_max_wait())
            
            while True:
                self.status.poll() # an early test to see if linuxcnc is still running
                
                if not self.is_running:
                    
                    self.c.abort()
                    self.c.wait_complete()
                    print("Stopped Grinder Sequence")
                    # return
                else:
                    # print("Loop")

                    if not self.is_running:
                        return

                    self.c.mode(linuxcnc.MODE_MDI)
                    self.c.wait_complete()

                    if bool(GrinderHal.get_hal("downfeed_now")):
                        self.downfeed_now()
                    
                    if not self.is_running:
                        return

                    self.c.mdi("o<xmove_to_max> call")
                    self.c.wait_complete(self.get_max_wait())

                    self.status.poll() # an early test to see if linuxcnc is still running

                    if bool(GrinderHal.get_hal("downfeed_now")):
                        self.downfeed_now()

                    if not self.is_running:
                        return

                    self.c.mdi("o<xmove_to_min> call")
                    self.c.wait_complete(self.get_max_wait())

                    # print("End Loop")
                    
                    time.sleep(0.055)
        except linuxcnc.error as detail:
            print("error", detail)
            self.stop()
            return

    def quit(self):
        
        try:
            self.c.abort()
        except:
            print("Error while sending abort command, Linuxcnc is probably stopped. Ignoring")

        try:
            self.stopThread()
        except:
            print("Error while stopping main sequence thread, Linuxcnc is probably stopped. Ignoring")

# Run the main sequence
try:
    grinderBackend = GrinderMotion()
    
    print("GRINDER_BACKEND STARTED")
    grinderBackend.main_loop()
    print("GRINDER_BACKEND MAIN LOOP EXITED")
# GLib.MainLoop().run()
except KeyboardInterrupt:
    grinderBackend.quit()
    print("Grinder Backend Motion controller stopped.")
    # GLib.MainLoop().stop()
    raise SystemExit

