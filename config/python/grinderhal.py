import hal
from hal_glib import GStat
import time
    
GSTAT = GStat()

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
        
    def save_settings():

        GrinderHal.set_hal("requires_save", True)
        print("Settings saved")

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