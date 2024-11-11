from qtpyvcp.widgets.form_widgets.main_window import VCPMainWindow
from qtpy.QtWidgets import QLineEdit, QPushButton, QComboBox, QDoubleSpinBox, QSpinBox, QCheckBox
from qtpy.QtGui import QDoubleValidator
import linuxcnc
import hal
import numpy as np
from qtpy.QtCore import QTimer, QEventLoop, Qt
from qtpyvcp.plugins import getPlugin
from enum import Enum

# Setup Help Text
import grinder_touch.helptext as helptext

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

# Setup logging
from qtpyvcp.utilities import logger

LOG = logger.getLogger('qtpyvcp.' + __name__)

class GrinderWindow(VCPMainWindow):
    """Main window class for the VCP."""
    def __init__(self, *args, **kwargs):
        super(GrinderWindow, self).__init__(*args, **kwargs)

        self.setFixedSize(1024, 600)
        
        self.settings = getPlugin('persistent_data_manager')

        self.position_rounding_tolerance_in = 5
        self.position_rounding_tolerance_mm = 3

        # Initialize LinuxCNC command, status, and HAL component
        self.c = linuxcnc.command()
        self.s = linuxcnc.stat()
        self.h = hal.HAL()


    def get_rounding_tolerance(self):
        # Check the current units
        if self.s.linear_units == 1.0:
            return self.position_rounding_tolerance_mm
        elif self.s.linear_units == 25.4:
            return self.position_rounding_tolerance_in
        else:
            raise Exception("Unknown work coordinate system units")
        
    def get_converted_value(self, value, units):
        if units != "inch" and units != "mm":
            raise Exception("Get converted value called with invalid unit type")
        
        if units == "inch":
            if self.s.linear_units == 1.0:
                return value*25.4
            elif self.s.linear_units == 25.4:
                return value
            
        elif units == "mm":
            if self.s.linear_units == 1.0:
                return value
            elif self.s.linear_units == 25.4:
                return value/25.4


    def get_pos(self, axis):

        self.s.poll()
        return round(self.s.actual_position[axis.to_int()], self.get_rounding_tolerance())

    def initialize_controls(self):
        """Initialize custom controls and connect UI elements."""

        self.x_max_edit = self.findChild(QPushButton, "x_max_edit")
        self.x_min_edit = self.findChild(QPushButton, "x_min_edit")
        self.z_max_edit = self.findChild(QPushButton, "z_max_edit")
        self.z_min_edit = self.findChild(QPushButton, "z_min_edit")
        self.y_max_edit = self.findChild(QPushButton, "y_max_edit")
        self.y_min_edit = self.findChild(QPushButton, "y_min_edit")

        self.x_max_here_pb = self.findChild(QPushButton, "x_max_here_pb")
        self.x_max_here_pb.clicked.connect(self.on_set_limit_clicked)
        self.x_min_here_pb = self.findChild(QPushButton, "x_min_here_pb")
        self.x_max_here_pb.clicked.connect(self.on_set_limit_clicked)
        self.z_max_here_pb = self.findChild(QPushButton, "z_max_here_pb")
        self.x_max_here_pb.clicked.connect(self.on_set_limit_clicked)
        self.z_min_here_pb = self.findChild(QPushButton, "z_min_here_pb")
        self.x_max_here_pb.clicked.connect(self.on_set_limit_clicked)
        self.y_max_here_pb = self.findChild(QPushButton, "y_max_here_pb")
        self.x_max_here_pb.clicked.connect(self.on_set_limit_clicked)
        self.y_min_here_pb = self.findChild(QPushButton, "y_min_here_pb")
        self.x_max_here_pb.clicked.connect(self.on_set_limit_clicked)

        self.x_speed_sb = self.findChild(QPushButton, "x_speed_sb")
        self.z_speed_sb = self.findChild(QPushButton, "z_speed_sb")
        self.y_speed_sb = self.findChild(QPushButton, "y_speed_sb")

        self.crossfeed_stepover_edit = self.findChild(QPushButton, "crossfeed_stepover_edit")
        self.downfeed_depth_edit = self.findChild(QPushButton, "downfeed_depth_edit")

        self.crossfeed_at_cb = self.findChild(QPushButton, "crossfeed_at_cb")
        self.repeat_at_cb = self.findChild(QPushButton, "repeat_at_cb")

        self.stop_x_at_z_limit_pb = self.findChild(QPushButton, "stop_x_at_z_limit_pb")
        self.stop_x_at_z_limit_pb.clicked.connect(lambda: self.on_toggle_clicked(self.stop_x_at_z_limit_pb, "stop_x_at_z_limit"))
        self.stop_z_at_z_limit_pb = self.findChild(QPushButton, "stop_z_at_z_limit_pb")
        self.stop_z_at_z_limit_pb.clicked.connect(lambda: self.on_toggle_clicked(self.stop_z_at_z_limit_pb, "stop_z_at_z_limit_pb"))

        self.save_grind_pb = self.findChild(QPushButton, "save_grind_pb")
        self.save_grind_pb.clicked.connect(self.save_grind_clicked)

        # Run/Stop Button
        self.run_stop_pb = self.findChild(QPushButton, "run_stop_pb")
        self.run_stop_pb.clicked.connect(lambda: self.on_toggle_clicked(self.run_stop_pb, "run_stop"))

        self.enable_x_pb = self.findChild(QPushButton, "enable_x_pb")
        self.enable_x_pb.clicked.connect(lambda: self.on_toggle_clicked(self.enable_x_pb, "enable_x"))
        self.enable_y_pb = self.findChild(QPushButton, "enable_y_pb")
        self.enable_y_pb.clicked.connect(lambda: self.on_toggle_clicked(self.enable_y_pb, "enable_y"))
        self.enable_z_pb = self.findChild(QPushButton, "enable_z_pb")
        self.enable_z_pb.clicked.connect(lambda: self.on_toggle_clicked(self.enable_z_pb, "enable_z"))
        

    def load_settings(self):
        """Load user settings using PersistentSettings."""
        self.h["x_min"] = self.settings.get_data('grinder_x_min',0)
        self.x_min_edit.setText(str(self.h["x_min"]))
        self.h["x_max"] = self.settings.getData('grinder_x_max', self.get_converted_value(1, "inch"))
        self.x_max_edit.setText(str(self.h["x_max"]))
        self.h["y_min"] = self.settings.get_data('grinder_y_min',0)
        self.y_minn_edit.setText(str(self.h["y_min"]))
        self.h["y_max"] = self.settings.getData('grinder_y_max', self.get_converted_value(1, "inch"))
        self.y_max_edit.setText(str(self.h["y_max"]))
        self.h["z_min"] = self.settings.get_data('grinder_z_min',0)
        self.z_min_edit.setText(str(self.h["z_min"]))
        self.h["z_max"] = self.settings.getData('grinder_z_max', self.get_converted_value(1, "inch"))
        self.z_max_edit.setText(str(self.h["z_max"]))

        self.h["x_speed"] = self.settings.getData('grinder_x_speed', self.get_converted_value(500, "inch"))
        self.x_speed_sb.setValue(float(self.h["x_speed"]))
        self.h["y_speed"] = self.settings.getData('grinder_y_speed', self.get_converted_value(200, "inch"))
        self.y_speed_sb.setValue(float(self.h["y_speed"]))
        self.h["z_speed"] = self.settings.getData('grinder_z_speed', self.get_converted_value(200, "inch"))
        self.z_speed_sb.setValue(float(self.h["z_speed"]))

        self.h["z_crossfeed"] = self.settings.getData('grinder_z_crossfeed', self.get_converted_value(0.005, "inch"))
        self.z_crossfeed_edit.setText(str(self.h["z_crossfeed"]))
        self.h["y_downfeed"] = self.settings.getData('grinder_y_downfeed', self.get_converted_value(0.0005, "inch"))
        self.y_downfeed_edit.setText(str(self.h["y_downfeed"]))

        self.h["enable_x"] = False
        self.h["enable_y"] = False
        self.h["enable_z"] = False

        self.h["stop_x_at_z_limit"] = self.settings.getData('grinder_stop_x_at_z_limit', 0)
        self.stop_x_at_z_limit_pb.setChecked(bool(self.h["stop_x_at_z_limit"]))
        self.h["stop_z_at_z_limit"] = self.settings.getData('grinder_stop_z_at_z_limit', 0)
        self.stop_x_at_z_limit_pb.setChecked(bool(self.h["stop_z_at_z_limit"]))

        self.h["crossfeed_at"] = self.settings.getData('grinder_crossfeed_at', 0)
        self.crossfeed_at_cb.setCurrentIndex(int(self.h["crossfeed_at"]))
        self.h["repeat_at"] = self.settings.getData('grinder_repeat_at', 0)
        self.repeat_at_cb.setCurrentIndex(int(self.h["repeat_at"]))

    def validate_and_save(self, field_name, value, value_type):
        if value_type == "float":
            try:
                self.h[field_name] = float(value)
                self.settings.setData("grinder_"+field_name, value)
            except ValueError:
                raise Exception(F"{field_name} must be numeric")
            
        if value_type == "int":
            try:
                self.h[field_name] = int(value)
                self.settings.setData("grinder_"+field_name, value)
            except ValueError:
                raise Exception(F"{field_name} must be an integer")
            
        if value_type == "bool":
            try:
                self.h[field_name] = bool(value)
                self.settings.setData("grinder_"field_name, value)
            except ValueError:
                raise Exception(F"{field_name} must be a boolean")

    def on_set_limit_clicked(self):
        sender = self.sender()
        if sender:
            full_name = sender.objectName()
            base_name = full_name.removesuffix("_here_pb")  # Removes the '_pb' suffix
            axis_name = base_name.removesuffix("_min")
            axis_name = base_name.removesuffix("_max")
            self.s.poll()
            self.h[base_name] = self.s.actual_position[Axis.from_str(axis_name).to_int()]
        else:
            raise Exception("unknown sender")
        
    def on_toggle_clicked(self, button, hal_field):
        self.h[hal_field] = -self.h[hal_field]
        button.setChecked(self.h[hal_field])

        self.set_toggle_button_color(button,"hal_field)

    def set_toggle_button_color(self, button, hal_field):
        if self.h[hal_field]:
            button.setStylesheet("background-color: red")
        else:
            if self.h[hal_field]:
                button.setStylesheet("background-color: green")

    def save_grind_clicked(self):
        """Stop movement, wait for idle, then save the traverse limits and 3D stepover values."""

        try:
            self.validate_and_save("x_min", self.x_min_edit.text(),"float")
            self.h["x_min"] = self.x_min_edit.text()
            self.validate_and_save("x_max", self.x_max_edit.text(),"float")
            self.h["x_max"] = self.x_max_edit.text()
            self.validate_and_save("y_min", self.y_min_edit.text(),"float")
            self.h["y_min"] = self.y_min_edit.text()
            self.validate_and_save("y_max", self.y_max_edit.text(),"float")
            self.h["y_max"] = self.y_max_edit.text()
            self.validate_and_save("x_min", self.x_min_edit.text(),"float")
            self.h["z_min"] = self.z_min_edit.text()
            self.validate_and_save("x_max", self.x_max_edit.text(),"float")
            self.h["z_max"] = self.z_max_edit.text()

            self.validate_and_save("x_speed", self.x_speed_sb.text(),"float")
            self.h["x_speed"] = self.x_speed_edit.text()
            self.validate_and_save("y_speed", self.y_speed_sb.text(),"float")
            self.h["y_speed"] = self.y_speed_edit.text()
            self.validate_and_save("z_speed", self.z_speed_sb.text(),"float")
            self.h["z_speed"] = self.z_speed_edit.text()

            self.validate_and_save("z_crossfeed", self.z_crossfeed_edit.text(),"float")
            self.h["z_crossfeed"] = self.z_crossfeed_edit.text()
            self.validate_and_save("y_downfeed", self.z_crossfeed_edit.text(),"float")
            self.h["y_downfeed"] = self.y_downfeed_edit.text()

            self.validate_and_save("stop_x_at_z_limit", self.stop_x_at_z_limit_pb.isChecked(),"bool")
            self.h["stop_x_at_z_limit"] = self.stop_x_at_z_limit_pb.isChecked()
            self.validate_and_save("stop_z_at_z_limit", self.stop_x_at_z_limit_pb.isChecked(),"bool")
            self.h["stop_z_at_z_limit"] = self.stop_x_at_z_limit_pb.isChecked()

            self.validate_and_save("crossfeed_at", self.crossfeed_at_cb.value(),"int")
            self.h["crossfeed_at"] = self.crossfeed_at_cb.value()
            self.validate_and_save("repeat_at", self.crossfeed_at_cb.value(),"int")
            self.h["repeat_at"] = self.repeat_at_cb.value()
        except Exception:
            self.stop()
            #todo set a notification
            self.load_settings()

    def stop(self):
        """Start or stop the control loop based on the run_stop signal."""
        self.c.abort()
        self.h["run_stop"] = False
        self.run_stop_button.setText("RUN")
        self.run_stop_button.setStyleSheet("")
        self.run_stop_button.setChecked(False)

    def move_to(self, axis, pos, speed):
        LOG.debug(F"Move_To: G1 {axis}{pos} F{speed}")
        self.c.mdi(F"G1 {axis}{pos} F{speed}")

    
