from enum import Enum

class Axis(Enum):
    X = 0
    Z = 1
    Y = 2

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