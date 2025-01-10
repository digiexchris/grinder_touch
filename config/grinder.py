import os
import sys
from PyQt6.QtWidgets import QLineEdit, QPushButton, QComboBox, QDoubleSpinBox, QSpinBox, QCheckBox, QWidget

import linuxcnc
from hal_glib import GStat

from python.axis import Axis
from python.grinderhal import GrinderHal

# from qtpyvcp.hal import QPin

import pickle

def startup(parent):
    #parent.setFixedSize(1920, 1200)
    parent.setFixedSize(1920, 1000)
    #parent.showFullScreen()
    try:
        parent.grinder_window = GrinderWindow(parent)
    except Exception as e:
        print(e)
        sys.exit(1)
        return
    # parent.grinder_window.initialize_hal()
    parent.grinder_window.load_settings()
    parent.grinder_window.initialize_controls(parent)
    
    

class GrinderWindow(QWidget):
    """Main window class for the VCP."""
    def __init__(self, parent):

        super().__init__(parent)

        self.GSTAT = GStat()
        self.parent = parent
        
        
        self.is_running = False

        self.settings_file = "./grinder.pkl"

        if not GrinderHal.waitForComponentReady(20):
            raise Exception("Grinder component not ready")

        self.pos = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        self.GSTAT.connect("current-position", self.update_pos)
        self.GSTAT.connect("state-estop-reset", self.enable_controls)
        self.GSTAT.connect("state-on", self.enable_controls)
        self.GSTAT.connect("state-estop", self.disable_controls)
        self.GSTAT.connect("state-off", self.disable_controls)

        self.c = linuxcnc.command()
        self.s = linuxcnc.stat()
    def start(self):
        GrinderHal.set_hal("is_running", True)

    def stop(self):
        GrinderHal.set_hal("is_running", False)

    def enable_controls(self, value):
        if self.GSTAT.estop_is_clear() and self.GSTAT.machine_is_on():
            self.run_stop_pb.setEnabled(True)
            self.enable_x_pb.setEnabled(True)
            self.enable_y_pb.setEnabled(True)
            self.enable_z_pb.setEnabled(True)

    def disable_controls(self, value):
            self.run_stop_pb.setEnabled(False)
            self.enable_x_pb.setEnabled(False)
            self.enable_y_pb.setEnabled(False)
            self.enable_z_pb.setEnabled(False)

    def update_pos(self, obj, absolute_pos, relative_pos, dist_to_go, joint_pos):
        running = bool(GrinderHal.get_hal("is_running"))
        if self.is_running != running:
            self.is_running = running
            if running:
                self.set_run_stop_started()
            else:
                self.set_run_stop_stopped()
        self.pos = relative_pos

    def get_converted_value(self, value, units):
        if units != "inch" and units != "mm":
            raise Exception("Get converted value called with invalid unit type")

        if self.GSTAT.is_metric_mode():
            if units == "mm":
                return value
            else:
                return value*25.4
        else:
            if units == "inch":
                return value
            else:
                return value/25.4
            
        
            
    def is_on(parent):
        return parent.status.task_state == linuxcnc.STATE_ON
