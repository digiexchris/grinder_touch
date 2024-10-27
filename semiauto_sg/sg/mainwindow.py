from qtpyvcp.widgets.form_widgets.main_window import VCPMainWindow
from qtpy.QtWidgets import QLineEdit, QPushButton, QComboBox
from qtpy.QtGui import QDoubleValidator
import linuxcnc
import hal
import numpy as np
from qtpy.QtCore import QTimer, QEventLoop

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

        # Local variables for traverse limits and stepover
        self.traverse_left_limit = np.zeros(4)
        self.traverse_right_limit = np.zeros(4)
        self.stepover = np.zeros(4)


        self.infeed_limit_min = np.array([0,0,0])
        self.infeed_limit_max = np.array([0,0,0])
        self.traverse_limit_min = np.array([0,0,0])
        self.traverse_limit_max = np.array([0,0,0])

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

        # Add HAL pin for run/stop
        self.start_motion = False

        # Add a QTimer for looping control
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.control_loop)

        # Add variables to keep track of state
        self.control_loop_running = False
        self.current_target = 0  # 0 for Traverse Left, 1 for Traverse Right
        self.stopped_mid_cycle = False

        # Add custom initialization logic here
        self.initialize_controls()

    def initialize_controls(self):
        """Initialize custom controls and connect UI elements."""
        # Validator to allow only numbers with optional decimals
        double_validator = QDoubleValidator()
        double_validator.setDecimals(5)
        double_validator.setNotation(QDoubleValidator.StandardNotation)

        # Traverse tab
        self.traverse_limit_min_x = self.findChild(QLineEdit, "traverse_limit_min_x")
        if self.traverse_limit_min_x:
            self.traverse_limit_min_x.setValidator(double_validator)
            self.traverse_limit_min_x.editingFinished.connect(self.on_traverse_limit_min_x_changed)

        self.traverse_limit_min_y = self.findChild(QLineEdit, "traverse_limit_min_y")
        if self.traverse_limit_min_y:
            self.traverse_limit_min_y.setValidator(double_validator)
            self.traverse_limit_min_y.editingFinished.connect(self.on_traverse_limit_min_y_changed)

        self.traverse_limit_min_z = self.findChild(QLineEdit, "traverse_limit_min_z")
        if self.traverse_limit_min_z:
            self.traverse_limit_min_z.setValidator(double_validator)
            self.traverse_limit_min_z.editingFinished.connect(self.on_traverse_limit_min_z_changed)

        self.traverse_limit_max_x = self.findChild(QLineEdit, "traverse_limit_max_x")
        if self.traverse_limit_max_x:
            self.traverse_limit_max_x.setValidator(double_validator)
            self.traverse_limit_max_x.editingFinished.connect(self.on_traverse_limit_max_x_changed)

        self.traverse_limit_max_y = self.findChild(QLineEdit, "traverse_limit_max_y")
        if self.traverse_limit_max_y:
            self.traverse_limit_max_y.setValidator(double_validator)
            self.traverse_limit_max_y.editingFinished.connect(self.on_traverse_limit_max_y_changed)

        self.traverse_limit_max_z = self.findChild(QLineEdit, "traverse_limit_max_z")
        if self.traverse_limit_max_z:
            self.traverse_limit_max_z.setValidator(double_validator)
            self.traverse_limit_max_z.editingFinished.connect(self.on_traverse_limit_max_z_changed)

        self.save_traverse = self.findChild(QPushButton, "save_traverse")
        if self.save_traverse:
            self.save_traverse.clicked.connect(self.on_save_traverse_clicked)

        self.cancel_edit_traverse = self.findChild(QPushButton, "cancel_edit_traverse")
        if self.cancel_edit_traverse:
            self.cancel_edit_traverse.clicked.connect(self.on_cancel_edit_traverse_clicked)

        self.traverse_speed = self.findChild(QSpinBox, "traverse_speed")
        if self.traverse_speed:
            self.traverse_speed.valueChanged.connect(self.on_traverse_speed_changed)

        self.save_traverse_speed = self.findChild(QPushButton, "save_traverse_speed")
        if self.save_traverse_speed:
            self.save_traverse_speed.clicked.connect(self.on_save_traverse_speed_clicked)

        self.cancel_edit_traverse_speed = self.findChild(QPushButton, "cancel_edit_traverse_speed")
        if self.cancel_edit_traverse_speed:
            self.cancel_edit_traverse_speed.clicked.connect(self.on_cancel_edit_traverse_speed_clicked)




        # Infeed tab
        self.infeed_min_x = self.findChild(QLineEdit, "infeed_limit_min_x")
        if self.infeed_min_x:
            self.infeed_min_x.setValidator(double_validator)
            self.infeed_min_x.editingFinished.connect(self.on_infeed_min_x_changed)

        self.infeed_min_y = self.findChild(QLineEdit, "infeed_limit_min_y")
        if self.infeed_min_y:
            self.infeed_min_y.setValidator(double_validator)
            self.infeed_min_y.editingFinished.connect(self.on_infeed_min_y_changed)

        self.infeed_min_z = self.findChild(QLineEdit, "infeed_limit_min_z")
        if self.infeed_min_z:
            self.infeed_min_z.setValidator(double_validator)
            self.infeed_min_z.editingFinished.connect(self.on_infeed_min_z_changed)

        self.infeed_max_x = self.findChild(QLineEdit, "infeed_limit_max_x")
        if self.infeed_max_x:
            self.infeed_max_x.setValidator(double_validator)
            self.infeed_max_x.editingFinished.connect(self.on_infeed_max_x_changed)

        self.infeed_max_y = self.findChild(QLineEdit, "infeed_limit_max_y")
        if self.infeed_max_y:
            self.infeed_max_y.setValidator(double_validator)
            self.infeed_max_y.editingFinished.connect(self.on_infeed_max_y_changed)

        self.infeed_max_z = self.findChild(QLineEdit, "infeed_limit_max_z")
        if self.infeed_max_z:
            self.infeed_max_z.setValidator(double_validator)
            self.infeed_max_z.editingFinished.connect(self.on_infeed_max_z_changed)

        self.stepover_x = self.findChild(QLineEdit, "stepover_x")
        if self.stepover_x:
            self.stepover_x.setValidator(double_validator)
            self.stepover_x.editingFinished.connect(self.on_stepover_x_changed)

        self.stepover_y = self.findChild(QLineEdit, "stepover_y")
        if self.stepover_y:
            self.stepover_y.setValidator(double_validator)
            self.stepover_y.editingFinished.connect(self.on_stepover_y_changed)

        self.stepover_z = self.findChild(QLineEdit, "stepover_z")
        if self.stepover_z:
            self.stepover_z.setValidator(double_validator)
            self.stepover_z.editingFinished.connect(self.on_stepover_z_changed)

        self.save_infeed = self.findChild(QPushButton, "save_infeed")
        if self.save_infeed:
            self.save_infeed.clicked.connect(self.on_save_infeed_clicked)

        self.cancel_edit_infeed = self.findChild(QPushButton, "cancel_edit_infeed")
        if self.cancel_edit_infeed:
            self.cancel_edit_infeed.clicked.connect(self.on_cancel_edit_infeed_clicked)

        self.infeed_speed = self.findChild(QSpinBox, "infeed_speed")
        if self.infeed_speed:
            self.infeed_speed.valueChanged.connect(self.on_infeed_speed_changed)

        self.cancel_edit_infeed_speed = self.findChild(QPushButton, "cancel_edit_infeed_speed")
        if self.cancel_edit_infeed_speed:
            self.cancel_edit_infeed_speed.clicked.connect(self.on_cancel_edit_infeed_speed_clicked)

        self.save_infeed_speed = self.findChild(QPushButton, "save_infeed_speed")
        if self.save_infeed_speed:
            self.save_infeed_speed.clicked.connect(self.on_save_infeed_speed_clicked)


        # Run/Stop Button
        self.run_stop_button = self.findChild(QPushButton, "run_stop_button")
        if self.run_stop_button:
            self.run_stop_button.setCheckable(True)
            self.run_stop_button.setChecked(False)
            self.run_stop_button.clicked.connect(self.on_run_stop_button_clicked)

        # Options Tab
        self.infeed_type_combo_box = self.findChild(QComboBox, "infeed_type")
        if self.infeed_type_combo_box:
            self.infeed_type_combo_box.currentIndexChanged.connect(self.on_infeed_type_change)
            self.on_infeed_type_change()  # Set initial index

        self.infeed_reverse_combo_box = self.findChild(QComboBox, "infeed_reverse")
        if self.infeed_reverse_combo_box:
            self.infeed_reverse_combo_box.currentIndexChanged.connect(self.on_infeed_reverse_change)
            self.on_infeed_reverse_change()  # Set initial index


        def on_save_infeed_clicked(self):
            """Handle Save Infeed button click."""
            LOG.info("Save Infeed button clicked.")
            self.save_infeed_limits()

        def on_cancel_edit_infeed_clicked(self):
            """Handle Cancel Infeed button click."""
            LOG.info("Cancel Infeed button clicked.")
            # Implement cancel functionality, e.g., reset fields or revert changes
            self.reset_infeed_fields()

        def save_infeed_limits(self):
            """Save Infeed limits."""
            try:
                self.infeed_limit_min = np.array([
                    float(self.infeed_limit_min_x.text()),
                    float(self.infeed_limit_min_y.text()),
                    float(self.infeed_limit_min_z.text())
                ])
                self.infeed_limit_max = np.array([
                    float(self.infeed_limit_max_x.text()),
                    float(self.infeed_limit_max_y.text()),
                    float(self.infeed_limit_max_z.text())
                ])
                LOG.info("Infeed limits saved successfully.")
            except ValueError:
                LOG.error("Invalid input: Please enter numeric values for infeed limits.")

        def reset_infeed_fields(self):
            """Reset Infeed limit fields to previous values."""
            self.infeed_limit_min_x.setText(str(self.infeed_limit_min[0]))
            self.infeed_limit_min_y.setText(str(self.infeed_limit_min[1]))
            self.infeed_limit_min_z.setText(str(self.infeed_limit_min[2]))
            self.infeed_limit_max_x.setText(str(self.infeed_limit_max[0]))
            self.infeed_limit_max_y.setText(str(self.infeed_limit_max[1]))
            self.infeed_limit_max_z.setText(str(self.infeed_limit_max[2]))
            LOG.info("Infeed limit fields reset to previous values.")


        def on_infeed_speed_changed(self, value):
            """Handle Infeed Speed change."""
            LOG.info(f"Infeed speed changed to: {value}")
            self.set_infeed_speed(value)

        def set_infeed_speed(self, speed):
            """Set infeed speed in the system."""
            LOG.info(f"Setting infeed speed to: {speed}")
            self.c.speed = speed

        def reset_infeed_speed(self):
            """Reset Infeed speed to previous value."""
            self.infeed_speed.setValue(int(self.current_infeed_speed))
            LOG.info("Infeed speed reset to previous value.")



        def on_traverse_speed_changed(self, value):
            """Handle Traverse Speed change."""
            LOG.info(f"Traverse speed changed to: {value}")
            self.set_traverse_speed(value)

        def set_traverse_speed(self, speed):
            """Set traverse speed in the system."""
            # Implement functionality to set speed
            LOG.info(f"Setting traverse speed to: {speed}")
            self.c.speed = speed

        def on_save_traverse_speed_clicked(self):
            """Handle Save Traverse Speed button click."""
            LOG.info("Save Traverse Speed button clicked.")
            speed = self.traverse_speed.value()
            self.set_traverse_speed(speed)

        def on_cancel_edit_traverse_speed_clicked(self):
            """Handle Cancel Traverse Speed button click."""
            LOG.info("Cancel Traverse Speed button clicked.")
            # Implement cancel functionality, e.g., reset to previous speed
            self.reset_traverse_speed()

        def reset_traverse_speed(self):
            """Reset Traverse speed to previous value."""
            self.traverse_speed.setValue(int(self.current_traverse_speed))
            LOG.info("Traverse speed reset to previous value.")




        def on_cancel_edit_traverse_clicked(self):
            """Handle Cancel Traverse button click."""
            LOG.info("Cancel Traverse button clicked.")
            # Implement cancel functionality, e.g., reset fields or revert changes
            self.reset_traverse_fields()

        def reset_traverse_fields(self):
            """Reset Traverse limit fields to previous values."""
            self.traverse_limit_min_x.setText(str(self.traverse_limit_min[0]))
            self.traverse_limit_min_y.setText(str(self.traverse_limit_min[1]))
            self.traverse_limit_min_z.setText(str(self.traverse_limit_min[2]))
            self.traverse_limit_max_x.setText(str(self.traverse_limit_max[0]))
            self.traverse_limit_max_y.setText(str(self.traverse_limit_max[1]))
            self.traverse_limit_max_z.setText(str(self.traverse_limit_max[2]))
            LOG.info("Traverse fields reset to previous values.")

    def on_infeed_type_change(self, index):
        """Handle infeed type change event."""
        self.infeed_type = index
        LOG.info(f"Infeed type changed to index: {index}")

    def on_infeed_reverse_change(self, index):
        """Handle infeed reverse change event."""
        self.infeed_reverse = index
        LOG.info(f"Infeed reverse changed to index: {index}")

    def on_run_stop_button_clicked(self):
        """Handle run/stop button toggle."""
        self.run_stop = not self.run_stop

        if self.run_stop:
            self.run_stop_button.setText("Running")
            self.run_stop_button.setStyleSheet("background-color: green; color: white;")
            self.run_stop_button.setChecked(True)
            LOG.info("Run/Stop toggled to 'run'.")
            self.timer.start(100)
        else:
            self.run_stop_button.setText("Stopped")
            self.run_stop_button.setStyleSheet("")
            self.run_stop_button.setChecked(False)
            self.stopped_mid_cycle = True
            self.timer.stop()
            LOG.info("Run/Stop toggled to 'stop'.")

    def on_save_traverse_clicked(self):
        """Handle save button click."""
        self.save_traverse_limits()

    def save_traverse_limits(self):
        """Stop movement, wait for idle, then save the traverse limits and 3D stepover values."""
        self.stop()  # Stops the timer and sets run_stop to False

        try:
            self.traverse_left_limit = np.array([
                float(self.traverse_limit_max_x.text()), 
                float(self.traverse_limit_min_y.text()), 
                float(self.traverse_limit_min_z.text())
            ])
            self.traverse_right_limit = np.array([
                float(self.traverse_limit_max_x.text()), 
                float(self.traverse_limit_max_y.text()), 
                float(self.traverse_limit_max_z.text())
            ])
            self.stepover = np.array([
                float(self.stepover_x.text()), 
                float(self.stepover_y.text()), 
                float(self.stepover_z.text())
            ])

            LOG.info("Traverse limits and 3D stepover values saved successfully.")

        except ValueError:
            LOG.error("Invalid input: Please enter numeric values for traverse limits and stepover.")

    # Newly generated on_ functions for QLineEdit changes
    def on_traverse_limit_min_x_changed(self):
        """Handle changes to traverse_limit_min_x."""
        value = self.traverse_limit_min_x.text()
        LOG.info(f"Traverse Limit Min X changed to: {value}")
        # Add validation or processing logic here

    def on_traverse_limit_min_y_changed(self):
        """Handle changes to traverse_limit_min_y."""
        value = self.traverse_limit_min_y.text()
        LOG.info(f"Traverse Limit Min Y changed to: {value}")
        # Add validation or processing logic here

    def on_traverse_limit_min_z_changed(self):
        """Handle changes to traverse_limit_min_z."""
        value = self.traverse_limit_min_z.text()
        LOG.info(f"Traverse Limit Min Z changed to: {value}")
        # Add validation or processing logic here

    def on_traverse_limit_max_x_changed(self):
        """Handle changes to traverse_limit_max_x."""
        value = self.traverse_limit_max_x.text()
        LOG.info(f"Traverse Limit Max X changed to: {value}")
        # Add validation or processing logic here

    def on_traverse_limit_max_y_changed(self):
        """Handle changes to traverse_limit_max_y."""
        value = self.traverse_limit_max_y.text()
        LOG.info(f"Traverse Limit Max Y changed to: {value}")
        # Add validation or processing logic here

    def on_traverse_limit_max_z_changed(self):
        """Handle changes to traverse_limit_max_z."""
        value = self.traverse_limit_max_z.text()
        LOG.info(f"Traverse Limit Max Z changed to: {value}")
        # Add validation or processing logic here

    def on_infeed_min_x_changed(self):
        """Handle changes to infeed_min_x."""
        value = self.infeed_min_x.text()
        LOG.info(f"Infeed Min X changed to: {value}")
        # Add validation or processing logic here

    def on_infeed_min_y_changed(self):
        """Handle changes to infeed_min_y."""
        value = self.infeed_min_y.text()
        LOG.info(f"Infeed Min Y changed to: {value}")
        # Add validation or processing logic here

    def on_infeed_min_z_changed(self):
        """Handle changes to infeed_min_z."""
        value = self.infeed_min_z.text()
        LOG.info(f"Infeed Min Z changed to: {value}")
        # Add validation or processing logic here

    def on_infeed_max_x_changed(self):
        """Handle changes to infeed_max_x."""
        value = self.infeed_max_x.text()
        LOG.info(f"Infeed Max X changed to: {value}")
        # Add validation or processing logic here

    def on_infeed_max_y_changed(self):
        """Handle changes to infeed_max_y."""
        value = self.infeed_max_y.text()
        LOG.info(f"Infeed Max Y changed to: {value}")
        # Add validation or processing logic here

    def on_infeed_max_z_changed(self):
        """Handle changes to infeed_max_z."""
        value = self.infeed_max_z.text()
        LOG.info(f"Infeed Max Z changed to: {value}")
        # Add validation or processing logic here

    def on_stepover_x_changed(self):
        """Handle changes to stepover_x."""
        value = self.stepover_x.text()
        LOG.info(f"Stepover X changed to: {value}")
        # Add validation or processing logic here

    def on_stepover_y_changed(self):
        """Handle changes to stepover_y."""
        value = self.stepover_y.text()
        LOG.info(f"Stepover Y changed to: {value}")
        # Add validation or processing logic here

    def on_stepover_z_changed(self):
        """Handle changes to stepover_z."""
        value = self.stepover_z.text()
        LOG.info(f"Stepover Z changed to: {value}")
        # Add validation or processing logic here

    def stop(self):
        """Start or stop the control loop based on the run_stop signal."""
        self.timer.stop()
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
        elif self.infeed_type == 1 and target == 1:
            return True
        elif self.infeed_type == 2 and target == 0:
            return True
        return False

    def reverse_infeed(self):
        """Invert the sign of the 3D stepover and handle infeed reverse logic."""
        if self.infeed_reverse == 0:
            # Reverse stepover
            self.stepover = -self.stepover

            # Update UI elements
            self.stepover_x.setText(str(self.stepover[0]))
            self.stepover_y.setText(str(self.stepover[1]))
            self.stepover_z.setText(str(self.stepover[2]))

            LOG.info(f"Stepover reversed: {self.stepover}")
        elif self.infeed_reverse == 1:
            # Move to minimum limits
            limit = np.array([self.infeed_min_x.text(), self.infeed_min_y.text(), self.infeed_min_z.text()], dtype=float)
            self.move_to_infeed_limit(limit, direction='min')
        elif self.infeed_reverse == 2:
            # Move to maximum limits
            limit = np.array([self.infeed_max_x.text(), self.infeed_max_y.text(), self.infeed_max_z.text()], dtype=float)
            self.move_to_infeed_limit(limit, direction='max')

    def move_to_infeed_limit(self, limit, direction):
        """Move to specified limit position (min or max)."""
        self.s.poll()
        current_pos = np.array(self.s.actual_position[:3])

        if direction == 'min':
            target_pos = current_pos + limit
        else:
            target_pos = current_pos - limit

        self.c.mdi(f"G1 X{target_pos[0]} Y{target_pos[1]} Z{target_pos[2]} F500")
        self.c.wait_complete()

    def move_to(self, pos):
        self.c.mdi(f"G1 X{pos[0]} Y{pos[1]} Z{pos[2]} F500")
        self.c.wait_complete()

    def execute_infeed(self):
        """Handle the infeed logic at each traverse limit."""
        self.s.poll()
        current_pos = np.array(self.s.actual_position[:3])

        if self.current_target == 0 and self.should_infeed(0):
            if np.all(current_pos <= self.traverse_left_limit):
                self.reverse_infeed()
            else:
                self.traverse_left_limit += self.stepover
                self.traverse_right_limit += self.stepover
                self.move_to(self.traverse_left_limit)

        elif self.current_target == 1 and self.should_infeed(1):
            if np.all(current_pos >= self.traverse_right_limit):
                self.reverse_infeed()
            else:
                self.traverse_left_limit += self.stepover
                self.traverse_right_limit += self.stepover
                self.move_to(self.traverse_right_limit)

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

        try:
            if self.s.interp_state == linuxcnc.INTERP_IDLE:
                if self.current_target == 0:
                    self.move_to(self.traverse_left_limit)
                    self.execute_infeed()
                    self.current_target = 1

                elif self.current_target == 1:
                    self.move_to(self.traverse_right_limit)
                    self.execute_infeed()
                    self.current_target = 0

        except linuxcnc.error as e:
            LOG.error(f"Error in control loop: {e}")

        self.control_loop_running = False

    def wait_for_idle(self):
        """Wait until the machine becomes idle."""
        while True:
            self.s.poll()
            if self.s.interp_state == linuxcnc.INTERP_IDLE:
                break
            QEventLoop().processEvents()
