from qtpyvcp.widgets.form_widgets.main_window import VCPMainWindow
from qtpy.QtWidgets import QLineEdit, QPushButton, QGroupBox
from qtpy.QtGui import QDoubleValidator
import linuxcnc
import hal
from qtpy.QtCore import QTimer

# Setup logging
from qtpyvcp.utilities import logger

LOG = logger.getLogger('qtpyvcp.' + __name__)

class MainWindow(VCPMainWindow):
    """Main window class for the VCP."""
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        # Initialize LinuxCNC command, status, and HAL component
        self.c = linuxcnc.command()
        self.s = linuxcnc.stat()
        self.h = hal.component("dynamic_control")

        # Add HAL pin for run/stop
        self.run_stop_pin = hal.Pin("run_stop")

        # Add a QTimer for looping control
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.control_loop)

        # Add variables to keep track of state
        self.control_loop_running = False
        self.current_target = 0  # 0 for Target 1, 1 for Target 2
        self.stopped_mid_cycle = False

        # Add custom initialization logic here
        self.initialize_controls()

    def initialize_controls(self):
        """Initialize custom controls and connect UI elements."""
        # Find the run/stop button from the designer
        self.run_stop_button = self.findChild(QPushButton, "run_stop_button")
        if self.run_stop_button:
            self.run_stop_button.setCheckable(True)
            self.run_stop_button.setChecked(False)
            self.run_stop_button.clicked.connect(self.toggle_run_stop)

        # Validator to allow only numbers with optional decimals
        double_validator = QDoubleValidator()
        double_validator.setDecimals(5)  # Allow up to 5 decimal places
        double_validator.setNotation(QDoubleValidator.StandardNotation)

        # Find QLineEdit widgets for targets and set validators
        self.target1_x = self.findChild(QLineEdit, "target1_x")
        if self.target1_x:
            self.target1_x.setValidator(double_validator)

        self.target1_y = self.findChild(QLineEdit, "target1_y")
        if self.target1_y:
            self.target1_y.setValidator(double_validator)

        self.target1_z = self.findChild(QLineEdit, "target1_z")
        if self.target1_z:
            self.target1_z.setValidator(double_validator)

        self.target2_x = self.findChild(QLineEdit, "target2_x")
        if self.target2_x:
            self.target2_x.setValidator(double_validator)

        self.target2_y = self.findChild(QLineEdit, "target2_y")
        if self.target2_y:
            self.target2_y.setValidator(double_validator)

        self.target2_z = self.findChild(QLineEdit, "target2_z")
        if self.target2_z:
            self.target2_z.setValidator(double_validator)

        # Find QLineEdit widgets for 3D Stepover and set validators
        self.stepover_x = self.findChild(QLineEdit, "stepover_x")
        if self.stepover_x:
            self.stepover_x.setValidator(double_validator)

        self.stepover_y = self.findChild(QLineEdit, "stepover_y")
        if self.stepover_y:
            self.stepover_y.setValidator(double_validator)

        self.stepover_z = self.findChild(QLineEdit, "stepover_z")
        if self.stepover_z:
            self.stepover_z.setValidator(double_validator)

        # Find the Save button
        self.save_button = self.findChild(QPushButton, "save_button")
        if self.save_button:
            self.save_button.clicked.connect(self.save_target_stepover)

    def save_target_stepover(self):
        """Save the target and 3D stepover values."""
        try:
            # Get the values from the target text boxes
            target1_x_val = float(self.target1_x.text())
            target1_y_val = float(self.target1_y.text())
            target1_z_val = float(self.target1_z.text())

            target2_x_val = float(self.target2_x.text())
            target2_y_val = float(self.target2_y.text())
            target2_z_val = float(self.target2_z.text())

            # Get the values from the 3D stepover text boxes
            stepover_x_val = float(self.stepover_x.text())
            stepover_y_val = float(self.stepover_y.text())
            stepover_z_val = float(self.stepover_z.text())

            # Update the HAL component variables for targets
            self.h["target-x1"] = target1_x_val
            self.h["target-y1"] = target1_y_val
            self.h["target-z1"] = target1_z_val

            self.h["target-x2"] = target2_x_val
            self.h["target-y2"] = target2_y_val
            self.h["target-z2"] = target2_z_val

            # Update the HAL component variables for 3D stepover
            self.h["stepover-x"] = stepover_x_val
            self.h["stepover-y"] = stepover_y_val
            self.h["stepover-z"] = stepover_z_val

            LOG.info("Target and 3D stepover values saved successfully.")
        
        except ValueError:
            LOG.error("Invalid input: Please enter numeric values for targets and stepover.")

    def toggle_run_stop(self):
        """Toggle the internal run/stop variable."""
        self.h["run_stop"] = not self.h["run_stop"]

        if self.h["run_stop"]:
            self.run_stop_button.setText("Running")
            self.run_stop_button.setStyleSheet("background-color: green; color: white;")
            LOG.info("Run/Stop toggled to 'run'.")
            self.timer.start(100)  # Start the control loop timer
        else:
            self.run_stop_button.setText("Stopped")
            self.run_stop_button.setStyleSheet("")
            self.stopped_mid_cycle = True
            self.timer.stop()
            LOG.info("Run/Stop toggled to 'stop'.")

    def handle_run_stop(self):
        """Start or stop the control loop based on the run_stop signal."""
        if self.h["run_stop"]:
            LOG.info("Run/Stop signal activated, starting the control loop...")
            self.timer.start(100)  # Start the control loop timer
        else:
            LOG.info("Run/Stop signal deactivated, stopping the control loop...")
            self.timer.stop()  # Stop the control loop timer

    def control_loop(self):
        """Main control loop with state tracking and reentrancy protection."""
        if self.control_loop_running:
            LOG.warning("Control loop skipped: Already running.")
            return

        self.control_loop_running = True
        self.s.poll()

        if not self.s.enabled or self.s.estop or not self.h["run_stop"]:
            self.timer.stop()
            LOG.info("Control loop stopped: Machine not ready.")
            self.control_loop_running = False
            self.stopped_mid_cycle = True
            return

        # Fetch current target positions and 3D stepover from HAL signals
        x1 = self.h["target-x1"]
        y1 = self.h["target-y1"]
        z1 = self.h["target-z1"]
        x2 = self.h["target-x2"]
        y2 = self.h["target-y2"]
        z2 = self.h["target-z2"]

        stepover_x = self.h["stepover-x"]
        stepover_y = self.h["stepover-y"]
        stepover_z = self.h["stepover-z"]

        try:
            if self.s.interp_state == linuxcnc.INTERP_IDLE:
                if self.current_target == 0:  # Move to Target 1
                    self.c.mdi(f"G1 X{x1} Y{y1} Z{z1} F500")
                    self.c.wait_complete()

                    self.current_target = 1

                elif self.current_target == 1:  # Move to Target 2
                    self.c.mdi(f"G1 X{x2} Y{y2} Z{z2} F500")
                    self.c.wait_complete()

                    # Update positions for the next pass with 3D stepover
                    self.h["target-x1"] = x1 - stepover_x
                    self.h["target-y1"] = y1 - stepover_y
                    self.h["target-z1"] = z1 - stepover_z

                    self.h["target-x2"] = x2 - stepover_x
                    self.h["target-y2"] = y2 - stepover_y
                    self.h["target-z2"] = z2 - stepover_z

                    self.current_target = 0

        except linuxcnc.error as e:
            LOG.error(f"Error in control loop: {e}")

        self.control_loop_running = False
