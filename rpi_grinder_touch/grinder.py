import inspect
import os
from pprint import pprint
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
    parent.grinder_window.initialize_hal()
    parent.grinder_window.load_settings()
    parent.grinder_window.initialize_controls(parent)
    
    

class GrinderWindow(QWidget):
    """Main window class for the VCP."""
    def __init__(self, parent):

        super().__init__(parent)
        self.parent = parent
        # self = aParentWindow

        # self.setFixedSize(1024, 600)

        self.settings_file = "./grinder.pkl"

        self.position_rounding_tolerance_in = 5
        self.position_rounding_tolerance_mm = 4

        self.pos = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        GSTAT.connect("current-position", self.update_pos)

        self.interp_state = linuxcnc.INTERP_IDLE

        GSTAT.connect("interp-paused",self.onInterpStateChanged)
        GSTAT.connect("interp-run",self.onInterpStateChanged)
        GSTAT.connect("interp-idle",self.onInterpStateChanged)
        GSTAT.connect("state-estop-reset", self.enable_run_stop)
        GSTAT.connect("state-on", self.enable_run_stop)


        GSTAT.connect("m-code-changed", self.on_mcodes_changed)

        # Initialize LinuxCNC command, status, and HAL component
        self.c = linuxcnc.command()
        self.s = linuxcnc.stat()
        self.h = hal

    def enable_run_stop(self, value):
        if GSTAT.estop_is_clear() and GSTAT.machine_is_on():
            self.run_stop_pb.setEnabled(True)

    def on_mcodes_changed(self, value, something):
        self.set_checked(self.enable_x_pb, "enable_x")
        self.set_toggle_button_color(self.enable_x_pb,"enable_x")
        self.set_checked(self.enable_y_pb, "enable_y")
        self.set_toggle_button_color(self.enable_y_pb,"enable_y")
        self.set_checked(self.enable_y_pb, "enable_y")
        self.set_toggle_button_color(self.enable_y_pb,"enable_y")

    def update_pos(self, obj, absolute_pos, relative_pos, dist_to_go, joint_pos):
        self.pos = relative_pos

    def onInterpStateChanged(self, value):
        print("Interp State Changed:")
        pprint(value.stat.interp_state)
        self.interp_state = value.stat.interp_state

        print("self.interp_state "+str(self.interp_state))

        # print("Interp idle is value:"+ str(linuxcnc.INTERP_IDLE))

        if not GSTAT.estop_is_clear() and not GSTAT.machine_is_on():
            return

        if self.interp_state == linuxcnc.INTERP_IDLE:
            self.run_stop_pb.setChecked(0)
            self.run_stop_pb.setText("RUN")
            self.set_run_stop_style()
        else:
            self.run_stop_pb.setChecked(1)
            self.run_stop_pb.setText("STOP")
            self.set_run_stop_style()
        # self.is_paused = value
        # if self.is_paused:
        #     self.run_stop_pb.setChecked(1)
        #     self.run_stop_pb.setText("STOP")
        #     self.set_run_stop_style()

    # def onRun(self, value):
    #     print(F"Interp Mode Run Changed: ")
    #     pprint(value.stat)
    #     self.is_running = value
    #     if self.is_running:
    #         self.run_stop_pb.setChecked(1)
    #         self.run_stop_pb.setText("STOP")
    #         self.set_run_stop_style()

    # def onIdle(self, value):
    #     print(F"Interp Mode Idle Changed: ")
    #     pprint(value.stat)
    #     self.is_idle = value
    #     if self.is_idle:
    #         self.run_stop_pb.setChecked(0)
    #         self.run_stop_pb.setText("RUN")
    #         self.set_run_stop_style()

    def get_rounding_tolerance(self):
        # Check the current units
        if GSTAT.is_metric_mode():
            return self.position_rounding_tolerance_mm
        else:
            return self.position_rounding_tolerance_in
        
    def get_converted_value(self, value, units):
        if units != "inch" and units != "mm":
            raise Exception("Get converted value called with invalid unit type")
        
        if GSTAT.is_metric_mode():
            if self.s.linear_units == 1.0:
                return value
            elif self.s.linear_units == 25.4:
                return value/25.4
            
        elif units == "inch":
            if self.s.linear_units == 1.0:
                return value*25.4
            elif self.s.linear_units == 25.4:
                return value
            
        
            
    def is_on(parent):
        return parent.status.task_state == linuxcnc.STATE_ON
