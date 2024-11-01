from qtpyvcp.widgets.form_widgets.main_window import VCPMainWindow
from qtpy.QtWidgets import QLineEdit, QPushButton, QComboBox, QSpinBox
from qtpy.QtGui import QDoubleValidator
import linuxcnc
import hal
import numpy as np
from qtpy.QtCore import QTimer, QEventLoop
from qtpyvcp.plugins import getPlugin
from enum import Enum

class MachineState(Enum):
    INIT = 0,
    TRAVERSING_START = 1,
    TRAVERSING_MAX = 2,
    TRAVERSING_MIN = 3,
    INFEEDING_START = 4,
    INFEEDING_MAX = 5,
    INFEEDING_MIN = 6,

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

class MainWindow(VCPMainWindow):
    """Main window class for the VCP."""
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.settings = getPlugin('persistent_data_manager')

        self.position_rounding_tolerance = 5

        # Initialize LinuxCNC command, status, and HAL component
        self.c = linuxcnc.command()
        self.s = linuxcnc.stat()
        self.h = hal.component("dynamic_control")

        # Local variables for traverse limits and stepover
        self.traverse_limit_min = float(0.0)
        self.traverse_limit_max = float(0.0)
        self.infeed_limit_min = float(0.0)
        self.infeed_limit_max = float(0.0)
        self.downfeed_limit_min = float(0.0)
        self.downfeed_limit_max = float(0.0)
        self.infeed_stepover = float(0.05)

        self.traverse_axis = Axis.X
        self.infeed_axis = Axis.Z

        # Local variables for infeed type and reverse logic
        # Infeed types are
        # 0: reverse at either stop
        # 1: move to the min and don't reverse
        # 2: move to the max and don't reverse
        # 3: none, don't move or reverse
        self.infeed_reverse = 0

        # Infeed types are
        # 0: Infeed at either traverse stop
        # 1: Infeed only at the right stop
        # 2: Infeed only at the left stop
        # 3: No infeed
        self.infeed_type = 0

        self.infeed_speed = 200
        self.traverse_speed = 500

        # Add HAL pin for run/stop
        self.start_motion = False

        # Add a QTimer for looping control
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.control_loop)

        # Add variables to keep track of state
        self.control_loop_running = False

        self.state = MachineState.INIT
        self.last_state = MachineState.INIT
        self.last_traverse_direction = MachineState.TRAVERSING_MAX
        self.last_infeed_direction = MachineState.INFEEDING_MAX

        # Add custom initialization logic here
        self.initialize_controls()
        self.load_settings()

    def initialize_controls(self):
        """Initialize custom controls and connect UI elements."""
        # Validator to allow only numbers with optional decimals
        double_validator = QDoubleValidator()
        double_validator.setDecimals(5)
        double_validator.setNotation(QDoubleValidator.StandardNotation)

        # Limits Tab

        self.infeed_axis_combo_box = self.findChild(QComboBox, "infeed_axis")
        self.traverse_axis_combo_box = self.findChild(QComboBox, "traverse_axis")
        self.traverse_limit_min_edit = self.findChild(QLineEdit, "traverse_limit_min")
        self.traverse_limit_max_edit = self.findChild(QLineEdit, "traverse_limit_max")
        self.infeed_limit_min_edit = self.findChild(QLineEdit, "infeed_limit_min")
        self.infeed_limit_max_edit = self.findChild(QLineEdit, "infeed_limit_max")

        self.save_limits_button = self.findChild(QPushButton, "save_limits_button")
        if self.save_limits_button:
            self.save_limits_button.clicked.connect(self.on_save_limits_clicked)

        self.cancel_edit_limits_button = self.findChild(QPushButton, "cancel_edit_limits")
        if self.cancel_edit_limits_button:
            self.cancel_edit_limits_button.clicked.connect(self.on_cancel_edit_limits_clicked)

        self.traverse_speed_spinbox = self.findChild(QSpinBox, "traverse_speed")
        # if self.traverse_speed_spinbox:
        #     self.traverse_speed_spinbox.valueChanged.connect(self.on_traverse_speed_changed)

        self.infeed_stepover_edit = self.findChild(QLineEdit, "infeed_stepover")
       
        self.infeed_speed_spinbox = self.findChild(QSpinBox, "infeed_speed")
        # if self.infeed_speed_spinbox:
        #     self.infeed_speed_spinbox.valueChanged.connect(self.on_infeed_speed_changed)

        # Run/Stop Button
        self.run_stop_button = self.findChild(QPushButton, "run_stop_button")
        if self.run_stop_button:
            self.run_stop_button.setCheckable(True)
            self.run_stop_button.setChecked(False)
            self.run_stop_button.clicked.connect(self.on_run_stop_button_clicked)

        # Options Tab
        self.infeed_type_combo_box = self.findChild(QComboBox, "infeed_type")
        self.infeed_reverse_combo_box = self.findChild(QComboBox, "infeed_reverse")
        

    def load_settings(self):
        """Load user settings using PersistentSettings."""
        self.infeed_limit_min = float(self.settings.getData('infeed_limit_min', 0))
        self.infeed_limit_max = float(self.settings.getData('infeed_limit_max', 20))
        self.traverse_limit_min = np.array(self.settings.getData('traverse_limit_min', 0))
        self.traverse_limit_max = np.array(self.settings.getData('traverse_limit_max', 100))
        self.infeed_stepover = float(self.settings.getData('infeed_stepover', 0.05))
        self.infeed_speed = int(self.settings.getData('infeed_speed', 200))
        self.traverse_speed = int(self.settings.getData('traverse_speed', 500))
        self.infeed_type = int(self.settings.getData('infeed_type', 0))
        self.infeed_reverse = int(self.settings.getData('infeed_reverse', 0))
        self.traverse_axis = Axis.from_int(self.settings.getData('traverse_axis', Axis.X.to_int()))
        self.infeed_axis = Axis.from_int(self.settings.getData('infeed_axis', Axis.Z.to_int()))

        # Update the UI
        self.update_ui_from_settings()

    def update_ui_from_settings(self):
        """Update UI fields from loaded settings."""
        self.infeed_limit_min_edit.setText(str(self.infeed_limit_min))
        self.infeed_limit_max_edit.setText(str(self.infeed_limit_max))
        self.infeed_stepover_edit.setText(str(self.infeed_stepover))
        self.traverse_limit_min_edit.setText(str(self.traverse_limit_min))
        self.traverse_limit_max_edit.setText(str(self.traverse_limit_max))

        self.infeed_speed_spinbox.setValue(int(self.infeed_speed))
        self.traverse_speed_spinbox.setValue(int(self.traverse_speed))
        self.infeed_type_combo_box.setCurrentIndex(self.infeed_type)
        self.infeed_reverse_combo_box.setCurrentIndex(self.infeed_reverse)

        self.traverse_axis_combo_box.setCurrentIndex(self.traverse_axis.to_int())
        self.infeed_axis_combo_box.setCurrentIndex(self.infeed_axis.to_int())


    def on_save_infeed_clicked(self):
        """Handle Save Infeed button click."""
        LOG.info("Save Infeed button clicked.")
        self.save_infeed_limits()

    def on_cancel_edit_infeed_clicked(self):
        """Handle Cancel Infeed button click."""
        LOG.info("Cancel Infeed button clicked.")
        # Implement cancel functionality, e.g., reset fields or revert changes
        self.reset_infeed_fields()

    def on_infeed_speed_changed(self, value):
        """Handle Infeed Speed change."""
        LOG.info(f"Infeed speed changed to: {value}")
        self.infeed_speed = int(value)
        # self.settings.setData("infeed_speed", self.infeed_speed)

    def on_traverse_speed_changed(self, value):
        """Handle Traverse Speed change."""
        LOG.info(f"Traverse speed changed to: {value}")
        self.set_traverse_speed(value)

    # def set_traverse_speed(self, speed):
    #     """Set traverse speed in the system."""
    #     # Implement functionality to set speed
    #     LOG.info(f"Setting traverse speed to: {speed}")
    #     self.traverse_speed = speed
    #     try:
    #         LOG.info("Save Traverse Speed button clicked.")
    #         speed = float(self.traverse_speed_spinbox.value())
    #         self.set_traverse_speed(speed)
    #         self.settings.setData("traverse_speed", self.traverse_speed)
    #     except ValueError:
    #         LOG.error("Invalid input: Please enter numeric values for traverse speed.")

    def on_cancel_edit_limits_clicked(self):
        """Handle Cancel Traverse button click."""
        LOG.info("Cancel Traverse button clicked.")
        # Implement cancel functionality, e.g., reset fields or revert changes
        self.reset_limit_fields()

    def reset_limit_fields(self):
        """Reset Traverse limit fields to previous values."""
        self.traverse_limit_min_edit.setText(str(self.traverse_limit_min))
        self.traverse_limit_max_edit.setText(str(self.traverse_limit_max))
        self.infeed_limit_min_edit.setText(str(self.infeed_limit_min))
        self.infeed_limit_max_edit.setText(str(self.infeed_limit_max))
        self.infeed_stepover_edit.setText(str(self.infeed_stepover))

        #todo: reset axis dropdowns
        self.infeed_axis_combo_box.setIndex(self.infeed_axis.to_int())
        self.traverse_axis_combo_box.setIndex(self.traverse_axis.to_int())
        
        LOG.info("Infeed limit fields reset to previous values.")
        LOG.info("Traverse fields reset to previous values.")

    def on_infeed_type_changed(self, index=None):
        """Handle infeed type change event."""
        if index is None:  # If called directly, set to the current index
            index = self.infeed_type_combo_box.currentIndex()
        
        self.infeed_type = index
        LOG.info(f"Infeed type changed to index: {index}")

    def on_infeed_reverse_changed(self, index=None):
        """Handle infeed reverse change event."""
        if index is None:  # If called directly, set to the current index
            index = self.infeed_reverse_combo_box.currentIndex()

        self.infeed_reverse = index
        LOG.info(f"Infeed reverse changed to index: {index}")

    def is_machine_idle(self):
        """Check if the machine is idle and ready for MDI."""
        self.s.poll()  # Update the status

        if self.s.interp_state == linuxcnc.INTERP_IDLE:
            return True
        else:
            return False

    def on_run_stop_button_clicked(self):
        """Handle run/stop button toggle."""
        self.start_motion = not self.start_motion

        if self.start_motion:

            if not self.is_machine_idle():
                LOG.info("Machine is busy, cannot enter MDI mode. Not starting.")
                return
            
            self.c.mode(linuxcnc.MODE_MDI)
            self.c.mdi(F"G90")
           
            self.c.wait_complete()

            self.run_stop_button.setText("Running")
            self.run_stop_button.setStyleSheet("background-color: green; color: white;")
            self.run_stop_button.setChecked(True)
            LOG.info("Run/Stop toggled to 'run'.")
            self.timer.start(250)
        else:
            self.stop()
            LOG.info("Run/Stop toggled to 'stop'.")

    def on_save_limits_clicked(self):
        """Handle save button click."""
        self.save_limits()

    def save_limits(self):
        """Stop movement, wait for idle, then save the traverse limits and 3D stepover values."""
        self.stop()  # Stops the timer and sets run_stop to False

        try:
            self.infeed_axis = Axis.from_int(self.infeed_axis_combo_box.currentIndex())
            self.settings.setData("infeed_axis", int(self.infeed_axis.to_int()))

            self.traverse_axis = Axis.from_int(self.traverse_axis_combo_box.currentIndex())
            self.settings.setData("traverse_axis", int(self.traverse_axis.to_int()))

            self.traverse_limit_min = round(float(self.traverse_limit_min_edit.text()), self.position_rounding_tolerance)
            self.traverse_limit_max = round(float(self.traverse_limit_max_edit.text()), self.position_rounding_tolerance)

            self.settings.setData("traverse_limit_min", self.traverse_limit_min)
            self.settings.setData("traverse_limit_max", self.traverse_limit_max)

            LOG.info("Traverse limits saved successfully.")

            self.infeed_limit_min = round(float(self.infeed_limit_min_edit.text()), self.position_rounding_tolerance)
            self.infeed_limit_max = round(float(self.infeed_limit_max_edit.text()), self.position_rounding_tolerance)
            
            self.infeed_stepover = round(float(self.infeed_stepover_edit.text()), self.position_rounding_tolerance)

            self.settings.setData("infeed_limit_max", self.infeed_limit_max)
            self.settings.setData("infeed_limit_min", self.infeed_limit_min)
            self.settings.setData("stepover", self.infeed_stepover)

            self.settings.setData("infeed_speed", int(self.infeed_speed))
            self.settings.setData("traverse_speed", int(self.traverse_speed))

            LOG.info("Infeed limits saved successfully.")

        except ValueError:
            LOG.error("Invalid input: Please enter numeric values for limits and stepover.")

    def stop(self):
        """Start or stop the control loop based on the run_stop signal."""
        self.timer.stop()
        self.c.abort()
        self.stopped_mid_cycle = True
        self.start_motion = False
        self.run_stop_button.setText("Start")
        self.run_stop_button.setStyleSheet("")
        self.run_stop_button.setChecked(False)
        self.stopped_mid_cycle = True
        LOG.info("Waiting for machine to stop...")
        self.wait_for_idle()

    def should_infeed(self, target):
        """Determine if infeed should occur based on target and infeed type."""
        # Infeed types are
        # 0: Infeed at either traverse stop
        # 1: Infeed only at the right stop
        # 2: Infeed only at the left stop
        # 3: No infeed

        if self.infeed_type == 0:
            return True
        elif self.infeed_type == 1 and target == MachineState.TRAVERSING_MAX:
            return True
        elif self.infeed_type == 2 and target == MachineState.TRAVERSING_MIN:
            return True
        return False

    def reverse_infeed(self):
        """Invert the sign of the 3D stepover and handle infeed reverse logic."""
        if self.infeed_reverse == 0:
            # Reverse stepover
            #self.infeed_stepover = -self.infeed_stepover

            # Update UI elements
            #self.infeed_stepover_edit.setText(str(self.infeed_stepover))

            if self.last_infeed_direction == MachineState.INFEEDING_MAX:
                self.last_infeed_direction = MachineState.INFEEDING_MIN
                self.last_state = MachineState.INFEEDING_MIN
            elif self.last_infeed_direction == MachineState.INFEEDING_MIN:
                self.last_infeed_direction = MachineState.INFEEDING_MAX
                self.last_state = MachineState.INFEEDING_MAX

            LOG.info(f"Infeed reversed: {MachineState.INFEEDING_MAX.name}")

            return True
        elif self.infeed_reverse == 1:
            self.move_to(self.infeed_axis, self.infeed_limit_min, self.infeed_speed)
            return False
        elif self.infeed_reverse == 2:
            self.move_to(self.infeed_axis, self.infeed_limit_max, self.infeed_speed)
            return False

    def move_to(self, axis, pos, speed):
        LOG.info(F"Move_To: G1 {axis}{pos} F{speed}")
        self.c.mdi(F"G1 {axis}{pos} F{speed}")

    def check_and_reverse(self, current_pos):
        LOG.info(F"execute infeed at pos {self.s.position}")
        at_min_height = current_pos <= self.infeed_limit_min
        at_max_height = current_pos >= self.infeed_limit_max
        if(at_min_height and self.state == MachineState.INFEEDING_MIN):
            self.reverse_infeed()
            return True
        elif(at_max_height and self.state == MachineState.INFEEDING_MAX):
            self.reverse_infeed()
            return True
        else:
            return False

    def execute_infeed(self, infeed_dir):
        """Handle the infeed logic at each traverse limit."""
        self.s.poll()
        current_pos = round(self.s.position[self.infeed_axis.to_int()], self.position_rounding_tolerance)
        LOG.info(F"Execute Infeed on {self.infeed_axis.to_str()} from {current_pos} ")
        if self.last_traverse_direction == MachineState.TRAVERSING_MAX and self.should_infeed(MachineState.TRAVERSING_MAX):

            if self.check_and_reverse(current_pos):
                return

        elif self.last_traverse_direction == MachineState.TRAVERSING_MIN and self.should_infeed(MachineState.TRAVERSING_MIN):

            if self.check_and_reverse(current_pos):
                return
        
        LOG.info(F"Infeeding...")
        

        infeed_stepover = self.infeed_stepover

        sign = ""

        if infeed_dir == MachineState.INFEEDING_MIN:
            infeed_stepover = -infeed_stepover
            if(current_pos + infeed_stepover < self.infeed_limit_min):
                infeed_stepover = self.infeed_limit_min - current_pos
        elif infeed_dir == MachineState.INFEEDING_MAX:
            if(current_pos + infeed_stepover > self.infeed_limit_max):
                infeed_stepover = self.infeed_limit_max - current_pos        
        
        if round(infeed_stepover, 7) == 0:
            #this probably should never happen
            LOG.warn("Infeed tried to infeed with 0 stepover.")
            return
        
        self.c.mdi(F"G91")
        self.c.mdi(F"G1 {self.infeed_axis.to_str()}{infeed_stepover} F{self.infeed_speed}")
        self.c.mdi(F"G90")

        LOG.info("Infeed done.")

        self.last_infeed_direction = infeed_dir
        self.last_state = infeed_dir
        self.state = MachineState.TRAVERSING_START

    def control_loop(self):
        """Main control loop with state tracking and reentrancy protection."""
        if self.control_loop_running:
            LOG.warning("Control loop skipped: Already running.")
            return

        self.control_loop_running = True
        self.s.poll()

        if not self.s.enabled or self.s.estop or not self.start_motion:
            self.timer.stop()
            LOG.info("Control loop stopped: Machine not ready.")
            self.stopped_mid_cycle = True
            self.exit_control_loop()
            return
        
        #not ready for a new command yet
        if self.s.interp_state != linuxcnc.INTERP_IDLE:
            self.exit_control_loop()
            return

        try:
            if self.s.interpreter_errcode != 0:
                error_message = self.s.error
                LOG.error(f"USRMOT error detected, stopping: {error_message}")

                # Stop the machine and display an error message
                self.stop()
                self.show_error_message(F"Error: {error_message}")
                self.exit_control_loop()  # Exit control loop to prevent further actions
                return
        
            if self.s.interp_state == linuxcnc.INTERP_IDLE:
                current_pos = np.array(self.s.position[:3])

                LOG.info(F"Position: {current_pos}")
                LOG.info(F"State: {self.state.name}")

                if self.state == MachineState.INIT:
                    LOG.info(F"State is {self.state}")
                    self.state = MachineState.TRAVERSING_MAX
                    self.exit_control_loop()
                    return
                
                if self.state == MachineState.TRAVERSING_START:
                    LOG.info(F"State is {self.state}")
                    if self.last_state == MachineState.INFEEDING_MAX or self.last_state == MachineState.INFEEDING_MIN:
                        if self.last_traverse_direction == MachineState.TRAVERSING_MAX:
                            self.state = MachineState.TRAVERSING_MIN
                        elif self.last_traverse_direction == MachineState.TRAVERSING_MIN:
                            self.state = MachineState.TRAVERSING_MAX
                        else:
                            self.state = MachineState.TRAVERSING_MAX
                    else:
                        self.state = MachineState.TRAVERSING_MAX

                    self.exit_control_loop()
                    return
                    
                
                elif self.state == MachineState.TRAVERSING_MAX:
                    LOG.info(F"State is {self.state}")
                    LOG.info(F"Traverse Axis {self.traverse_axis.to_str()} position {round(current_pos[self.traverse_axis.to_int()], self.position_rounding_tolerance)} Traverse Limit {self.traverse_limit_max}")

                    if round(current_pos[self.traverse_axis.to_int()], self.position_rounding_tolerance) < self.traverse_limit_max:
                        self.move_to(self.traverse_axis.to_str(),self.traverse_limit_max, self.traverse_speed)
                        self.last_traverse_direction = MachineState.TRAVERSING_MAX
                        self.last_state = MachineState.TRAVERSING_MAX
                        self.exit_control_loop()
                        return
                    else:
                        self.state = MachineState.INFEEDING_START
                        self.last_traverse_direction = MachineState.TRAVERSING_MAX
                        self.exit_control_loop()
                        return

                elif self.state == MachineState.TRAVERSING_MIN:
                    LOG.info(F"State is {self.state}")
                    LOG.info(F"Traverse Axis {self.traverse_axis.to_str()} position {current_pos[self.traverse_axis.to_int()]} Traverse Limit {self.traverse_limit_max}")
                    if round(current_pos[self.traverse_axis.to_int()], self.position_rounding_tolerance) > self.traverse_limit_min:
                        self.move_to(self.traverse_axis.to_str(), self.traverse_limit_min, self.traverse_speed)
                        self.last_traverse_direction = MachineState.TRAVERSING_MIN
                        self.last_state = MachineState.TRAVERSING_MIN
                        self.exit_control_loop()
                        return
                    else:
                        self.state = MachineState.INFEEDING_START
                        self.last_traverse_direction = MachineState.TRAVERSING_MIN
                        self.exit_control_loop()
                        return
                        
                elif self.state == MachineState.INFEEDING_START:
                    LOG.info(F"State is {self.state}")
                    if self.last_infeed_direction == MachineState.INFEEDING_MAX:
                        self.state = MachineState.INFEEDING_MAX
                    elif self.last_infeed_direction == MachineState.INFEEDING_MIN:
                        self.state = MachineState.INFEEDING_MIN
                    else:
                        self.state = MachineState.INFEEDING_MAX

                    self.exit_control_loop()
                    return
                
                elif self.state == MachineState.INFEEDING_MAX:
                    LOG.info(F"State is {self.state}")
                    if round(current_pos[self.infeed_axis.to_int()], self.position_rounding_tolerance) >= self.infeed_limit_max:
                        if self.reverse_infeed():
                            self.state = MachineState.TRAVERSING_START
                            self.last_state = MachineState.INFEEDING_MAX
                            self.exit_control_loop()
                            return
                        else:
                            #reverse_infeed is executing a move
                            self.exit_control_loop()
                            return
                    else:    
                        self.execute_infeed(MachineState.INFEEDING_MAX)
                        self.exit_control_loop()
                        return
                        
                elif self.state == MachineState.INFEEDING_MIN:
                    if round(current_pos[self.infeed_axis.to_int()], self.position_rounding_tolerance) <= self.infeed_limit_min:
                        if self.reverse_infeed():
                            self.state = MachineState.TRAVERSING_START
                            self.last_state = MachineState.INFEEDING_MIN
                            self.exit_control_loop()
                            return
                        else:
                            #reverse_infeed is executing a move
                            self.exit_control_loop()
                            return
                    else:    
                        self.execute_infeed(MachineState.INFEEDING_MIN)
                        self.exit_control_loop()
                        return
            
        except linuxcnc.error as e:
            LOG.error(f"Error in control loop: {e}")
            self.stop()

        self.exit_control_loop()
        return

    def exit_control_loop(self):
        self.control_loop_running = False
        return
    
    def wait_for_idle(self):
        """Wait until the machine becomes idle."""
        while True:
            self.s.poll()
            if self.s.interp_state == linuxcnc.INTERP_IDLE:
                break
            QEventLoop().processEvents()
