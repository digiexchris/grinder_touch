import linuxcnc, hal
from enum import Enum
from hal_glib import GStat
class Axis(Enum):
    X = 0
    Y = 1
    Z = 2

    @classmethod
    def from_int(cls, value):
        """Convert an integer to a corresponding enum member."""
        return cls._value2member_map_.get(value)

    @classmethod
    def from_str(cls, name):
        """Convert a string to a corresponding enum member."""
        try:
            return cls[name.upper()]
        except KeyError:
            return None

    def to_int(self):
        """Convert an enum member to its integer value."""
        return self.value

    def to_str(self):
        """Convert an enum member to its string representation."""
        return self.name

    def __str__(self):
        """Override the default string representation."""
        return self.name
    
GSTAT = GStat()

class GrinderCommon():

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