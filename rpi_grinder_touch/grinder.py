import os
from qtpy.QtWidgets import QLineEdit, QPushButton, QComboBox, QDoubleSpinBox, QSpinBox, QCheckBox, QWidget
from qtpy.QtGui import QDoubleValidator

import linuxcnc, hal
from qtpy.QtCore import QTimer, QEventLoop, Qt
from enum import Enum

from hal_glib import GStat
GSTAT = GStat()

# from qtpyvcp.hal import QPin

import pickle

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

def startup(parent):
    parent.setFixedSize(1024, 600)
    parent.grinder_window = GrinderWindow(parent)
    parent.grinder_window.initialize_controls(parent)
    parent.grinder_window.load_settings()
    

class GrinderWindow(QWidget):
    """Main window class for the VCP."""
    def __init__(self, parent):

        self.parent = parent
        # self = aParentWindow

        # self.setFixedSize(1024, 600)

        self.settings_file = "./grinder.pkl"

        self.position_rounding_tolerance_in = 5
        self.position_rounding_tolerance_mm = 3

        self.pos = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        GSTAT.connect("current-position", self.update_pos)

        # Initialize LinuxCNC command, status, and HAL component
        self.c = linuxcnc.command()
        self.s = linuxcnc.stat()
        self.h = hal

    def update_pos(self, obj, absolute_pos, relative_pos, dist_to_go, joint_pos):
        self.pos = relative_pos


    def get_rounding_tolerance(self):
        # Check the current units
        if GSTAT.is_metric_mode():
            return self.position_rounding_tolerance_mm
        else:
            return self.position_rounding_tolerance_in
        
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
            
    def is_on(parent):
        return parent.status.task_state == linuxcnc.STATE_ON
