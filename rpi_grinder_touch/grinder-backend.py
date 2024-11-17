import threading
import hal
import linuxcnc
import time
import traceback
from GrinderCommon import GrinderCommon, Axis
from hal_glib import GStat
from kthread import KThread

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject
from gi.repository import GLib

class GrinderMotion():
    def __init__(self):
        self.status = linuxcnc.stat()
        self.GSTAT = GStat()
        self.thread = None
        # Initialize HAL and LinuxCNC
        self.initialize_hal()
        self.pos = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.GSTAT.connect("current-position", self.update_pos)
        self.GSTAT.connect("state-estop", self.stop)
        self.GSTAT.connect("state-off", self.stop)
        self.is_running = False
    def __del__(self):
        print("GrinderMotion cleaned up")

    def onModeChanged(self):
        running = bool(GrinderCommon.get_hal("is_running"))

        if self.is_running != running:
            self.is_running = running
            if running:
                print("Start request BE")
                self.start()
            else:
                print("Stop request BE")
                self.stop()

    def start(self, obj = None):
        if not self.GSTAT.estop_is_clear and not self.GSTAT.machine_is_on and not self.GSTAT.is_all_homed:
            if self.is_running:
                GrinderCommon.set_hal("is_running", False)
                self.is_running = False
            return
        
        self.thread = threading.Thread(target = self.main_sequence, name = "MainLoop")
        self.thread.start()
        #THIS THREAD CAUSES THIS TO HANG, no more gstat events come in.
        # self.thread = Thread(target=self.main_sequence)
        # self.thread.run()

    def stop(self, obj = None):
        print("Stopping BE")
        try:
            if self.thread != None:
                self.thread.terminate()
        except threading.ThreadError:
            print("BE thread already stopped")
        
        self.c.abort()
        # self.c.mode(linuxcnc.MODE_MANUAL)
        #self.thread._stop().set()

    def update_pos(self, obj, absolute_pos, relative_pos, dist_to_go, joint_pos):
        self.pos = relative_pos
        self.onModeChanged()

    def get_pos(self, axis):
        return round(self.pos[axis.to_int()], GrinderCommon.get_rounding_tolerance())

    def initialize_hal(self):
        self.h = hal.component("grinder")
        self.c = linuxcnc.command()

        self.h.newpin("x_min", hal.HAL_FLOAT, hal.HAL_IN)
        self.h.newpin("x_max", hal.HAL_FLOAT, hal.HAL_IN)
        self.h.newpin("y_min", hal.HAL_FLOAT, hal.HAL_IN)
        self.h.newpin("y_max", hal.HAL_FLOAT, hal.HAL_IN)
        self.h.newpin("z_min", hal.HAL_FLOAT, hal.HAL_IN)
        self.h.newpin("z_max", hal.HAL_FLOAT, hal.HAL_IN)
        self.h.newpin("x_speed", hal.HAL_FLOAT, hal.HAL_IN)
        self.h.newpin("y_speed", hal.HAL_FLOAT, hal.HAL_IN)
        self.h.newpin("z_speed", hal.HAL_FLOAT, hal.HAL_IN)
        self.h.newpin("z_direction", hal.HAL_BIT, hal.HAL_IO)
        self.h.newpin("z_crossfeed", hal.HAL_FLOAT, hal.HAL_IN)
        self.h.newpin("y_downfeed", hal.HAL_FLOAT, hal.HAL_IN)
        self.h.newpin("enable_x", hal.HAL_BIT, hal.HAL_IO)
        self.h.newpin("enable_y", hal.HAL_BIT, hal.HAL_IO)
        self.h.newpin("enable_z", hal.HAL_BIT, hal.HAL_IO)
        self.h.newpin("stop_at_z_limit", hal.HAL_BIT, hal.HAL_IN)
        self.h.newpin("crossfeed_at", hal.HAL_S32, hal.HAL_IN)
        self.h.newpin("repeat_at", hal.HAL_S32, hal.HAL_IN)
        self.h.newpin("is_running", hal.HAL_BIT, hal.HAL_IO)
        
        self.h.ready()

        print("Grinder hal ready")

        #hal.new_sig("grinder.z_direction", hal.HAL_BIT)

        hal.set_p("grinder.z_direction", str(1))

        hal.set_p("grinder.x_min", str(0.0))
        hal.set_p("grinder.x_max", str(0.0))
        hal.set_p("grinder.y_min", str(0.0))
        hal.set_p("grinder.y_max", str(0.0))
        hal.set_p("grinder.z_min", str(0.0))
        hal.set_p("grinder.z_max", str(0.0))

        hal.set_p("grinder.x_speed", str(0.0))
        hal.set_p("grinder.y_speed", str(0.0))
        hal.set_p("grinder.z_speed", str(0.0))

        hal.set_p("grinder.z_crossfeed", str(0.0))
        hal.set_p("grinder.y_downfeed", str(0.0))

        # Enable and control signals
        hal.set_p("grinder.enable_x", str(False))
        hal.set_p("grinder.enable_y", str(False))
        hal.set_p("grinder.enable_z", str(False))
        hal.set_p("grinder.stop_at_z_limit", str(False))

        # Crossfeed and repeat settings
        hal.set_p("grinder.crossfeed_at", str(0))
        hal.set_p("grinder.repeat_at", str(0))

        hal.set_p("grinder.is_running", str(False))
    # Main logic sequence

    def print_mode(self):
        
        self.status.poll()
        if self.status.task_mode == linuxcnc.MODE_MANUAL:
            print("Current mode: Manual")
        elif self.status.task_mode == linuxcnc.MODE_AUTO:
            print("Current mode: Auto")
        elif self.status.task_mode == linuxcnc.MODE_MDI:
            print("Current mode: MDI")

    def main_sequence(self):
        
        #self.GSTAT.emit("general",  {"ID":"GRINDER.STARTED"})
        print("Started")
        # self.is_running = True

        self.c.mode(linuxcnc.MODE_MDI)
        self.c.wait_complete()

        x_pos = self.get_pos(Axis.X)
        x_max = float(GrinderCommon.get_hal("x_max"))
        x_min = float(GrinderCommon.get_hal("x_min"))
        y_pos = self.get_pos(Axis.Y)
        y_max = float(GrinderCommon.get_hal("y_max"))
        y_min = float(GrinderCommon.get_hal("y_min"))
        z_pos = self.get_pos(Axis.Z)
        z_max = float(GrinderCommon.get_hal("z_max"))
        z_min = float(GrinderCommon.get_hal("z_min"))

        if x_pos > x_max:
            mdi = f"G0 X{x_max}"
            self.c.mdi(mdi)

        if y_pos > y_max:
            mdi = f"G0 Y{y_max}"
            self.c.mdi(mdi)

        if z_pos > z_max:
            mdi = f"G0 Z{z_max}"
            self.c.mdi(mdi)

        if x_pos < x_min:
            mdi = f"G0 X{x_min}"
            self.c.mdi(mdi)

        if y_pos < y_min:
            mdi = f"G0 Y{y_min}"
            self.c.mdi(mdi)

        if z_pos < z_min:
            mdi = f"G0 Z{z_min}"
            self.c.mdi(mdi)
        

        while True:

            # the thread will be terminated by the outside process, but just in case this can stop it faster:
            if not self.is_running:
                
                self.c.abort()
                self.c.wait_complete()
                print("Stopped")
                time.sleep(1)
                # return
            else:
                print("Loop")
                self.print_mode()
                time.sleep(1)

                self.c.mode(linuxcnc.MODE_MDI)
                self.c.wait_complete()
                self.print_mode()
                self.c.mdi("o<xmove_to_max> call")
                self.print_mode()
                self.c.mdi("o<xmove_to_min> call")
                self.c.wait_complete()

                self.print_mode()
                
                time.sleep(1)

# Run the main sequence


try:
    grinder = GrinderMotion()
    print("GRINDER_BACKEND STARTED")
    GLib.MainLoop().run()
except KeyboardInterrupt:
    print("Motion controller stopped.")
    #GLib.MainLoop().stop()
    raise SystemExit
except Exception:
    print(traceback.format_exc())

