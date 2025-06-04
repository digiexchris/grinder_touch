import sys
from PyQt6.QtWidgets import QLineEdit, QPushButton, QComboBox, QDoubleSpinBox, QSpinBox, QCheckBox, QWidget

import linuxcnc
from hal_glib import GStat

from python.axis import Axis
from python.grinderhal import GrinderHal

def startup(parent):
    # parent.setFixedSize(1920, 1200)
    # parent.setFixedSize(1920, 1000)
    # parent.showFullScreen() # moved to flexhal ini with flexhal > 1.2.0
    try:
        parent.grinder_window = GrinderWindow(parent)
    except Exception as e:
        print(e)
        sys.exit(1)
        return
    

class GrinderWindow(QWidget):
    """Main window class for the VCP."""
    def __init__(self, parent):

        super().__init__(parent)

        self.GSTAT = GStat()
        self.parent = parent
        
        if not GrinderHal.waitForComponentReady(20):
            raise Exception("Grinder component not ready")
        
        self.is_running = GrinderHal.get_hal("is_running")
        self.pos = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        self.GSTAT.connect("current-position", self.update_pos)
        self.GSTAT.connect("state-estop-reset", self.enable_controls)
        self.GSTAT.connect("state-on", self.enable_controls)
        self.GSTAT.connect("state-estop", self.disable_controls)
        self.GSTAT.connect("state-off", self.disable_controls)

        self.c = linuxcnc.command()
        self.s = linuxcnc.stat()
        self.initialize_controls(parent)
        self.update_fields()
    
    def start(self):
        if not GrinderHal.get_hal("is_running"):

            if bool(GrinderHal.get_hal("downfeed_now")):
                GrinderHal.set_hal("downfeed_now", False) # just make sure we don't have an unintended pending downfeed

            #move within limits
            x_pos = self.get_pos(Axis.X)
            x_max = float(GrinderHal.get_hal("x_max"))
            x_min = float(GrinderHal.get_hal("x_min"))
            y_pos = self.get_pos(Axis.Y)
            y_max = float(GrinderHal.get_hal("y_max"))
            y_min = float(GrinderHal.get_hal("y_min"))
            z_pos = self.get_pos(Axis.Z)
            z_max = float(GrinderHal.get_hal("z_max"))
            z_min = float(GrinderHal.get_hal("z_min"))

            if x_pos > x_max + 0.00001 and bool(GrinderHal.get_hal("enable_x")):
                mdi = f"G0 X{x_max}"
                self.c.mdi(mdi)
                self.c.wait_complete(30)

            if y_pos > y_max + 0.00001 and bool(GrinderHal.get_hal("enable_y")):
                mdi = f"G0 Y{y_max}"
                self.c.mdi(mdi)
                self.c.wait_complete(30)

            if z_pos > z_max + 0.00001 and bool(GrinderHal.get_hal("enable_z")):
                mdi = f"G0 Z{z_max}"
                self.c.mdi(mdi)
                self.c.wait_complete(30)

            if x_pos < x_min - 0.00001 and bool(GrinderHal.get_hal("enable_x")):
                mdi = f"G0 X{x_min}"
                self.c.mdi(mdi)
                self.c.wait_complete(30)

            if y_pos < y_min - 0.00001 and bool(GrinderHal.get_hal("enable_y")):
                mdi = f"G0 Y{y_min}"
                self.c.mdi(mdi)
                self.c.wait_complete(30)

            if z_pos < z_min - 0.00001 and bool(GrinderHal.get_hal("enable_z")):
                mdi = f"G0 Z{z_min}"
                self.c.mdi(mdi)
                self.c.wait_complete(30)
        #start the backend
        GrinderHal.set_hal("is_running", True)

    def stop(self):
        GrinderHal.set_hal("is_running", False)

    def enable_controls(self, value):
        if self.GSTAT.estop_is_clear() and self.GSTAT.machine_is_on():
            self.run_stop_pb.setEnabled(True)
            self.enable_x_pb.setEnabled(True)
            self.enable_y_pb.setEnabled(True)
            self.enable_z_pb.setEnabled(True)
            self.downfeed_now_pb.setEnabled(True)

    def disable_controls(self, value):
            self.run_stop_pb.setEnabled(False)
            self.enable_x_pb.setEnabled(False)
            self.enable_y_pb.setEnabled(False)
            self.enable_z_pb.setEnabled(False)
            self.downfeed_now_pb.setEnabled(False)

    def update_pos(self, obj, absolute_pos, relative_pos, dist_to_go, joint_pos):
        running = bool(GrinderHal.get_hal("is_running"))
        if self.is_running != running:
            self.is_running = running
            if running:
                self.set_run_stop_started()
            else:
                self.set_run_stop_stopped()
        self.pos = relative_pos

        self.update_fields()
    
    def is_on(parent):
        return parent.status.task_state == linuxcnc.STATE_ON

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

        self.downfeed_now_pb = parent.findChild(QPushButton, "downfeed_now_pb")
        self.downfeed_now_pb.clicked.connect(lambda: GrinderHal.set_hal("downfeed_now", True))
        self.downfeed_now_pb.setEnabled(False)

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
        print("Starting Grinder")

    def set_run_stop_stopped(self):
        self.run_stop_pb.setText("START")
        self.run_stop_pb.setChecked(False)
        self.set_run_stop_style()
        print("Stopping Grinder")

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
        edit.setText(str(self.get_pos(axis)))

    def set_checked(self, button, hal_field):
        button.setChecked(bool(GrinderHal.get_hal(hal_field)))
        
    def on_toggle_clicked_mcode(self, button, mcode, off_text = "", on_text = ""):
        self.c.mode(linuxcnc.MODE_MDI)
        self.c.wait_complete() # wait until mode switch executed
        mdi = F"{mcode}{str(int(button.isChecked()))}"
        self.c.mdi(mdi)
        print(mdi)
        self.c.wait_complete()
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
        GrinderHal.save_settings()
        self.update_fields()


    
