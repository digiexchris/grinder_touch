import hal
import os
from hal_glib import GStat
import time
    
GSTAT = GStat()

import pickle

# settings = {}
settings_file = "grinder.pkl"
previous_linear_units = 1

class GrinderHal():
    def get_converted_value(value, units):
        if units != "inch" and units != "mm":
            raise Exception("Get converted value called with invalid unit type")

        if GSTAT.is_metric_mode():
            if units == "mm":
                return value
            else:
                return value*25.4
        else:
            if units == "inch":
                return value
            else:
                return value/25.4

    def initialize_hal():
        # h = hal.component("grinder")
        # h.newpin("x_min", hal.HAL_FLOAT, hal.HAL_IO)
        # h.newpin("x_max", hal.HAL_FLOAT, hal.HAL_IO)
        # h.newpin("y_min", hal.HAL_FLOAT, hal.HAL_IO)
        # h.newpin("y_max", hal.HAL_FLOAT, hal.HAL_IO)
        # h.newpin("z_min", hal.HAL_FLOAT, hal.HAL_IO)
        # h.newpin("z_max", hal.HAL_FLOAT, hal.HAL_IO)
        # h.newpin("x_speed", hal.HAL_FLOAT, hal.HAL_IO)
        # h.newpin("y_speed", hal.HAL_FLOAT, hal.HAL_IO)
        # h.newpin("z_speed", hal.HAL_FLOAT, hal.HAL_IO)
        # h.newpin("z_direction", hal.HAL_BIT, hal.HAL_IO)
        # h.newpin("z_crossfeed", hal.HAL_FLOAT, hal.HAL_IO)
        # h.newpin("y_downfeed", hal.HAL_FLOAT, hal.HAL_IO)
        # h.newpin("downfeed_now", hal.HAL_BIT, hal.HAL_IO)
        # h.newpin("enable_x", hal.HAL_BIT, hal.HAL_IO)
        # h.newpin("enable_y", hal.HAL_BIT, hal.HAL_IO)
        # h.newpin("enable_z", hal.HAL_BIT, hal.HAL_IO)
        # h.newpin("stop_at_z_limit", hal.HAL_BIT, hal.HAL_IO)
        # h.newpin("crossfeed_at", hal.HAL_S32, hal.HAL_IO)
        # h.newpin("repeat_at", hal.HAL_S32, hal.HAL_IO)
        # h.newpin("is_running", hal.HAL_BIT, hal.HAL_IO)

        # h.newpin("dress_start_x", hal.HAL_FLOAT, hal.HAL_IO)
        # h.newpin("dress_start_y", hal.HAL_FLOAT, hal.HAL_IO)
        # h.newpin("dress_start_z", hal.HAL_FLOAT, hal.HAL_IO)
        # h.newpin("dress_end_x", hal.HAL_FLOAT, hal.HAL_IO)
        # h.newpin("dress_end_y", hal.HAL_FLOAT, hal.HAL_IO)
        # h.newpin("dress_end_z", hal.HAL_FLOAT, hal.HAL_IO)
        # h.newpin("dress_stepover_x", hal.HAL_FLOAT, hal.HAL_IO)
        # h.newpin("dress_stepover_y", hal.HAL_FLOAT, hal.HAL_IO)
        # h.newpin("dress_stepover_z", hal.HAL_FLOAT, hal.HAL_IO)
        # h.newpin("dress_wheel_rpm", hal.HAL_FLOAT, hal.HAL_IO)
        # h.newpin("dress_wheel_dia", hal.HAL_FLOAT, hal.HAL_IO)
        # h.newpin("dress_point_dia", hal.HAL_FLOAT, hal.HAL_IO)
        # h.newpin("dress_overlap_ratio", hal.HAL_FLOAT, hal.HAL_IO)
        # h.newpin("dress_safe_y", hal.HAL_FLOAT, hal.HAL_IO)
        # h.newpin("dress_offset_gcode", hal.HAL_S32, hal.HAL_IO)

        # h.ready()

        # print("Grinder hal ready")

        # hal.set_p("grinder.z_direction",str(1))

        # # hal.set_p("grinder.x_min", str(0.0))
        # # hal.set_p("grinder.x_max", str(0.0))
        # # hal.set_p("grinder.y_min", str(0.0))
        # # hal.set_p("grinder.y_max", str(0.0))
        # # hal.set_p("grinder.z_min", str(0.0))
        # # hal.set_p("grinder.z_max", str(0.0))

        # # hal.set_p("grinder.x_speed", str(0.0))
        # # hal.set_p("grinder.y_speed", str(0.0))
        # # hal.set_p("grinder.z_speed", str(0.0))

        # # hal.set_p("grinder.z_crossfeed", str(0.0))
        # # hal.set_p("grinder.y_downfeed", str(0.0))
        # # hal.set_p("grinder.downfeed_now", str(False))

        # # # Enable and control signals
        # # hal.set_p("grinder.enable_x", str(False))
        # # hal.set_p("grinder.enable_y", str(False))
        # # hal.set_p("grinder.enable_z", str(False))
        # # hal.set_p("grinder.stop_at_z_limit", str(False))

        # # # Crossfeed and repeat settings
        # # hal.set_p("grinder.crossfeed_at", str(0))
        # # hal.set_p("grinder.repeat_at", str(0))

        # hal.set_p("grinder.is_running", str(False))

        # print(hal.get_value("grinder.x_max"))
        # print("Created pins")

    def load_settings():
        if os.path.exists(settings_file):
            with open(settings_file, "rb") as file:
                settings = pickle.load(file)
                print(settings)
                print("Grinder settings loaded")
        else:
            settings = {}
            print("Empty settings loaded")
        
        previous_linear_units = settings.get('previous_linear_units',1)
        GrinderHal.set_hal("x_min", settings.get('x_min',0))
        GrinderHal.set_hal("x_max", settings.get('x_max', GrinderHal.get_converted_value(1, "inch")))
        GrinderHal.set_hal("y_min", settings.get('y_min',0))
        GrinderHal.set_hal("y_max", settings.get('y_max', GrinderHal.get_converted_value(1, "inch")))
        GrinderHal.set_hal("z_min",  settings.get('z_min',0))
        GrinderHal.set_hal("z_max",  settings.get('z_max', GrinderHal.get_converted_value(1, "inch")))
        

        GrinderHal.set_hal("x_speed",  settings.get('x_speed', GrinderHal.get_converted_value(500, "inch")))
        # print("X_SPEED:")
        # print(GrinderHal.get_hal("x_speed"))
        # print(GrinderHal.get_converted_value(500, "inch"))
        GrinderHal.set_hal("y_speed",  settings.get('y_speed', GrinderHal.get_converted_value(200, "inch")))
        GrinderHal.set_hal("z_speed",  settings.get('z_speed', GrinderHal.get_converted_value(200, "inch")))
        

        GrinderHal.set_hal("z_crossfeed",  settings.get('z_crossfeed', GrinderHal.get_converted_value(0.005, "inch")))        
        GrinderHal.set_hal("y_downfeed",  settings.get('y_downfeed', GrinderHal.get_converted_value(0.0005, "inch")))
        
        GrinderHal.set_hal("enable_x",  settings.get('enable_x', bool(False)))
        GrinderHal.set_hal("enable_y",  settings.get('enable_y', bool(False)))
        GrinderHal.set_hal("enable_z",  settings.get('enable_z', bool(False)))

        GrinderHal.set_hal("stop_at_z_limit",  settings.get('stop_at_z_limit', 0))

        GrinderHal.set_hal("crossfeed_at",  settings.get('crossfeed_at', 2))
        GrinderHal.set_hal("repeat_at",  settings.get('repeat_at', 1))

        ############## DRESS PARAMS ################

        GrinderHal.set_hal("dress_start_x", settings.get('dress_start_x', 0.0))
        GrinderHal.set_hal("dress_start_y", settings.get('dress_start_y', 0.0))
        GrinderHal.set_hal("dress_start_z", settings.get('dress_start_z', 0.0))
        GrinderHal.set_hal("dress_end_x", settings.get('dress_end_x', 0.0))
        GrinderHal.set_hal("dress_end_y", settings.get('dress_end_y', 0.0))
        GrinderHal.set_hal("dress_end_z", settings.get('dress_end_z', 0.0))
        GrinderHal.set_hal("dress_stepover_x", settings.get('dress_stepover_x', 0.0))
        GrinderHal.set_hal("dress_stepover_y", settings.get('dress_stepover_y', 0.0))
        GrinderHal.set_hal("dress_stepover_z", settings.get('dress_stepover_z', 0.0))
        GrinderHal.set_hal("dress_wheel_rpm", settings.get('dress_wheel_rpm', 0.0))
        GrinderHal.set_hal("dress_wheel_dia", settings.get('dress_wheel_dia', 0.0))
        GrinderHal.set_hal("dress_point_dia", settings.get('dress_point_dia', 0.0))
        GrinderHal.set_hal("dress_overlap_ratio", settings.get('dress_overlap_ratio', 0.0))
        GrinderHal.set_hal("dress_safe_y", settings.get('dress_safe_y', 0.0))
        GrinderHal.set_hal("dress_offset_gcode", settings.get('dress_offset_gcode', "G92 Y0"))
        

        print(settings.get('x_min',0))
        print(GrinderHal.get_hal("x_min"))
        print(GrinderHal.get_hal("x_max"))
        print(hal.get_value("grinder.x_max"))
        print(settings.get("x_max"))

        print("Settings finished loading")

        

    def save_settings():

        print(GrinderHal.get_hal("x_min"))
        print(GrinderHal.get_hal("x_max"))
        # try:
        settings = {
            'previous_linear_units': previous_linear_units,
            'x_min': float(GrinderHal.get_hal("x_min")),
            'x_max': float(GrinderHal.get_hal("x_max")),
            'y_min': float(GrinderHal.get_hal("y_min")),
            'y_max': float(GrinderHal.get_hal("y_max")),
            'z_min': float(GrinderHal.get_hal("z_min")),
            'z_max': float(GrinderHal.get_hal("z_max")),
            'x_speed': float(GrinderHal.get_hal("x_speed")),
            'y_speed': float(GrinderHal.get_hal("y_speed")),
            'z_speed': float(GrinderHal.get_hal("z_speed")),
            'enable_x': bool(GrinderHal.get_hal("enable_x")),
            'enable_y': bool(GrinderHal.get_hal("enable_y")),
            'enable_z': bool(GrinderHal.get_hal("enable_z")),
            'z_crossfeed': float(GrinderHal.get_hal("z_crossfeed")),
            'y_downfeed': float(GrinderHal.get_hal("y_downfeed")),
            'stop_at_z_limit': bool(GrinderHal.get_hal("stop_at_z_limit")),
            'crossfeed_at': int(GrinderHal.get_hal("crossfeed_at")),
            'repeat_at': int(GrinderHal.get_hal("repeat_at")),
            'dress_start_x': float(GrinderHal.get_hal("dress_start_x")),
            'dress_start_y': float(GrinderHal.get_hal("dress_start_y")),
            'dress_start_z': float(GrinderHal.get_hal("dress_start_z")),
            'dress_end_x': float(GrinderHal.get_hal("dress_end_x")),
            'dress_end_y': float(GrinderHal.get_hal("dress_end_y")),
            'dress_end_z': float(GrinderHal.get_hal("dress_end_z")),
            'dress_stepover_x': float(GrinderHal.get_hal("dress_stepover_x")),
            'dress_stepover_y': float(GrinderHal.get_hal("dress_stepover_y")),
            'dress_stepover_z': float(GrinderHal.get_hal("dress_stepover_z")),
            'dress_wheel_rpm': float(GrinderHal.get_hal("dress_wheel_rpm")),
            'dress_wheel_dia': float(GrinderHal.get_hal("dress_wheel_dia")),
            'dress_point_dia': float(GrinderHal.get_hal("dress_point_dia")),
            'dress_overlap_ratio': float(GrinderHal.get_hal("dress_overlap_ratio")),
            'dress_safe_y': float(GrinderHal.get_hal("dress_safe_y")),
            'dress_offset_gcode': GrinderHal.get_hal("dress_offset_gcode")
        }

        with open(settings_file, "wb") as file:
            pickle.dump(settings, file)

        print("Settings saved")
        # except Exception:
        #     #todo set a notification
        #     print(f"")
        #     load_settings()

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

        # hal.set_p("grinder.z_direction",str(1))

        # # hal.set_p("grinder.x_min", str(0.0))
        # # hal.set_p("grinder.x_max", str(0.0))
        # # hal.set_p("grinder.y_min", str(0.0))
        # # hal.set_p("grinder.y_max", str(0.0))
        # # hal.set_p("grinder.z_min", str(0.0))
        # # hal.set_p("grinder.z_max", str(0.0))

        # # hal.set_p("grinder.x_speed", str(0.0))
        # # hal.set_p("grinder.y_speed", str(0.0))
        # # hal.set_p("grinder.z_speed", str(0.0))

        # # hal.set_p("grinder.z_crossfeed", str(0.0))
        # # hal.set_p("grinder.y_downfeed", str(0.0))
        # # hal.set_p("grinder.downfeed_now", str(False))

        # # # Enable and control signals
        # # hal.set_p("grinder.enable_x", str(False))
        # # hal.set_p("grinder.enable_y", str(False))
        # # hal.set_p("grinder.enable_z", str(False))
        # # hal.set_p("grinder.stop_at_z_limit", str(False))

        # # # Crossfeed and repeat settings
        # # hal.set_p("grinder.crossfeed_at", str(0))
        # # hal.set_p("grinder.repeat_at", str(0))

        # hal.set_p("grinder.is_running", str(False))

        # print(hal.get_value("grinder.x_max"))
        # print("Created pins")

    def load_settings():
        if os.path.exists(settings_file):
            with open(settings_file, "rb") as file:
                settings = pickle.load(file)
                print(settings)
                print("Grinder settings loaded")
        else:
            settings = {}
            print("Empty settings loaded")
        
        previous_linear_units = settings.get('previous_linear_units',1)
        GrinderHal.set_hal("x_min", settings.get('x_min',0))
        GrinderHal.set_hal("x_max", settings.get('x_max', GrinderHal.get_converted_value(1, "inch")))
        GrinderHal.set_hal("y_min", settings.get('y_min',0))
        GrinderHal.set_hal("y_max", settings.get('y_max', GrinderHal.get_converted_value(1, "inch")))
        GrinderHal.set_hal("z_min",  settings.get('z_min',0))
        GrinderHal.set_hal("z_max",  settings.get('z_max', GrinderHal.get_converted_value(1, "inch")))
        

        GrinderHal.set_hal("x_speed",  settings.get('x_speed', GrinderHal.get_converted_value(500, "inch")))
        # print("X_SPEED:")
        # print(GrinderHal.get_hal("x_speed"))
        # print(GrinderHal.get_converted_value(500, "inch"))
        GrinderHal.set_hal("y_speed",  settings.get('y_speed', GrinderHal.get_converted_value(200, "inch")))
        GrinderHal.set_hal("z_speed",  settings.get('z_speed', GrinderHal.get_converted_value(200, "inch")))
        

        GrinderHal.set_hal("z_crossfeed",  settings.get('z_crossfeed', GrinderHal.get_converted_value(0.005, "inch")))        
        GrinderHal.set_hal("y_downfeed",  settings.get('y_downfeed', GrinderHal.get_converted_value(0.0005, "inch")))
        
        GrinderHal.set_hal("enable_x",  settings.get('enable_x', bool(False)))
        GrinderHal.set_hal("enable_y",  settings.get('enable_y', bool(False)))
        GrinderHal.set_hal("enable_z",  settings.get('enable_z', bool(False)))

        GrinderHal.set_hal("stop_at_z_limit",  settings.get('stop_at_z_limit', 0))

        GrinderHal.set_hal("crossfeed_at",  settings.get('crossfeed_at', 2))
        GrinderHal.set_hal("repeat_at",  settings.get('repeat_at', 1))

        ############## DRESS PARAMS ################

        GrinderHal.set_hal("dress_start_x", settings.get('dress_start_x', 0.0))
        GrinderHal.set_hal("dress_start_y", settings.get('dress_start_y', 0.0))
        GrinderHal.set_hal("dress_start_z", settings.get('dress_start_z', 0.0))
        GrinderHal.set_hal("dress_end_x", settings.get('dress_end_x', 0.0))
        GrinderHal.set_hal("dress_end_y", settings.get('dress_end_y', 0.0))
        GrinderHal.set_hal("dress_end_z", settings.get('dress_end_z', 0.0))
        GrinderHal.set_hal("dress_stepover_x", settings.get('dress_stepover_x', 0.0))
        GrinderHal.set_hal("dress_stepover_y", settings.get('dress_stepover_y', 0.0))
        GrinderHal.set_hal("dress_stepover_z", settings.get('dress_stepover_z', 0.0))
        GrinderHal.set_hal("dress_wheel_rpm", settings.get('dress_wheel_rpm', 0.0))
        GrinderHal.set_hal("dress_wheel_dia", settings.get('dress_wheel_dia', 0.0))
        GrinderHal.set_hal("dress_point_dia", settings.get('dress_point_dia', 0.0))
        GrinderHal.set_hal("dress_overlap_ratio", settings.get('dress_overlap_ratio', 0.0))
        GrinderHal.set_hal("dress_safe_y", settings.get('dress_safe_y', 0.0))
        GrinderHal.set_hal("dress_offset_gcode", settings.get('dress_offset_gcode', "G92 Y0"))
        

        print(settings.get('x_min',0))
        print(GrinderHal.get_hal("x_min"))
        print(GrinderHal.get_hal("x_max"))
        print(hal.get_value("grinder.x_max"))
        print(settings.get("x_max"))

        print("Settings finished loading")

        

    def save_settings():

        print(GrinderHal.get_hal("x_min"))
        print(GrinderHal.get_hal("x_max"))
        # try:
        settings = {
            'previous_linear_units': previous_linear_units,
            'x_min': float(GrinderHal.get_hal("x_min")),
            'x_max': float(GrinderHal.get_hal("x_max")),
            'y_min': float(GrinderHal.get_hal("y_min")),
            'y_max': float(GrinderHal.get_hal("y_max")),
            'z_min': float(GrinderHal.get_hal("z_min")),
            'z_max': float(GrinderHal.get_hal("z_max")),
            'x_speed': float(GrinderHal.get_hal("x_speed")),
            'y_speed': float(GrinderHal.get_hal("y_speed")),
            'z_speed': float(GrinderHal.get_hal("z_speed")),
            'enable_x': bool(GrinderHal.get_hal("enable_x")),
            'enable_y': bool(GrinderHal.get_hal("enable_y")),
            'enable_z': bool(GrinderHal.get_hal("enable_z")),
            'z_crossfeed': float(GrinderHal.get_hal("z_crossfeed")),
            'y_downfeed': float(GrinderHal.get_hal("y_downfeed")),
            'stop_at_z_limit': bool(GrinderHal.get_hal("stop_at_z_limit")),
            'crossfeed_at': int(GrinderHal.get_hal("crossfeed_at")),
            'repeat_at': int(GrinderHal.get_hal("repeat_at")),
            'dress_start_x': float(GrinderHal.get_hal("dress_start_x")),
            'dress_start_y': float(GrinderHal.get_hal("dress_start_y")),
            'dress_start_z': float(GrinderHal.get_hal("dress_start_z")),
            'dress_end_x': float(GrinderHal.get_hal("dress_end_x")),
            'dress_end_y': float(GrinderHal.get_hal("dress_end_y")),
            'dress_end_z': float(GrinderHal.get_hal("dress_end_z")),
            'dress_stepover_x': float(GrinderHal.get_hal("dress_stepover_x")),
            'dress_stepover_y': float(GrinderHal.get_hal("dress_stepover_y")),
            'dress_stepover_z': float(GrinderHal.get_hal("dress_stepover_z")),
            'dress_wheel_rpm': float(GrinderHal.get_hal("dress_wheel_rpm")),
            'dress_wheel_dia': float(GrinderHal.get_hal("dress_wheel_dia")),
            'dress_point_dia': float(GrinderHal.get_hal("dress_point_dia")),
            'dress_overlap_ratio': float(GrinderHal.get_hal("dress_overlap_ratio")),
            'dress_safe_y': float(GrinderHal.get_hal("dress_safe_y")),
            'dress_offset_gcode': GrinderHal.get_hal("dress_offset_gcode")
        }

        with open(settings_file, "wb") as file:
            pickle.dump(settings, file)

        print("Settings saved")
        # except Exception:
        #     #todo set a notification
        #     print(f"")
        #     load_settings()

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

        # hal.set_p("grinder.z_direction",str(1))

        # # hal.set_p("grinder.x_min", str(0.0))
        # # hal.set_p("grinder.x_max", str(0.0))
        # # hal.set_p("grinder.y_min", str(0.0))
        # # hal.set_p("grinder.y_max", str(0.0))
        # # hal.set_p("grinder.z_min", str(0.0))
        # # hal.set_p("grinder.z_max", str(0.0))

        # # hal.set_p("grinder.x_speed", str(0.0))
        # # hal.set_p("grinder.y_speed", str(0.0))
        # # hal.set_p("grinder.z_speed", str(0.0))

        # # hal.set_p("grinder.z_crossfeed", str(0.0))
        # # hal.set_p("grinder.y_downfeed", str(0.0))
        # # hal.set_p("grinder.downfeed_now", str(False))

        # # # Enable and control signals
        # # hal.set_p("grinder.enable_x", str(False))
        # # hal.set_p("grinder.enable_y", str(False))
        # # hal.set_p("grinder.enable_z", str(False))
        # # hal.set_p("grinder.stop_at_z_limit", str(False))

        # # # Crossfeed and repeat settings
        # # hal.set_p("grinder.crossfeed_at", str(0))
        # # hal.set_p("grinder.repeat_at", str(0))

        # hal.set_p("grinder.is_running", str(False))

        # print(hal.get_value("grinder.x_max"))
        # print("Created pins")

    def load_settings():
        if os.path.exists(settings_file):
            with open(settings_file, "rb") as file:
                settings = pickle.load(file)
                print(settings)
                print("Grinder settings loaded")
        else:
            settings = {}
            print("Empty settings loaded")
        
        previous_linear_units = settings.get('previous_linear_units',1)
        GrinderHal.set_hal("x_min", settings.get('x_min',0))
        GrinderHal.set_hal("x_max", settings.get('x_max', GrinderHal.get_converted_value(1, "inch")))
        GrinderHal.set_hal("y_min", settings.get('y_min',0))
        GrinderHal.set_hal("y_max", settings.get('y_max', GrinderHal.get_converted_value(1, "inch")))
        GrinderHal.set_hal("z_min",  settings.get('z_min',0))
        GrinderHal.set_hal("z_max",  settings.get('z_max', GrinderHal.get_converted_value(1, "inch")))
        

        GrinderHal.set_hal("x_speed",  settings.get('x_speed', GrinderHal.get_converted_value(500, "inch")))
        # print("X_SPEED:")
        # print(GrinderHal.get_hal("x_speed"))
        # print(GrinderHal.get_converted_value(500, "inch"))
        GrinderHal.set_hal("y_speed",  settings.get('y_speed', GrinderHal.get_converted_value(200, "inch")))
        GrinderHal.set_hal("z_speed",  settings.get('z_speed', GrinderHal.get_converted_value(200, "inch")))
        

        GrinderHal.set_hal("z_crossfeed",  settings.get('z_crossfeed', GrinderHal.get_converted_value(0.005, "inch")))        
        GrinderHal.set_hal("y_downfeed",  settings.get('y_downfeed', GrinderHal.get_converted_value(0.0005, "inch")))
        
        GrinderHal.set_hal("enable_x",  settings.get('enable_x', bool(False)))
        GrinderHal.set_hal("enable_y",  settings.get('enable_y', bool(False)))
        GrinderHal.set_hal("enable_z",  settings.get('enable_z', bool(False)))

        GrinderHal.set_hal("stop_at_z_limit",  settings.get('stop_at_z_limit', 0))

        GrinderHal.set_hal("crossfeed_at",  settings.get('crossfeed_at', 2))
        GrinderHal.set_hal("repeat_at",  settings.get('repeat_at', 1))

        ############## DRESS PARAMS ################

        GrinderHal.set_hal("dress_start_x", settings.get('dress_start_x', 0.0))
        GrinderHal.set_hal("dress_start_y", settings.get('dress_start_y', 0.0))
        GrinderHal.set_hal("dress_start_z", settings.get('dress_start_z', 0.0))
        GrinderHal.set_hal("dress_end_x", settings.get('dress_end_x', 0.0))
        GrinderHal.set_hal("dress_end_y", settings.get('dress_end_y', 0.0))
        GrinderHal.set_hal("dress_end_z", settings.get('dress_end_z', 0.0))
        GrinderHal.set_hal("dress_stepover_x", settings.get('dress_stepover_x', 0.0))
        GrinderHal.set_hal("dress_stepover_y", settings.get('dress_stepover_y', 0.0))
        GrinderHal.set_hal("dress_stepover_z", settings.get('dress_stepover_z', 0.0))
        GrinderHal.set_hal("dress_wheel_rpm", settings.get('dress_wheel_rpm', 0.0))
        GrinderHal.set_hal("dress_wheel_dia", settings.get('dress_wheel_dia', 0.0))
        GrinderHal.set_hal("dress_point_dia", settings.get('dress_point_dia', 0.0))
        GrinderHal.set_hal("dress_overlap_ratio", settings.get('dress_overlap_ratio', 0.0))
        GrinderHal.set_hal("dress_safe_y", settings.get('dress_safe_y', 0.0))
        GrinderHal.set_hal("dress_offset_gcode", settings.get('dress_offset_gcode', "G92 Y0"))
        

        print(settings.get('x_min',0))
        print(GrinderHal.get_hal("x_min"))
        print(GrinderHal.get_hal("x_max"))
        print(hal.get_value("grinder.x_max"))
        print(settings.get("x_max"))

        print("Settings finished loading")

        

    def save_settings():

        print(GrinderHal.get_hal("x_min"))
        print(GrinderHal.get_hal("x_max"))
        # try:
        settings = {
            'previous_linear_units': previous_linear_units,
            'x_min': float(GrinderHal.get_hal("x_min")),
            'x_max': float(GrinderHal.get_hal("x_max")),
            'y_min': float(GrinderHal.get_hal("y_min")),
            'y_max': float(GrinderHal.get_hal("y_max")),
            'z_min': float(GrinderHal.get_hal("z_min")),
            'z_max': float(GrinderHal.get_hal("z_max")),
            'x_speed': float(GrinderHal.get_hal("x_speed")),
            'y_speed': float(GrinderHal.get_hal("y_speed")),
            'z_speed': float(GrinderHal.get_hal("z_speed")),
            'enable_x': bool(GrinderHal.get_hal("enable_x")),
            'enable_y': bool(GrinderHal.get_hal("enable_y")),
            'enable_z': bool(GrinderHal.get_hal("enable_z")),
            'z_crossfeed': float(GrinderHal.get_hal("z_crossfeed")),
            'y_downfeed': float(GrinderHal.get_hal("y_downfeed")),
            'stop_at_z_limit': bool(GrinderHal.get_hal("stop_at_z_limit")),
            'crossfeed_at': int(GrinderHal.get_hal("crossfeed_at")),
            'repeat_at': int(GrinderHal.get_hal("repeat_at")),
            'dress_start_x': float(GrinderHal.get_hal("dress_start_x")),
            'dress_start_y': float(GrinderHal.get_hal("dress_start_y")),
            'dress_start_z': float(GrinderHal.get_hal("dress_start_z")),
            'dress_end_x': float(GrinderHal.get_hal("dress_end_x")),
            'dress_end_y': float(GrinderHal.get_hal("dress_end_y")),
            'dress_end_z': float(GrinderHal.get_hal("dress_end_z")),
            'dress_stepover_x': float(GrinderHal.get_hal("dress_stepover_x")),
            'dress_stepover_y': float(GrinderHal.get_hal("dress_stepover_y")),
            'dress_stepover_z': float(GrinderHal.get_hal("dress_stepover_z")),
            'dress_wheel_rpm': float(GrinderHal.get_hal("dress_wheel_rpm")),
            'dress_wheel_dia': float(GrinderHal.get_hal("dress_wheel_dia")),
            'dress_point_dia': float(GrinderHal.get_hal("dress_point_dia")),
            'dress_overlap_ratio': float(GrinderHal.get_hal("dress_overlap_ratio")),
            'dress_safe_y': float(GrinderHal.get_hal("dress_safe_y")),
            'dress_offset_gcode': GrinderHal.get_hal("dress_offset_gcode")
        }

        with open(settings_file, "wb") as file:
            pickle.dump(settings, file)

        print("Settings saved")
        # except Exception:
        #     #todo set a notification
        #     print(f"")
        #     load_settings()

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