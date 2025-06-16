# import sys
from PyQt6.QtWidgets import QLineEdit, QPushButton, QComboBox, QDoubleSpinBox, QSpinBox, QCheckBox, QWidget

import linuxcnc
# from hal_glib import GStat

# from python.axis import Axis
# from python.grinderhal import GrinderHal

from functools import partial

def startup(parent):
    print("Started")
    initialize_controls(parent)
    # parent.x_max_here_pb.clicked.connect(partial(test))
    
    # parent.setFixedSize(1920, 1200)
    # parent.setFixedSize(1920, 1000)
    # parent.showFullScreen()
    # try:
    #     parent.grinder_window = GrinderWindow(parent)
    # except Exception as e:
    #     print(e)
    #     sys.exit(1)
    #     return
    
def start():
    if not GrinderHal.get_hal("is_running"):

        if bool(GrinderHal.get_hal("downfeed_now")):
            GrinderHal.set_hal("downfeed_now", False) # just make sure we don't have an unintended pending downfeed
    #start the backend
    GrinderHal.set_hal("is_running", True)

def stop():
    GrinderHal.set_hal("is_running", False)

def initialize_controls(parent):
    """Initialize custom controls and connect UI elements."""

    parent.x_max_here_pb.clicked.connect(lambda: on_set_limit_clicked("x_max", parent.x_max_edit))
    parent.x_min_here_pb.clicked.connect(lambda: on_set_limit_clicked("x_min", parent.x_min_edit))
    parent.z_max_here_pb.clicked.connect(lambda: on_set_limit_clicked("z_max", parent.z_max_edit))
    parent.z_min_here_pb.clicked.connect(lambda: on_set_limit_clicked("z_min", parent.z_min_edit))
    parent.y_max_here_pb.clicked.connect(lambda: on_set_limit_clicked("y_max", parent.y_max_edit))
    parent.y_min_here_pb.clicked.connect(lambda: on_set_limit_clicked("y_min", parent.y_min_edit))

    parent.stop_at_z_limit_pb.clicked.connect(on_value_changed)

    parent.enable_x_pb.clicked.connect(on_value_changed)
    parent.enable_y_pb.clicked.connect(on_value_changed)
    parent.enable_z_pb.clicked.connect(on_value_changed)

    parent.downfeed_now_pb.clicked.connect(lambda: GrinderHal.set_hal("downfeed_now", True))

    parent.x_max_edit.textChanged.connect(on_value_changed)
    parent.x_min_edit.textChanged.connect(on_value_changed)
    parent.z_max_edit.textChanged.connect(on_value_changed)
    parent.z_min_edit.textChanged.connect(on_value_changed)
    parent.y_max_edit.textChanged.connect(on_value_changed)
    parent.y_min_edit.textChanged.connect(on_value_changed)

    parent.x_speed_sb.valueChanged.connect(on_value_changed)
    parent.y_speed_sb.valueChanged.connect(on_value_changed)
    parent.z_speed_sb.valueChanged.connect(on_value_changed)

    parent.crossfeed_at_cb.currentIndexChanged.connect(on_value_changed)
    parent.repeat_at_cb.currentIndexChanged.connect(on_value_changed)

    parent.z_crossfeed_edit.textChanged.connect(on_value_changed)
    parent.y_downfeed_edit.textChanged.connect(on_value_changed)

    parent.run_stop_pb.clicked.connect(on_run_stop_clicked)

def on_run_stop_clicked():
    if GrinderHal.get_hal("is_running"):
        stop()
    else:
        start()

def on_set_limit_clicked(source, field):
    # axis_name = base_name.removesuffix("_min")
    # axis_name = axis_name.removesuffix("_max")
    # axis = Axis.from_str(axis_name)
    print("fired")
    print(source.text)
    field.setText(str(source.text))
    GrinderHal.save()

def on_value_changed(self):
    save_settings()

def save_settings():
    GrinderHal.save_settings()


    
