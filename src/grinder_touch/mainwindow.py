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

        ############# milltouch ##############

        self.setWindowFlags(
            Qt.Window |
            Qt.CustomizeWindowHint |
            Qt.WindowStaysOnTopHint
            )

        LOG.setLevel('DEBUG')

        self.coordOffsetGroup.buttonClicked.connect(self.offsetHandleKeys)
        self.toolButtonGroup.buttonClicked.connect(self.toolHandleKeys)
        self.toolBackSpace.clicked.connect(self.toolHandleBackSpace)
        self.mdiSmartButtonGroup.buttonClicked.connect(self.mdiSmartHandleKeys)
        self.mdiLoadParameters.clicked.connect(self.mdiSmartSetLabels)
        self.mdiSmartBackspace.clicked.connect(self.mdiSmartHandleBackSpace)
        self.gcodeHelpBtn.clicked.connect(self.tabForward)
        self.mdiBackBtn.clicked.connect(self.tabBack)

        ############### end milltouch ###########

        self.settings = getPlugin('persistent_data_manager')

        self.position_rounding_tolerance_in = 5
        self.position_rounding_tolerance_mm = 3

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

        self.infeed_enabled = False
        self.traverse_enabled = False

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

        self.axis_pins = [None] * 3  # Initialize a list with three elements
        self.axis_pins[0] = hal.getHALPin('halui.axis.x.pos-relative')
        self.axis_pins[1] = hal.getHALPin('halui.axis.y.pos-relative')
        self.axis_pins[2] = hal.getHALPin('halui.axis.z.pos-relative')
        self.is_on_pin = hal.getHALPin('halui.machine.is-on')

        # Add custom initialization logic here
        self.initialize_controls()
        self.load_settings()

    ############ milltouch ##################

    def tabForward(parent):
        parent.mdiStackedWidget.setCurrentIndex(parent.mdiStackedWidget.currentIndex() + 1)
    def tabBack(parent):
        parent.mdiStackedWidget.setCurrentIndex(parent.mdiStackedWidget.currentIndex() - 1)

    def mdiSmartHandleKeys(self, button):
        char = str(button.text())
        text = self.mdiSmartEntry.text() or '0'
        if text != '0':
            text += char
        else:
            text = char
        self.mdiSmartEntry.setText(text)

    def mdiSmartSetLabels(self):
        # get smart and figure out what axes are used

        text = self.mdiSmartEntry.text() or '0'
        if text != '0':
            words = helptext.gcode_words()
            if text in words:
                self.mdiSmartClear()
                print(type(words[text]))
                for index, value in enumerate(words[text], start=1):
                    getattr(self, 'gcodeParameter_' + str(index)).setText(value)
            else:
                self.mdiSmartClear()
            titles = helptext.gcode_titles()
            if text in titles:
                self.gcodeDescription.setText(titles[text])
            else:
                self.mdiSmartClear()
            self.gcodeHelpLabel.setText(helptext.gcode_descriptions(text))
        else:
            self.mdiSmartClear()

    def mdiSmartClear(self):
        for index in range(1,13):
            getattr(self, 'gcodeParameter_' + str(index)).setText('')
        self.gcodeDescription.setText('')
        self.gcodeHelpLabel.setText('')

    def mdiSmartHandleBackSpace(self):
        if len(self.mdiSmartEntry.text()) > 0:
            text = self.mdiSmartEntry.text()[:-1]
            self.mdiSmartEntry.setText(text)

    def offsetHandleKeys(self, button):
        char = str(button.text())
        text = self.cordOffsetLbl.text() or '0'
        if text != '0':
            text += char
        else:
            text = char
        self.cordOffsetLbl.setText(text)

    def toolHandleKeys(self, button):
        char = str(button.text())
        text = self.toolOffsetLabel.text() or '0'
        if text != '0':
            text += char
        else:
            text = char
        self.toolOffsetLabel.setText(text)

    def toolHandleBackSpace(self):
        if len(self.toolOffsetLabel.text()) > 0:
            text = self.toolOffsetLabel.text()[:-1]
            self.toolOffsetLabel.setText(text)


    def on_exitBtn_clicked(self):
        self.app.quit()

    ############### end milltouch ################

    def get_rounding_tolerance(self):
        # Check the current units
        if self.linear_units == 1.0:
            return self.position_rounding_tolerance_mm
        elif self.linear_units == 25.4:
            return self.position_rounding_tolerance_in
        else:
            raise Exception("Unknown work coordinate system units")

    def get_pos(self, axis):

        return round(self.axis_pins[axis.to_int()], self.get_rounding_tolerance())

    def initialize_controls(self):
        """Initialize custom controls and connect UI elements."""
        # Validator to allow only numbers with optional decimals
        double_validator = QDoubleValidator()
        double_validator.setDecimals(5)
        double_validator.setNotation(QDoubleValidator.StandardNotation)

        self.enable_infeed_button = self.findChild(QPushButton, "enable_infeed_button")
        self.enable_traverse_button = self.findChild(QPushButton, "enable_traverse_button")

        self.disable_infeed_at_limit_checkbox = self.findChild(QCheckBox, "disable_infeed_at_limit_checkbox")
        self.disable_infeed_at_limit_checkbox.clicked.connect(self.on_disable_infeed_at_limit_checkbox_clicked)
        self.disable_traverse_at_infeed_limit_checkbox = self.findChild(QCheckBox, "disable_traverse_at_infeed_limit_checkbox")
        self.disable_traverse_at_infeed_limit_checkbox.clicked.connect(self.on_disable_traverse_at_infeed_limit_checkbox_clicked)

        self.enable_infeed_button.setCheckable(True)
        self.enable_infeed_button.setChecked(False)
        self.enable_infeed_button.clicked.connect(self.on_enable_infeed_button_clicked)

        self.enable_traverse_button.setCheckable(True)
        self.enable_traverse_button.setChecked(False)
        self.enable_traverse_button.clicked.connect(self.on_enable_traverse_button_clicked)

        self.infeed_axis_combo_box = self.findChild(QComboBox, "infeed_axis")
        self.traverse_axis_combo_box = self.findChild(QComboBox, "traverse_axis")
        self.traverse_limit_min_edit = self.findChild(QLineEdit, "traverse_limit_min")
        self.traverse_limit_max_edit = self.findChild(QLineEdit, "traverse_limit_max")
        self.infeed_limit_min_edit = self.findChild(QLineEdit, "infeed_limit_min")
        self.infeed_limit_max_edit = self.findChild(QLineEdit, "infeed_limit_max")

        self.save_limits_button = self.findChild(QPushButton, "save_limits_button")
        if self.save_limits_button:
            self.save_limits_button.clicked.connect(self.on_save_limits_clicked)

        self.traverse_speed_spinbox = self.findChild(QDoubleSpinBox, "traverse_speed")

        self.infeed_stepover_edit = self.findChild(QLineEdit, "infeed_stepover")
       
        self.infeed_speed_spinbox = self.findChild(QDoubleSpinBox, "infeed_speed")

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
        self.disable_infeed_at_limit = bool(self.settings.getData('disable_infeed_at_limit', False))
        self.disable_traverse_at_infeed_limit = bool(self.settings.getData('disable_traverse_at_infeed_limit', False))
        self.infeed_limit_min = float(self.settings.getData('infeed_limit_min', 0))
        self.infeed_limit_max = float(self.settings.getData('infeed_limit_max', 1))
        self.traverse_limit_min = np.array(self.settings.getData('traverse_limit_min', 0))
        self.traverse_limit_max = np.array(self.settings.getData('traverse_limit_max', 1))
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
        self.disable_infeed_at_limit_checkbox.setChecked(self.disable_infeed_at_limit)
        self.disable_traverse_at_infeed_limit_checkbox.setChecked(self.disable_traverse_at_infeed_limit)
        self.infeed_limit_min_edit.setText(str(self.infeed_limit_min))
        self.infeed_limit_max_edit.setText(str(self.infeed_limit_max))
        self.infeed_stepover_edit.setText(str(self.infeed_stepover))
        self.traverse_limit_min_edit.setText(str(self.traverse_limit_min))
        self.traverse_limit_max_edit.setText(str(self.traverse_limit_max))

        self.infeed_speed_spinbox.setValue(float(self.infeed_speed))
        self.traverse_speed_spinbox.setValue(float(self.traverse_speed))
        self.infeed_type_combo_box.setCurrentIndex(self.infeed_type)
        self.infeed_reverse_combo_box.setCurrentIndex(self.infeed_reverse)

        self.traverse_axis_combo_box.setCurrentIndex(self.traverse_axis.to_int())
        self.infeed_axis_combo_box.setCurrentIndex(self.infeed_axis.to_int())


    def on_infeed_speed_changed(self, value):
        """Handle Infeed Speed change."""
        LOG.info(f"Infeed speed changed to: {value}")
        self.infeed_speed = float(value)
        # self.settings.setData("infeed_speed", self.infeed_speed)

    def on_traverse_speed_changed(self, value):
        """Handle Traverse Speed change."""
        LOG.info(f"Traverse speed changed to: {value}")
        self.traverse_speed = float(value)

    def is_machine_idle(self):
        """Check if the machine is idle and ready for MDI."""
        self.s.poll()  # Update the status

        if self.s.interp_state == linuxcnc.INTERP_IDLE:
            return True
        else:
            return False
        
    def on_disable_infeed_at_limit_checkbox_clicked(self):
        self.disable_infeed_at_limit = not self.disable_infeed_at_limit
        self.disable_infeed_at_limit_checkbox.setChecked(self.disable_infeed_at_limit)

    def on_disable_traverse_at_infeed_limit_checkbox_clicked(self):
        self.disable_traverse_at_infeed_limit = not self.disable_traverse_at_infeed_limit
        self.disable_traverse_at_infeed_limit_checkbox.setChecked(self.disable_traverse_at_infeed_limit)

    def on_enable_traverse_button_clicked(self):
        """Handle run/stop button toggle."""
        self.traverse_enabled = not self.traverse_enabled
        if self.traverse_enabled:
            self.enable_traverse_button.setChecked(True)
        else:
            self.enable_traverse_button.setChecked(False)

    def on_enable_infeed_button_clicked(self):
        """Handle run/stop button toggle."""
        self.infeed_enabled = not self.infeed_enabled
        if self.infeed_enabled:
            self.enable_infeed_button.setChecked(True)
        else:
            self.enable_infeed_button.setChecked(False)

    def on_run_stop_button_clicked(self):
        """Handle run/stop button toggle."""
        self.start_motion = not self.start_motion

        if self.start_motion:

            if not self.is_machine_idle():
                LOG.warn("Machine is busy, cannot enter MDI mode. Not starting.")
                return
            
            self.c.mode(linuxcnc.MODE_MDI)
            self.c.mdi(F"G90")
           
            self.c.wait_complete()

            self.run_stop_button.setText("Running")
            self.run_stop_button.setStyleSheet("background-color: green; color: white;")
            self.run_stop_button.setChecked(True)
            LOG.info("Run/Stop toggled to 'run'.")
            self.timer.start(100)
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
            self.infeed_type = self.infeed_type_combo_box.currentIndex()
            self.infeed_reverse = self.infeed_reverse_combo_box.currentIndex()
            self.disable_infeed_at_limit = bool(self.disable_infeed_at_limit_checkbox.isChecked())
            self.disable_traverse_at_infeed_limit = bool(self.disable_traverse_at_infeed_limit_checkbox.isChecked())

            self.settings.setData("infeed_type", int(self.infeed_type))
            self.settings.setData("infeed_reverse", int(self.infeed_reverse))
            self.settings.setData("disable_infeed_at_limit", int(self.disable_infeed_at_limit))

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
            self.settings.setData("infeed_stepover", self.infeed_stepover)

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

        if self.infeed_enabled:
            if self.infeed_type == 0:
                return True
            elif self.infeed_type == 1 and target == MachineState.TRAVERSING_MAX:
                return True
            elif self.infeed_type == 2 and target == MachineState.TRAVERSING_MIN:
                return True
            return False

    def check_and_reverse_infeed_dir(self, current_pos) -> bool:
        """Invert the sign of the 3D stepover and handle infeed reverse logic."""

        continue_infeeding = True
        at_min_height = current_pos <= self.infeed_limit_min
        at_max_height = current_pos >= self.infeed_limit_max

        if self.infeed_reverse == 0:
            if(at_min_height and self.state == MachineState.INFEEDING_MIN):
                self.last_infeed_direction = MachineState.INFEEDING_MAX
                self.state = MachineState.INFEEDING_MAX
                self.disable_infeed_if_at_limit()
                LOG.debug(f"Infeed reversed: {self.state.name}")
            elif(at_max_height and self.state == MachineState.INFEEDING_MAX):
                self.last_infeed_direction = MachineState.INFEEDING_MIN
                self.state = MachineState.INFEEDING_MIN
                self.disable_infeed_if_at_limit()
                LOG.debug(f"Infeed reversed: {self.state.name}")
            elif(self.state != MachineState.INFEEDING_MAX and self.state != MachineState.INFEEDING_MIN):
                LOG.error(F"Attempting to check and reverse infeed dir while not in an infeed state: {self.state.name}")
                raise Exception(F"Attempting to check and reverse infeed dir while not in an infeed state: {self.state.name}")
    
            continue_infeeding = True
        elif self.infeed_reverse == 1:
            if self.state != MachineState.INFEEDING_MAX:
                self.last_infeed_direction = MachineState.INFEEDING_MAX
                self.state = MachineState.INFEEDING_MAX
            if at_max_height:
                self.move_to(self.infeed_axis, self.infeed_limit_min, self.infeed_speed)
                continue_infeeding = False
                self.disable_infeed_if_at_limit()
        elif self.infeed_reverse == 2:
            if self.state != MachineState.INFEEDING_MIN:
                self.last_infeed_direction = MachineState.INFEEDING_MIN
                self.state = MachineState.INFEEDING_MIN
            if at_min_height:
                self.move_to(self.infeed_axis, self.infeed_limit_max, self.infeed_speed)
                continue_infeeding = False
                self.disable_infeed_if_at_limit()

        return continue_infeeding
    
    def disable_infeed_if_at_limit(self):
        if self.disable_infeed_at_limit:
            self.infeed_enabled = False
            self.enable_infeed_button.setChecked(False)
            continue_infeeding = False

            if self.disable_traverse_at_infeed_limit:
                self.traverse_enabled = False
                self.enable_traverse_button.setChecked(False)

    def move_to(self, axis, pos, speed):
        LOG.debug(F"Move_To: G1 {axis}{pos} F{speed}")
        self.c.mdi(F"G1 {axis}{pos} F{speed}")

    def reverse_traverse(self):
        if self.state == MachineState.TRAVERSING_MAX:
            self.last_traverse_direction = MachineState.TRAVERSING_MAX
            self.state = MachineState.TRAVERSING_MIN
        elif self.state == MachineState.TRAVERSING_MIN:
            self.last_traverse_direction = MachineState.TRAVERSING_MIN
            self.state = MachineState.TRAVERSING_MAX
        else:
            raise Exception(F"Unknown state during reverse {self.state.name}")

    def execute_infeed(self, infeed_dir):
        """Handle the infeed logic at each traverse limit."""
        self.s.poll()
        current_pos = self.get_pos(self.infeed_axis)
        LOG.debug(F"Execute Infeed on {self.infeed_axis.to_str()} from {current_pos} ")
        
        LOG.debug(f"Infeed direction after checking: {infeed_dir}")
        
        self.last_infeed_direction = infeed_dir
        self.last_state = infeed_dir

        LOG.info(F"Infeeding...")
        
        # if we're only infeeding, just move to the limit. eg. dressing the wheel
        if not self.traverse_enabled:
            LOG.debug(F"Traverse not enabled, infeeding to the limit: {infeed_dir}")
            if infeed_dir == MachineState.INFEEDING_MAX:
                self.move_to(self.infeed_axis.name, self.infeed_limit_max, self.infeed_speed)
            elif infeed_dir == MachineState.INFEEDING_MIN:
                self.move_to(self.infeed_axis.name, self.infeed_limit_min, self.infeed_speed)
            return

        infeed_stepover = self.infeed_stepover

        sign = ""

        if infeed_dir == MachineState.INFEEDING_MIN:
            infeed_stepover = -infeed_stepover
            if(current_pos + infeed_stepover < self.infeed_limit_min):
                infeed_stepover = self.infeed_limit_min - current_pos
        elif infeed_dir == MachineState.INFEEDING_MAX:
            if(current_pos + infeed_stepover > self.infeed_limit_max):
                infeed_stepover = self.infeed_limit_max - current_pos        
        
        if round(infeed_stepover, self.get_rounding_tolerance()) == 0:
            #this probably should never happen
            LOG.warn("Infeed tried to infeed with 0 stepover.")
            return
        
        LOG.debug(F"Stepover: {infeed_stepover}")
        
        self.c.mdi(F"G91")
        self.c.mdi(F"G1 {self.infeed_axis.to_str()}{infeed_stepover} F{self.infeed_speed}")
        self.c.mdi(F"G90")

        LOG.debug("Infeed done.")

    def control_loop(self):
        """Main control loop with state tracking and reentrancy protection."""
        if self.control_loop_running:
            LOG.warning("Control loop skipped: Already running.")
            return

        self.control_loop_running = True
        self.s.poll()

        if not self.s.enabled or self.s.estop == linuxcnc.STATE_ESTOP or not self.start_motion or not self.is_on_pin.value:
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
                LOG.info("*************************************")

                if self.state == MachineState.INIT:
                    LOG.info(F"{self.state}")
                    self.state = MachineState.TRAVERSING_START
                    self.exit_control_loop()
                    return
                
                if self.state == MachineState.TRAVERSING_START:
                    LOG.info(F"{self.state}")
                    self.state = self.last_traverse_direction

                    if not self.traverse_enabled:
                        LOG.debug(F"Traverse not enabled, skipping to infeed")
                        self.state = MachineState.INFEEDING_START
                    else:
                        LOG.debug(F"Next State: {self.state}")
                        current_pos = self.et_pos(self.traverse_axis)
                        LOG.debug(F"Current: {current_pos} Limit Max: {self.traverse_limit_max} Limit Min: {self.traverse_limit_min}")
                        if self.state == MachineState.TRAVERSING_MAX and current_pos >= self.traverse_limit_max:
                            self.reverse_traverse()
                            LOG.debug(F"Reversed direction to {self.state} due to max limit")
                        elif self.state == MachineState.TRAVERSING_MIN and current_pos <= self.traverse_limit_min:
                            self.reverse_traverse()
                            LOG.debug(F"Reversed direction to {self.state} due to max limit")

                    self.exit_control_loop()
                    return
                    
                
                elif self.state == MachineState.TRAVERSING_MAX:
                    LOG.info(F"{self.state}")
                    current_pos = self.et_pos(self.traverse_axis)
                    LOG.debug(F"Traverse Axis {self.traverse_axis.to_str()} position {current_pos} Traverse Limit {self.traverse_limit_max}")
                    self.last_traverse_direction = MachineState.TRAVERSING_MAX
                    self.last_state = MachineState.TRAVERSING_MAX
                    
                    if current_pos < self.traverse_limit_max and self.traverse_enabled:
                        self.move_to(self.traverse_axis.to_str(),self.traverse_limit_max, self.traverse_speed)
                        self.exit_control_loop()
                        return
                    else:
                        self.state = MachineState.INFEEDING_START
                        self.exit_control_loop()
                        return

                elif self.state == MachineState.TRAVERSING_MIN:
                    LOG.info(F"{self.state}")
                    current_pos = self.et_pos(self.traverse_axis)
                    LOG.debug(F"Traverse Axis {self.traverse_axis.to_str()} position {current_pos} Traverse Limit {self.traverse_limit_max}")
                    
                    self.last_traverse_direction = MachineState.TRAVERSING_MIN
                    self.last_state = MachineState.TRAVERSING_MIN
                    
                    if current_pos > self.traverse_limit_min  and self.traverse_enabled:
                        self.move_to(self.traverse_axis.to_str(), self.traverse_limit_min, self.traverse_speed)
                        self.exit_control_loop()
                        return
                    else:
                        self.state = MachineState.INFEEDING_START
                        self.exit_control_loop()
                        return
                        
                elif self.state == MachineState.INFEEDING_START:
                    LOG.info(F"{self.state}")
                    current_pos = self.et_pos(self.traverse_axis)
                    if self.infeed_enabled:
                        self.state = self.last_infeed_direction
                        LOG.debug(F"INFEEDING_START switched to last direction {self.state}")
                        if self.state == MachineState.INFEEDING_MAX or self.state == MachineState.INFEEDING_MIN:
                            continue_infeed = self.check_and_reverse_infeed_dir(current_pos)
                            LOG.debug(F"Direction after limits check now {self.state}")
                            if not continue_infeed:
                                LOG.debug(F"Skipping to traverse, continue_infeed was {continue_infeed}")
                                self.state = MachineState.TRAVERSING_START
                        else:
                            raise Exception(F"INFEEDING_START changed to invalid last direction {self.state}")
                    else:
                        LOG.debug("Infeed not enabled, skipping to TRAVERSE_START")
                        self.state = MachineState.TRAVERSING_START

                    
                    self.exit_control_loop()
                    return
                
                elif self.state == MachineState.INFEEDING_MAX:
                    LOG.info(F"{self.state}")
                    
                    self.last_state = MachineState.INFEEDING_MAX

                    if self.should_infeed(self.last_traverse_direction):
                            self.execute_infeed(MachineState.INFEEDING_MAX)
                            self.state = MachineState.TRAVERSING_START
                            self.exit_control_loop()
                            return
                    else:
                        self.state = MachineState.TRAVERSING_START
                        self.exit_control_loop()
                        return
                        
                elif self.state == MachineState.INFEEDING_MIN:
                    LOG.info(F"{self.state}")

                    self.last_state = MachineState.INFEEDING_MIN

                    if self.should_infeed(self.last_traverse_direction):
                            self.execute_infeed(MachineState.INFEEDING_MIN)
                            self.state = MachineState.TRAVERSING_START
                            self.exit_control_loop()
                            return
                    else:
                        self.state = MachineState.TRAVERSING_START
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
