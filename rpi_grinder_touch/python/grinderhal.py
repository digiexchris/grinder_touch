import hal

from hal_glib import GStat
    
GSTAT = GStat()

class GrinderHal():

    def get_rounding_tolerance():
        # Check the current units
        if GSTAT.is_metric_mode():
            return 4
        else:
            return 5

    def set_hal(field, value):
        print("Setting hal value: "+str(value))
        hal.set_p("grinder."+field, str(value))
            
    def get_hal(field):
        return hal.get_value("grinder."+field)