# if parent.status.task_state == emc.STATE_ESTOP:

    def get_pos(self, axis):

        return round(self.pos[axis.to_int()], self.get_rounding_tolerance())
    
    def on_value_changed(self, field, value, value_type):
        try:
            v = self.validate_and_set(field, value, value_type)
            self.save_grind_clicked()
        except ValueError:
            return
        
    def initialize_hal(self):
        self.h = hal.component("grinder")
        c = linuxcnc.command()

        self.previous_mode = 0

        # raise Exception("These pin stuff need to be done at the same time flexgui creates it's pins, this is too late in the process I think")
        # Define HAL pins
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
        
        self.h.ready()

        print("Grinder hal ready")

        hal.new_sig("grinder.z_direction", hal.HAL_BIT)

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
        hal.set_p("grinder.stop_z_at_z_limit", str(False))

        # Crossfeed and repeat settings
        hal.set_p("grinder.crossfeed_at", str(0))
        hal.set_p("grinder.repeat_at", str(0))

        self.previous_linear_units = 1

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

        self.stop_at_z_limit_pb = parent.findChild(QPushButton, "stop_at_z_limit_pb")
        self.stop_at_z_limit_pb.clicked.connect(lambda: self.on_toggle_clicked(self.stop_at_z_limit_pb, "stop_at_z_limit", "OFF", "ON"))

        # self.save_grind_pb = parent.findChild(QPushButton, "save_grind_pb")
        # self.save_grind_pb.clicked.connect(self.save_grind_clicked)

        # print(self.save_grind_pb)

        # Run/Stop Button
        self.run_stop_pb = parent.findChild(QPushButton, "run_stop_pb")
        self.run_stop_pb.clicked.connect(lambda: self.on_run_stop_clicked())
        self.run_stop_pb.setEnabled(False)

        self.enable_x_pb = parent.findChild(QPushButton, "enable_x_pb")
        self.enable_x_pb.clicked.connect(lambda: self.on_toggle_clicked_mcode(self.enable_x_pb, "M101 P0 Q"))
        self.set_toggle_button_color(self.enable_x_pb, "enable_x")
        self.enable_y_pb = parent.findChild(QPushButton, "enable_y_pb")
        self.enable_y_pb.clicked.connect(lambda: self.on_toggle_clicked_mcode(self.enable_y_pb, "M101 P1 Q"))
        self.set_toggle_button_color(self.enable_y_pb, "enable_y")
        self.enable_z_pb = parent.findChild(QPushButton, "enable_z_pb")
        self.enable_z_pb.clicked.connect(lambda: self.on_toggle_clicked_mcode(self.enable_z_pb, "M101 P2 Q"))
        self.set_toggle_button_color(self.enable_z_pb, "enable_z")


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

        #update visible values to match hal

        self.update_fields()

        #connect them up

        self.x_max_edit.textChanged.connect(lambda value: self.on_value_changed("x_max", value, "float"))
        self.x_min_edit.textChanged.connect(lambda value: self.on_value_changed("x_min", value, "float"))
        self.z_max_edit.textChanged.connect(lambda value: self.on_value_changed("z_max", value, "float"))
        self.z_min_edit.textChanged.connect(lambda value: self.on_value_changed("z_min", value, "float"))
        self.y_max_edit.textChanged.connect(lambda value: self.on_value_changed("y_max", value, "float"))
        self.y_min_edit.textChanged.connect(lambda value: self.on_value_changed("y_min", value, "float"))

        self.x_speed_sb.valueChanged.connect(lambda value: self.on_value_changed("x_speed", value, "float"))
        self.y_speed_sb.valueChanged.connect(lambda value: self.on_value_changed("y_speed", value, "float"))
        self.z_speed_sb.valueChanged.connect(lambda value: self.on_value_changed("z_speed", value, "float"))

        self.crossfeed_at_cb.currentIndexChanged.connect(lambda value: self.on_value_changed("crossfeed_at", value, "int"))
        self.repeat_at_cb.currentIndexChanged.connect(lambda value: self.on_value_changed("repeat_at", value, "int"))

        self.z_crossfeed_edit.textChanged.connect(lambda value: self.on_value_changed("z_crossfeed", value, "float"))
        self.y_downfeed_edit.textChanged.connect(lambda value: self.on_value_changed("y_downfeed", value, "float"))

    def set_run_stop_style(self):
        existing_styles = self.run_stop_pb.styleSheet()
        new_background = "background-color: green;" if self.run_stop_pb.isChecked() else "background-color: red;"
        self.run_stop_pb.setStyleSheet(f"{existing_styles} {new_background}")

    def on_run_stop_clicked(self):
        if self.interp_state != linuxcnc.INTERP_IDLE:
            self.stop()
        else:
            mdi_command = f"o<Flat_Grind> call"

            self.previous_mode = GSTAT.get_current_mode()
            self.c.mode(linuxcnc.MODE_MDI)
            self.c.wait_complete() # wait until mode switch executed
            self.c.mdi(mdi_command)

    def handle_units_change(self):
        if self.previous_linear_units != self.s.linear_units:
            raise Exception("This doesn't work, in progress")
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

            # self.save_grind_clicked()

    def estop_changed(self): #todo: wire this up
        if self.get_hal("halui.estop.is-activated"):
            if self.is_running or self.is_paused:
                self.stop()

    def on_hal_toggle_changed(self, button, hal_field):

        self.set_checked(button, hal_field)
        self.set_toggle_button_color(button,hal_field)

    def set_hal(self, field, value):
        print("Setting hal value: "+str(value))
        hal.set_p("grinder."+field, str(value))
        
    def get_hal(self, field):
        return hal.get_value("grinder."+field)
    
    def update_fields(self):
        self.x_min_edit.setText(str(self.get_hal("x_min")))
        self.x_max_edit.setText(str(self.get_hal("x_max")))
        self.y_min_edit.setText(str(self.get_hal("y_min")))
        self.y_max_edit.setText(str(self.get_hal("y_max")))
        self.z_min_edit.setText(str(self.get_hal("z_min")))
        self.z_max_edit.setText(str(self.get_hal("z_max")))

        self.x_speed_sb.setValue(float(self.get_hal("x_speed")))
        self.y_speed_sb.setValue(float(self.get_hal("y_speed")))
        self.z_speed_sb.setValue(float(self.get_hal("z_speed")))

        self.z_crossfeed_edit.setText(str(self.get_hal("z_crossfeed")))
        self.y_downfeed_edit.setText(str(self.get_hal("y_downfeed")))

        self.stop_at_z_limit_pb.setChecked(bool(self.get_hal("stop_at_z_limit")))
        self.set_toggle_button_color(self.stop_at_z_limit_pb, "stop_at_z_limit")
        self.set_toggle_button_text(self.stop_at_z_limit_pb,"OFF", "ON")

        self.crossfeed_at_cb.setCurrentIndex(int(self.get_hal("crossfeed_at")))
        self.repeat_at_cb.setCurrentIndex(int(self.get_hal("repeat_at")))

    def load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, "rb") as file:
                self.settings = pickle.load(file)
                print(self.settings)
                print("Grinder settings loaded")
        else:
            self.settings = {}
            print("Empty settings loaded")

        self.previous_linear_units = self.settings.get('previous_linear_units',1)
        self.set_hal("x_min", self.settings.get('x_min',0))
        self.set_hal("x_max", self.settings.get('x_max', self.get_converted_value(1, "inch")))
        self.set_hal("y_min", self.settings.get('y_min',0))
        self.set_hal("y_max", self.settings.get('y_max', self.get_converted_value(1, "inch")))
        self.set_hal("z_min",  self.settings.get('z_min',0))
        self.set_hal("z_max",  self.settings.get('z_max', self.get_converted_value(1, "inch")))
        

        self.set_hal("x_speed",  self.settings.get('x_speed', self.get_converted_value(500, "inch")))
        self.set_hal("y_speed",  self.settings.get('y_speed', self.get_converted_value(200, "inch")))
        self.set_hal("z_speed",  self.settings.get('z_speed', self.get_converted_value(200, "inch")))
        

        self.set_hal("z_crossfeed",  self.settings.get('z_crossfeed', self.get_converted_value(0.005, "inch")))        
        self.set_hal("y_downfeed",  self.settings.get('y_downfeed', self.get_converted_value(0.0005, "inch")))
        

        # self.set_hal("enable_x",  False)
        # self.set_hal("enable_y",  False)
        # self.set_hal("enable_z",  False)

        self.set_hal("stop_at_z_limit",  self.settings.get('stop_at_z_limit', 0))
        

        self.set_hal("crossfeed_at",  self.settings.get('crossfeed_at', 2))
        self.set_hal("repeat_at",  self.settings.get('repeat_at', 1))

    def validate_and_set(self, field_name, value, value_type):
        if value_type == "float":
            try:
                self.set_hal(field_name,float(value))
                return float(value)
            except ValueError:
                raise Exception(F"{field_name} must be numeric: {value}")
            
        if value_type == "int":
            try:
                self.set_hal(field_name, int(value))
                return int(value)
            except ValueError:
                raise Exception(F"{field_name} must be an integer: {value}")
            
        if value_type == "bool":
            try:
                self.set_hal(field_name, bool(value))
                return int(value)
            except ValueError:
                raise Exception(F"{field_name} must be a boolean: {value}")

    def on_set_limit_clicked(self, base_name, edit):
        axis_name = base_name.removesuffix("_min")
        axis_name = axis_name.removesuffix("_max")
        axis = Axis.from_str(axis_name)
        #self.set_hal(base_name, self.get_pos(axis))
        edit.setText(str(self.get_pos(axis)))

        
    def set_checked(self, button, hal_field):
        button.setChecked(bool(self.get_hal(hal_field)))
        

    def on_toggle_clicked_mcode(self, button, mcode, off_text = "", on_text = ""):
        mode = GSTAT.get_current_mode()
        self.c.mode(linuxcnc.MODE_MDI)
        self.c.wait_complete() # wait until mode switch executed
        mdi = F"{mcode}{str(int(button.isChecked()))}"
        self.c.mdi(mdi)
        print(mdi)
        self.c.wait_complete()
        self.c.mode(mode)
        # self.set_checked(button, hal_field)

        self.set_toggle_button_text(button, off_text, on_text)

    def on_toggle_clicked(self, button, hal_field, off_text = "", on_text = ""):
        self.set_hal(hal_field, button.isChecked())
        # self.set_checked(button, hal_field)

        self.set_toggle_button_text(button, off_text, on_text)

        self.save_grind_clicked()

        # self.set_toggle_button_color(button,hal_field)

    def set_toggle_button_text(self, button, off_text = "", on_text = ""):
        if button.isChecked():
            if on_text != "":
                button.setText(on_text)
        else:
            if off_text != "":
                button.setText(off_text)

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
            'x_min': self.validate_and_set("x_min", self.x_min_edit.text(),"float"),
            'x_max': self.validate_and_set("x_max", self.x_max_edit.text(),"float"),
            'y_min': self.validate_and_set("y_min", self.y_min_edit.text(),"float"),
            'y_max': self.validate_and_set("y_max", self.y_max_edit.text(),"float"),
            'z_min': self.validate_and_set("x_min", self.x_min_edit.text(),"float"),
            'z_max': self.validate_and_set("x_max", self.x_max_edit.text(),"float"),
            'x_speed': self.validate_and_set("x_speed", self.x_speed_sb.text(),"float"),
            'y_speed': self.validate_and_set("y_speed", self.y_speed_sb.text(),"float"),
            'z_speed': self.validate_and_set("z_speed", self.z_speed_sb.text(),"float"),
            'z_crossfeed': self.validate_and_set("z_crossfeed", self.z_crossfeed_edit.text(),"float"),
            'y_downfeed': self.validate_and_set("y_downfeed", self.y_downfeed_edit.text(),"float"),
            'stop_at_z_limit': self.validate_and_set("stop_at_z_limit", self.stop_at_z_limit_pb.isChecked(),"bool"),
            'crossfeed_at': self.validate_and_set("crossfeed_at", self.crossfeed_at_cb.currentIndex(),"int"),
            'repeat_at': self.validate_and_set("repeat_at", self.repeat_at_cb.currentIndex(),"int"),
        }

        print(self.settings)

        with open(self.settings_file, "wb") as file:
            pickle.dump(self.settings, file

        self.update_fields()

        # except Exception:
        #     self.stop()
        #     #todo set a notification
        #     self.load_settings()

    def stop(self):
        """Start or stop the control loop based on the run_stop signal."""
        self.c.abort()
        self.c.mode(linuxcnc.MODE_MANUAL)


    
