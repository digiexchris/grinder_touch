import hal

from hal_glib import GStat
import time
    
GSTAT = GStat()

class GrinderHal():

    # def __init__(self):


    def initialize_hal(self):
        self.h = hal.component("grinder")
        self.c = linuxcnc.command()

        self.x_min = self.h.newpin("x_min", hal.HAL_FLOAT, hal.HAL_IN)
        self.x_max = self.h.newpin("x_max", hal.HAL_FLOAT, hal.HAL_IN)
        self.y_min = self.h.newpin("y_min", hal.HAL_FLOAT, hal.HAL_IN)
        self.y_max = self.h.newpin("y_max", hal.HAL_FLOAT, hal.HAL_IN)
        self.z_min = self.h.newpin("z_min", hal.HAL_FLOAT, hal.HAL_IN)
        self.z_max = self.h.newpin("z_max", hal.HAL_FLOAT, hal.HAL_IN)
        self.x_speed = self.h.newpin("x_speed", hal.HAL_FLOAT, hal.HAL_IN)
        self.x_speed = self.h.newpin("y_speed", hal.HAL_FLOAT, hal.HAL_IN)
        self.z_speed = self.h.newpin("z_speed", hal.HAL_FLOAT, hal.HAL_IN)
        self.z_speed = self.h.newpin("z_direction", hal.HAL_BIT, hal.HAL_IO)
        self.z_speed = self.h.newpin("z_crossfeed", hal.HAL_FLOAT, hal.HAL_IN)
        self.z_speed = self.h.newpin("y_downfeed", hal.HAL_FLOAT, hal.HAL_IN)
        self.z_speed = self.h.newpin("downfeed_now", hal.HAL_BIT, hal.HAL_IO)
        self.z_speed = self.h.newpin("enable_x", hal.HAL_BIT, hal.HAL_IO)
        self.z_speed = self.h.newpin("enable_y", hal.HAL_BIT, hal.HAL_IO)
        self.z_speed = self.h.newpin("enable_z", hal.HAL_BIT, hal.HAL_IO)
        self.z_speed = self.h.newpin("stop_at_z_limit", hal.HAL_BIT, hal.HAL_IN)
        self.z_speed = self.h.newpin("crossfeed_at", hal.HAL_S32, hal.HAL_IN)
        self.z_speed = self.h.newpin("repeat_at", hal.HAL_S32, hal.HAL_IN)
        self.z_speed = self.h.newpin("is_running", hal.HAL_BIT, hal.HAL_IO)
        
        self.h.ready()

        print("Grinder hal ready")

        self.z_direction.set(str(1))

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
        hal.set_p("grinder.downfeed_now", str(False))

        # Enable and control signals
        hal.set_p("grinder.enable_x", str(False))
        hal.set_p("grinder.enable_y", str(False))
        hal.set_p("grinder.enable_z", str(False))
        hal.set_p("grinder.stop_at_z_limit", str(False))

        # Crossfeed and repeat settings
        hal.set_p("grinder.crossfeed_at", str(0))
        hal.set_p("grinder.repeat_at", str(0))

        hal.set_p("grinder.is_running", str(False))

    def load_settings():
        if os.path.exists(self.settings_file):
            with open(self.settings_file, "rb") as file:
                self.settings = pickle.load(file)
                # print(self.settings)
                print("Grinder settings loaded")
        else:
            self.settings = {}
            print("Empty settings loaded")



        self.previous_linear_units = self.settings.get('previous_linear_units',1)
        set_hal("x_min", self.settings.get('x_min',0))
        set_hal("x_max", self.settings.get('x_max', self.get_converted_value(1, "inch")))
        set_hal("y_min", self.settings.get('y_min',0))
        set_hal("y_max", self.settings.get('y_max', self.get_converted_value(1, "inch")))
        set_hal("z_min",  self.settings.get('z_min',0))
        set_hal("z_max",  self.settings.get('z_max', self.get_converted_value(1, "inch")))
        

        set_hal("x_speed",  self.settings.get('x_speed', self.get_converted_value(500, "inch")))
        # print("X_SPEED:")
        # print(get_hal("x_speed"))
        # print(self.get_converted_value(500, "inch"))
        set_hal("y_speed",  self.settings.get('y_speed', self.get_converted_value(200, "inch")))
        set_hal("z_speed",  self.settings.get('z_speed', self.get_converted_value(200, "inch")))
        

        set_hal("z_crossfeed",  self.settings.get('z_crossfeed', self.get_converted_value(0.005, "inch")))        
        set_hal("y_downfeed",  self.settings.get('y_downfeed', self.get_converted_value(0.0005, "inch")))
        
        set_hal("enable_x",  self.settings.get('enable_x', bool(False)))
        set_hal("enable_y",  self.settings.get('enable_y', bool(False)))
        set_hal("enable_z",  self.settings.get('enable_z', bool(False)))

        set_hal("stop_at_z_limit",  self.settings.get('stop_at_z_limit', 0))

        set_hal("crossfeed_at",  self.settings.get('crossfeed_at', 2))
        set_hal("repeat_at",  self.settings.get('repeat_at', 1))

        ############## DRESS PARAMS ################

    def get_rounding_tolerance():
        # Check the current units
        if GSTAT.is_metric_mode():
            return 4
        else:
            return 5

    def set_hal(field, value):
        # print("Setting hal value: "+str(value))
        hal.set_p("grinder."+field, str(value))
            
    def get_hal(field):
        return hal.get_value("grinder."+field)
    
    def waitForComponentReady(timeoutInSeconds):
        start_time = time.time()
        while True:
            if time.time() - start_time > timeoutInSeconds:
                return False
            try:
                if hal.component_exists("grinder"):
                    return True
            except:
                pass