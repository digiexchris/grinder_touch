import hal
import linuxcnc
import time
import traceback
from GrinderCommon import GrinderCommon
from hal_glib import GStat
from threading import Thread

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject
from gi.repository import GLib

class GrinderMotion():
    def __init__(self):

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
        # print(running)
        # print(self.is_running)
        if self.is_running != running:
            print(running)
            print(self.is_running)
            self.is_running = running
            print(running)
            print(self.is_running)
            if running:
                print("Start request BE")
                self.start()
            else:
                print("Stop request BE")
                self.stop()

    def start(self, obj = None):
        if not self.GSTAT.estop_is_clear and not self.GSTAT.machine_is_on:
            return
        
        #THIS THREAD CAUSES THIS TO HANG, no more gstat events come in.
        # self.thread = Thread(target=self.main_sequence)
        # self.thread.run()

    def stop(self, obj = None):
        print("Stopping BE")
        self.c.mode(linuxcnc.MODE_MDI)
        self.c.wait_complete()
        self.c.abort()
        self.c.mode(linuxcnc.MODE_MANUAL)
        #self.thread._stop().set()

    def update_pos(self, obj, absolute_pos, relative_pos, dist_to_go, joint_pos):
        self.pos = relative_pos
        self.onModeChanged()

    def get_pos(self, axis):
        return round(self.pos[axis.to_int()], self.get_rounding_tolerance())

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
    def main_sequence(self):
        
        #self.GSTAT.emit("general",  {"ID":"GRINDER.STARTED"})
        print("Started")
        # self.is_running = True
        while True:
            # if not self.is_running:
            #     self.c.mode(linuxcnc.MODE_MDI)
            #     self.c.wait_complete()
            #     self.c.abort()
            #     self.c.wait_complete()
            #     print("Stopped")
            #     return
            
            time.sleep(0.15)

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