# if parent.status.task_state == emc.STATE_ESTOP:

    def get_pos(self, axis):

        return round(self.pos[axis.to_int()], self.get_rounding_tolerance())

    def initialize_controls(self, parent):
        """Initialize custom controls and connect UI elements."""

        # GSTAT.connect("state-estop",lambda w: self.update_estate_label('ESTOP'))

        self.x_max_edit = parent.findChild(QLineEdit, "x_max_edit")
        self.x_min_edit = parent.findChild(QLineEdit, "x_min_edit")
        self.z_max_edit = parent.findChild(QLineEdit, "z_max_edit")
        self.z_min_edit = parent.findChild(QLineEdit, "z_min_edit")
        self.y_max_edit = parent.findChild(QLineEdit, "y_max_edit")
        self.y_min_edit = parent.findChild(QLineEdit, "y_min_edit")

        self.x_max_here_pb = parent.findChild(QPushButton, "x_max_here_pb")
        self.x_max_here_pb.clicked.connect(lambda: self.on_set_limit_clicked("x_max", self.x_max_edit))
        self.x_min_here_pb = parent.findChild(QPushButton, "x_min_here_pb")
        self.x_min_here_pb.clicked.connect(lambda: self.on_set_limit_clicked("x_min", self.x_min_edit))
        self.z_max_here_pb = parent.findChild(QPushButton, "z_max_here_pb")
        self.z_max_here_pb.clicked.connect(lambda: self.on_set_limit_clicked("z_max", self.z_max_edit))
        self.z_min_here_pb = parent.findChild(QPushButton, "z_min_here_pb")
        self.z_min_here_pb.clicked.connect(lambda: self.on_set_limit_clicked("z_min", self.z_min_edit))
        self.y_max_here_pb = parent.findChild(QPushButton, "y_max_here_pb")
        self.y_max_here_pb.clicked.connect(lambda: self.on_set_limit_clicked("y_max", self.y_max_edit))
        self.y_min_here_pb = parent.findChild(QPushButton, "y_min_here_pb")
        self.y_min_here_pb.clicked.connect(lambda: self.on_set_limit_clicked("y_min", self.y_min_edit))

        self.x_speed_sb = parent.findChild(QDoubleSpinBox, "x_speed_sb")
        self.z_speed_sb = parent.findChild(QDoubleSpinBox, "z_speed_sb")
        self.y_speed_sb = parent.findChild(QDoubleSpinBox, "y_speed_sb")

        self.z_crossfeed_edit = parent.findChild(QLineEdit, "z_crossfeed_edit")
        self.y_downfeed_edit = parent.findChild(QLineEdit, "y_downfeed_edit")

        self.crossfeed_at_cb = parent.findChild(QComboBox, "crossfeed_at_cb")
        self.repeat_at_cb = parent.findChild(QComboBox, "repeat_at_cb")

        self.stop_x_at_z_limit_pb = parent.findChild(QPushButton, "stop_x_at_z_limit_pb")
        self.stop_x_at_z_limit_pb.clicked.connect(lambda: self.on_toggle_clicked(self.stop_x_at_z_limit_pb, "stop_x_at_z_limit", "OFF", "ON"))
        self.stop_z_at_z_limit_pb = parent.findChild(QPushButton, "stop_z_at_z_limit_pb")
        self.stop_z_at_z_limit_pb.clicked.connect(lambda: self.on_toggle_clicked(self.stop_z_at_z_limit_pb, "stop_z_at_z_limit", "OFF", "ON"))

        self.save_grind_pb = parent.findChild(QPushButton, "save_grind_pb")
        self.save_grind_pb.clicked.connect(self.save_grind_clicked)

        print(self.save_grind_pb)

        # Run/Stop Button
        self.run_stop_pb = parent.findChild(QPushButton, "run_stop_pb")
        self.run_stop_pb.clicked.connect(lambda: self.on_toggle_clicked(self.run_stop_pb, "run_stop", "RUN", "STOP"))

        self.enable_x_pb = parent.findChild(QPushButton, "enable_x_pb")
        self.enable_x_pb.clicked.connect(lambda: self.on_toggle_clicked(self.enable_x_pb, "enable_x"))
        self.enable_y_pb = parent.findChild(QPushButton, "enable_y_pb")
        self.enable_y_pb.clicked.connect(lambda: self.on_toggle_clicked(self.enable_y_pb, "enable_y"))
        self.enable_z_pb = parent.findChild(QPushButton, "enable_z_pb")
        self.enable_z_pb.clicked.connect(lambda: self.on_toggle_clicked(self.enable_z_pb, "enable_z"))


        #TODO do the below with gstat
        #respond to the classicladder routine toggling these buttons
        # self.hal_enable_x_pin = QPin("enable_x")
        # self.hal_enable_x_pin.value_changed.connect(lambda: self.on_hal_toggle_changed(self.enable_x_pb, "enable_x"))
        # self.hal_enable_z_pin = QPin("enable_z")
        # self.hal_enable_z_pin.value_changed.connect(lambda: self.on_hal_toggle_changed(self.enable_z_pb, "enable_z"))

        #deactivate Run if the estop triggers high
        # self.hal_estop_activated_pin = QPin("halui.estop.is-activated")
        # self.hal_enable_x_pin.value_changed.connect(self.estop_changed)

        # #convert all units if machine units changes
        # self.units_pin = QPin("halui.program.is-metric")
        # self.units_pin.value_changed.connect(self.handle_units_change)

    def handle_units_change(self):
        if self.previous_linear_units != self.s.linear_units:
            conversion_factor = 1
            if self.previous_linear_units == 1:
                conversion_factor = 25.4
                self.previous_linear_units = 25.4
            else:
                conversion_factor = 1/25.4
                self.previous_linear_units = 1

            self.x_min_edit.setText(str(self.get_hal("x_min") * conversion_factor))    
            self.x_min_edit.setText(str(self.get_hal("x_max") * conversion_factor))  
            self.x_min_edit.setText(str(self.get_hal("y_min") * conversion_factor))    
            self.x_min_edit.setText(str(self.get_hal("y_max") * conversion_factor))  
            self.x_min_edit.setText(str(self.get_hal("z_min") * conversion_factor))    
            self.x_min_edit.setText(str(self.get_hal("z_max") * conversion_factor))  
            self.x_speed_sb.setValue(float(self.get_hal("x_speed") * conversion_factor))
            self.y_speed_sb.setValue(float(self.get_hal("y_speed") * conversion_factor))
            self.z_speed_sb.setValue(float(self.get_hal("z_speed") * conversion_factor))
            self.z_crossfeed_edit.setText(str(self.get_hal("z_crossfeed") * conversion_factor))
            self.y_downfeed_edit.setText(str(self.get_hal("y_downfeed") * conversion_factor))

            self.save_grind_clicked()

    def estop_changed(self):
        if self.get_hal("halui.estop.is-activated"):
            if self.get_hal("grinder.run_stop"):
                self.stop()

    def on_hal_toggle_changed(self, button, hal_field):

        self.set_checked(button, hal_field)
        self.set_toggle_button_color(button,hal_field)

    def set_hal(self, field, value):
        print("Setting hal value: "+str(value))
        hal.set_p("grinder."+field, str(value))
        
    def get_hal(self, field):
        return hal.get_value("grinder."+field)

    def load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, "rb") as file:
                self.settings = pickle.load(file)
                print("Grinder settings loaded")
        else:
            self.settings = {}

        self.previous_linear_units = self.settings.get('previous_linear_units',1)
        self.set_hal("x_min", self.settings.get('x_min',0))
        self.x_min_edit.setText(str(self.get_hal("x_min")))
        self.set_hal("x_max", self.settings.get('x_max', self.get_converted_value(1, "inch")))
        self.x_max_edit.setText(str(self.get_hal("x_max")))
        self.set_hal("y_min", self.settings.get('y_min',0))
        self.y_min_edit.setText(str(self.get_hal("y_min")))
        self.set_hal("y_max", self.settings.get('y_max', self.get_converted_value(1, "inch")))
        self.y_max_edit.setText(str(self.get_hal("y_max")))
        self.set_hal("z_min",  self.settings.get('z_min',0))
        self.z_min_edit.setText(str(self.get_hal("z_min")))
        self.set_hal("z_max",  self.settings.get('z_max', self.get_converted_value(1, "inch")))
        self.z_max_edit.setText(str(self.get_hal("z_max")))

        self.set_hal("x_speed",  self.settings.get('x_speed', self.get_converted_value(500, "inch")))
        self.x_speed_sb.setValue(float(self.get_hal("x_speed")))
        self.set_hal("y_speed",  self.settings.get('y_speed', self.get_converted_value(200, "inch")))
        self.y_speed_sb.setValue(float(self.get_hal("y_speed")))
        self.set_hal("z_speed",  self.settings.get('z_speed', self.get_converted_value(200, "inch")))
        self.z_speed_sb.setValue(float(self.get_hal("z_speed")))

        self.set_hal("z_crossfeed",  self.settings.get('z_crossfeed', self.get_converted_value(0.005, "inch")))
        self.z_crossfeed_edit.setText(str(self.get_hal("z_crossfeed")))
        self.set_hal("y_downfeed",  self.settings.get('y_downfeed', self.get_converted_value(0.0005, "inch")))
        self.y_downfeed_edit.setText(str(self.get_hal("y_downfeed")))

        # self.set_hal("enable_x",  False)
        # self.set_hal("enable_y",  False)
        # self.set_hal("enable_z",  False)

        self.set_hal("stop_x_at_z_limit",  self.settings.get('stop_x_at_z_limit', 0))
        self.stop_x_at_z_limit_pb.setChecked(bool(self.get_hal("stop_x_at_z_limit")))
        self.set_hal("stop_z_at_z_limit",  self.settings.get('stop_z_at_z_limit', 0))
        self.stop_x_at_z_limit_pb.setChecked(bool(self.get_hal("stop_z_at_z_limit")))

        self.set_hal("crossfeed_at",  self.settings.get('crossfeed_at', 0))
        self.crossfeed_at_cb.setCurrentIndex(int(self.get_hal("crossfeed_at")))
        self.set_hal("repeat_at",  self.settings.get('repeat_at', 0))
        self.repeat_at_cb.setCurrentIndex(int(self.get_hal("repeat_at")))

    def validate_and_convert(self, field_name, value, value_type):
        if value_type == "float":
            try:
                self.set_hal(field_name,float(value))
                return float(value)
            except ValueError:
                raise Exception(F"{field_name} must be numeric")
            
        if value_type == "int":
            try:
                self.set_hal(field_name, int(value))
                return int(value)
            except ValueError:
                raise Exception(F"{field_name} must be an integer")
            
        if value_type == "bool":
            try:
                self.set_hal(field_name, bool(value))
                return int(value)
            except ValueError:
                raise Exception(F"{field_name} must be a boolean")

    def on_set_limit_clicked(self, base_name, edit):
        print("base: "+base_name)
        axis_name = base_name.removesuffix("_min")
        print("Removed Min: "+axis_name)
        axis_name = axis_name.removesuffix("_max")
        print("Removed Max: "+axis_name)
        self.s.poll()
        
        axis = Axis.from_str(axis_name)
        print("axis: "+ axis.to_str())
        print("Actual Position:" + str(self.s.position[axis.to_int()]))
        self.set_hal(base_name, self.get_pos(axis))
        edit.setText(str(self.get_hal(base_name)))

        
    def set_checked(self, button, hal_field):
        button.setChecked(bool(self.get_hal(hal_field)))
        
    def on_toggle_clicked(self, button, hal_field, off_text = "", on_text = ""):
        self.set_hal(hal_field, button.isChecked())
        # self.set_checked(button, hal_field)

        if button.isChecked():
            if on_text != "":
                button.setText(on_text)
        else:
            if off_text != "":
                button.setText(off_text)

        # self.set_toggle_button_color(button,hal_field)

    def set_toggle_button_color(self, button, hal_field):

        existing_styles = button.styleSheet()
        new_background = "background-color: red;" if bool(self.get_hal(hal_field)) else "background-color: green;"
        button.setStyleSheet(f"{existing_styles} {new_background}")

    def save_grind_clicked(self):
        """Stop movement, wait for idle, then save the traverse limits and 3D stepover values."""

        print("Saving grind settings")

        # try:
        self.settings = {
            'previous_linear_units': self.previous_linear_units,
            'x_min': self.validate_and_convert("x_min", self.x_min_edit.text(),"float"),
            'x_max': self.validate_and_save("x_max", self.x_max_edit.text(),"float"),
            'y_min': self.validate_and_save("y_min", self.y_min_edit.text(),"float"),
            'y_max': self.validate_and_save("y_max", self.y_max_edit.text(),"float"),
            'z_min': self.validate_and_save("x_min", self.x_min_edit.text(),"float"),
            'z_max': self.validate_and_save("x_max", self.x_max_edit.text(),"float"),
            'x_speed': self.validate_and_save("x_speed", self.x_speed_sb.text(),"float"),
            'y_speed': self.validate_and_save("y_speed", self.y_speed_sb.text(),"float"),
            'z_speed': self.validate_and_save("z_speed", self.z_speed_sb.text(),"float"),
            'z_crossfeed': self.validate_and_save("z_crossfeed", self.z_crossfeed_edit.text(),"float"),
            'y_downfeed': self.validate_and_save("y_downfeed", self.z_crossfeed_edit.text(),"float"),
            'stop_x_at_z_limit': self.validate_and_save("stop_x_at_z_limit", self.stop_x_at_z_limit_pb.isChecked(),"bool"),
            'stop_z_at_z_limit': self.validate_and_save("stop_z_at_z_limit", self.stop_x_at_z_limit_pb.isChecked(),"bool"),
            'crossfeed_at': self.validate_and_save("crossfeed_at", self.crossfeed_at_cb.value(),"int"),
            'repeat_at': self.validate_and_save("repeat_at", self.crossfeed_at_cb.value(),"int"),
        }

        print(self.settings)

        with open("grinder.pkl", "wb") as file:
            pickle.dump("grinder.pkl", file)

        # self.set_hal("x_min", self.x_min_edit.text())
        # self.set_hal("x_max", self.x_max_edit.text())
        # self.set_hal("y_min", self.y_min_edit.text())
        # self.set_hal("y_max", self.y_max_edit.text())
        # self.set_hal("z_min", self.z_min_edit.text())
        # self.set_hal("z_max", self.z_max_edit.text())
        # self.set_hal("x_speed", self.x_speed_edit.text())
        # self.set_hal("y_speed", self.y_speed_edit.text())
        # self.set_hal("z_speed", self.z_speed_edit.text())
        # self.set_hal("z_crossfeed", self.z_crossfeed_edit.text())
        # self.set_hal("y_downfeed", self.y_downfeed_edit.text())
        # self.set_hal("stop_x_at_z_limit", self.stop_x_at_z_limit_pb.isChecked())
        # self.set_hal("stop_z_at_z_limit", self.stop_x_at_z_limit_pb.isChecked())
        # self.set_hal("crossfeed_at", self.crossfeed_at_cb.value())
        # self.set_hal("repeat_at", self.repeat_at_cb.value())

        self.load_settings()

        # except Exception:
        #     self.stop()
        #     #todo set a notification
        #     self.load_settings()

    def stop(self):
        """Start or stop the control loop based on the run_stop signal."""
        self.c.abort()
        self.set_hal("run_stop", False)
        self.set_checked(self.run_stop_pb, "run_stop")
        self.set_toggle_button_color(self.run_stop_pb, "run_stop")


    