# if parent.status.task_state == emc.STATE_ESTOP:

    def get_pos(self, axis):

        return round(self.pos[axis.to_int()], GrinderHal.get_rounding_tolerance())
    
    def on_value_changed(self, field, value, value_type):
        try:
            v = self.validate_and_set(field, value, value_type)
            self.save_grind_clicked()
        except ValueError:
            return

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
        self.stop_at_z_limit_pb.clicked.connect(lambda: self.on_toggle_clicked(self.stop_at_z_limit_pb, "stop_at_z_limit"))

        # Run/Stop Button
        self.run_stop_pb = parent.findChild(QPushButton, "run_stop_pb")
        self.run_stop_pb.clicked.connect(lambda: self.on_run_stop_clicked())
        self.run_stop_pb.setEnabled(False)
        self.run_stop_pb.setCheckable(False)
        self.set_button_color(self.run_stop_pb,False)

        self.enable_x_pb = parent.findChild(QPushButton, "enable_x_pb")
        self.enable_x_pb.clicked.connect(lambda: self.on_toggle_clicked(self.enable_x_pb, "enable_x"))
        self.set_button_color(self.enable_x_pb, False)
        self.enable_x_pb.setEnabled(False)
        self.enable_y_pb = parent.findChild(QPushButton, "enable_y_pb")
        self.enable_y_pb.clicked.connect(lambda: self.on_toggle_clicked(self.enable_y_pb, "enable_y"))
        self.set_button_color(self.enable_y_pb, False)
        self.enable_y_pb.setEnabled(False)
        self.enable_z_pb = parent.findChild(QPushButton, "enable_z_pb")
        self.enable_z_pb.clicked.connect(lambda: self.on_toggle_clicked(self.enable_z_pb, "enable_z"))
        self.set_button_color(self.enable_z_pb, False)
        self.enable_y_pb.setEnabled(False)

        self.update_fields()

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
        new_background = "background-color: green;" if self.is_running else "background-color: red;"
        self.run_stop_pb.setStyleSheet(f"{existing_styles} {new_background}")

    def set_run_stop_started(self):
        self.run_stop_pb.setText("STOP")
        self.run_stop_pb.setChecked(True)
        self.set_run_stop_style()
        print("Run Stop started UI")

    def set_run_stop_stopped(self):
        self.run_stop_pb.setText("START")
        self.run_stop_pb.setChecked(False)
        self.set_run_stop_style()
        print("Run Stop stopped UI")

    def on_run_stop_clicked(self):
        if self.is_running:
            self.stop()
        else:
            self.start()

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

            self.x_min_edit.setText(str(GrinderHal.get_hal("x_min") * conversion_factor))    
            self.x_min_edit.setText(str(GrinderHal.get_hal("x_max") * conversion_factor))  
            self.x_min_edit.setText(str(GrinderHal.get_hal("y_min") * conversion_factor))    
            self.x_min_edit.setText(str(GrinderHal.get_hal("y_max") * conversion_factor))  
            self.x_min_edit.setText(str(GrinderHal.get_hal("z_min") * conversion_factor))    
            self.x_min_edit.setText(str(GrinderHal.get_hal("z_max") * conversion_factor))  
            self.x_speed_sb.setValue(float(GrinderHal.get_hal("x_speed") * conversion_factor))
            self.y_speed_sb.setValue(float(GrinderHal.get_hal("y_speed") * conversion_factor))
            self.z_speed_sb.setValue(float(GrinderHal.get_hal("z_speed") * conversion_factor))
            self.z_crossfeed_edit.setText(str(GrinderHal.get_hal("z_crossfeed") * conversion_factor))
            self.y_downfeed_edit.setText(str(GrinderHal.get_hal("y_downfeed") * conversion_factor))

            # self.save_grind_clicked()

    def on_hal_toggle_changed(self, button, hal_field):

        self.set_checked(button, hal_field)
        self.set_button_color(button,bool(button.isChecked()))
    
    def update_fields(self):
        self.x_min_edit.setText(str(GrinderHal.get_hal("x_min")))
        self.x_max_edit.setText(str(GrinderHal.get_hal("x_max")))
        self.y_min_edit.setText(str(GrinderHal.get_hal("y_min")))
        self.y_max_edit.setText(str(GrinderHal.get_hal("y_max")))
        self.z_min_edit.setText(str(GrinderHal.get_hal("z_min")))
        self.z_max_edit.setText(str(GrinderHal.get_hal("z_max")))

        self.x_speed_sb.setValue(float(GrinderHal.get_hal("x_speed")))
        self.y_speed_sb.setValue(float(GrinderHal.get_hal("y_speed")))
        self.z_speed_sb.setValue(float(GrinderHal.get_hal("z_speed")))

        self.z_crossfeed_edit.setText(str(GrinderHal.get_hal("z_crossfeed")))
        self.y_downfeed_edit.setText(str(GrinderHal.get_hal("y_downfeed")))

        self.enable_x_pb.setChecked(bool(GrinderHal.get_hal("enable_x")))
        self.set_button_color(self.enable_x_pb, bool(GrinderHal.get_hal("enable_x")))
        self.enable_y_pb.setChecked(bool(GrinderHal.get_hal("enable_y")))
        self.set_button_color(self.enable_y_pb, bool(GrinderHal.get_hal("enable_y")))
        self.enable_z_pb.setChecked(bool(GrinderHal.get_hal("enable_z")))
        self.set_button_color(self.enable_z_pb, bool(GrinderHal.get_hal("enable_z")))

        self.stop_at_z_limit_pb.setChecked(bool(GrinderHal.get_hal("stop_at_z_limit")))
        self.set_button_color(self.stop_at_z_limit_pb, bool(GrinderHal.get_hal("stop_at_z_limit")))
        #self.set_toggle_button_text(self.stop_at_z_limit_pb,"OFF", "ON")

        self.crossfeed_at_cb.setCurrentIndex(int(GrinderHal.get_hal("crossfeed_at")))
        self.repeat_at_cb.setCurrentIndex(int(GrinderHal.get_hal("repeat_at")))

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
        GrinderHal.set_hal("x_min", self.settings.get('x_min',0))
        GrinderHal.set_hal("x_max", self.settings.get('x_max', self.get_converted_value(1, "inch")))
        GrinderHal.set_hal("y_min", self.settings.get('y_min',0))
        GrinderHal.set_hal("y_max", self.settings.get('y_max', self.get_converted_value(1, "inch")))
        GrinderHal.set_hal("z_min",  self.settings.get('z_min',0))
        GrinderHal.set_hal("z_max",  self.settings.get('z_max', self.get_converted_value(1, "inch")))
        

        GrinderHal.set_hal("x_speed",  self.settings.get('x_speed', self.get_converted_value(500, "inch")))
        print("X_SPEED:")
        print(GrinderHal.get_hal("x_speed"))
        print(self.get_converted_value(500, "inch"))
        GrinderHal.set_hal("y_speed",  self.settings.get('y_speed', self.get_converted_value(200, "inch")))
        GrinderHal.set_hal("z_speed",  self.settings.get('z_speed', self.get_converted_value(200, "inch")))
        

        GrinderHal.set_hal("z_crossfeed",  self.settings.get('z_crossfeed', self.get_converted_value(0.005, "inch")))        
        GrinderHal.set_hal("y_downfeed",  self.settings.get('y_downfeed', self.get_converted_value(0.0005, "inch")))
        
        GrinderHal.set_hal("enable_x",  self.settings.get('enable_x', bool(False)))
        GrinderHal.set_hal("enable_y",  self.settings.get('enable_y', bool(False)))
        GrinderHal.set_hal("enable_z",  self.settings.get('enable_z', bool(False)))

        GrinderHal.set_hal("stop_at_z_limit",  self.settings.get('stop_at_z_limit', 0))

        GrinderHal.set_hal("crossfeed_at",  self.settings.get('crossfeed_at', 2))
        GrinderHal.set_hal("repeat_at",  self.settings.get('repeat_at', 1))

    def validate_and_set(self, field_name, value, value_type):
        if value_type == "float":
            try:
                GrinderHal.set_hal(field_name,float(value))
                return float(value)
            except ValueError:
                raise Exception(F"{field_name} must be numeric: {value}")
            
        if value_type == "int":
            try:
                GrinderHal.set_hal(field_name, int(value))
                return int(value)
            except ValueError:
                raise Exception(F"{field_name} must be an integer: {value}")
            
        if value_type == "bool":
            try:
                GrinderHal.set_hal(field_name, bool(value))
                return int(value)
            except ValueError:
                raise Exception(F"{field_name} must be a boolean: {value}")

    def on_set_limit_clicked(self, base_name, edit):
        axis_name = base_name.removesuffix("_min")
        axis_name = axis_name.removesuffix("_max")
        axis = Axis.from_str(axis_name)
        #GrinderHal.set_hal(base_name, self.get_pos(axis))
        edit.setText(str(self.get_pos(axis)))

    def set_checked(self, button, hal_field):
        button.setChecked(bool(GrinderHal.get_hal(hal_field)))
        
    def on_toggle_clicked_mcode(self, button, mcode, off_text = "", on_text = ""):
        # mode = self.GSTAT.get_current_mode()
        self.c.mode(linuxcnc.MODE_MDI)
        self.c.wait_complete() # wait until mode switch executed
        mdi = F"{mcode}{str(int(button.isChecked()))}"
        self.c.mdi(mdi)
        print(mdi)
        self.c.wait_complete()
        # self.set_checked(button, hal_field)

        self.set_button_color(button,bool(button.isChecked()))

        self.set_toggle_button_text(button, off_text, on_text)

    def on_toggle_clicked(self, button, hal_field, off_text = "", on_text = ""):
        checked = not bool(GrinderHal.get_hal(hal_field))
        GrinderHal.set_hal(hal_field, checked)
        self.set_checked(button, hal_field)

        self.set_toggle_button_text(button, off_text, on_text)

        self.save_grind_clicked()

        self.set_button_color(button,checked)

    def set_toggle_button_text(self, button, off_text = "", on_text = ""):
        if button.isChecked():
            if on_text != "":
                button.setText(on_text)
        else:
            if off_text != "":
                button.setText(off_text)

    def set_button_color(self, button, on_or_off_bool):

        existing_styles = button.styleSheet()
        new_background = "background-color: green;" if bool(on_or_off_bool) else "background-color: red;"
        button.setStyleSheet(f"{existing_styles} {new_background}")

    def save_grind_clicked(self):
        """Stop movement, wait for idle, then save the traverse limits and 3D stepover values."""

        print("Saving grind settings")

        try:
            self.settings = {
                'previous_linear_units': self.previous_linear_units,
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
            }

            with open(self.settings_file, "wb") as file:
                pickle.dump(self.settings, file)

            self.update_fields()

        except Exception:
            self.stop()
            #todo set a notification
            self.load_settings()


    
