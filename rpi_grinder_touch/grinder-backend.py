import hal
import linuxcnc
import time

import traceback

# Initialize HAL and LinuxCNC
h = hal.component("grinder")
c = linuxcnc.command()

# Define HAL pins
h.newpin("x_min", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("x_max", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("y_min", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("y_max", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("z_min", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("z_max", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("x_speed", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("y_speed", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("z_speed", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("x_position", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("y_position", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("z_position", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("z_crossfeed", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("y_downfeed", hal.HAL_FLOAT, hal.HAL_IN)
h.newpin("enable_x", hal.HAL_BIT, hal.HAL_IN)
h.newpin("enable_y", hal.HAL_BIT, hal.HAL_IN)
h.newpin("enable_z", hal.HAL_BIT, hal.HAL_IN)
h.newpin("run_permission", hal.HAL_BIT, hal.HAL_IN)
h.newpin("run_stop", hal.HAL_BIT, hal.HAL_IN)
h.newpin("stop_x_at_z_limit", hal.HAL_BIT, hal.HAL_IN)
h.newpin("stop_z_at_z_limit", hal.HAL_BIT, hal.HAL_IN)
h.newpin("crossfeed_at", hal.HAL_S32, hal.HAL_IN)
h.newpin("repeat_at", hal.HAL_S32, hal.HAL_IN)

# Ready HAL component
h.ready()

print("GRINDER READY")

# Function to call G-code subroutines
def call_subroutine(subroutine_name):
    c.mode(linuxcnc.MODE_MDI)
    c.wait_complete()
    c.mdi(f"o<{subroutine_name}> call")
    print("sub called")

# Main logic sequence
def main_sequence():
    while True:
        time.sleep(1)
        if not h["run_permission"]:
            time.sleep(0.2)
            continue

        x_pos = h["x_position"]
        y_pos = h["y_position"]
        z_pos = h["z_position"]
        x_min = h["x_min"]
        x_max = h["x_max"]
        y_min = h["y_min"]
        y_max = h["y_max"]
        z_min = h["z_min"]
        z_max = h["z_max"]
        crossfeed_at = h["crossfeed_at"]
        repeat_at = h["repeat_at"]

        # X-axis traverse to max
        if x_pos <= x_min and crossfeed_at != 2:
            call_subroutine("XMove_To_Max")
            while h["x_position"] < x_max:
                time.sleep(0.1)

            # Crossfeed at X max
            if h["enable_z"]:
                if repeat_at == 0:
                    call_subroutine("ZMove_RepeatType0")
                elif repeat_at == 1:
                    call_subroutine("ZMove_RepeatType1")
                elif repeat_at == 2:
                    call_subroutine("ZMove_RepeatType2")

        # X-axis traverse to min
        if x_pos >= x_max and crossfeed_at != 3:
            call_subroutine("XMove_To_Min")
            while h["x_position"] > x_min:
                time.sleep(0.1)

            # Crossfeed at X min
            if h["enable_z"]:
                if repeat_at == 0:
                    call_subroutine("ZMove_RepeatType0")
                elif repeat_at == 1:
                    call_subroutine("ZMove_RepeatType1")
                elif repeat_at == 2:
                    call_subroutine("ZMove_RepeatType2")

        # Y-axis downfeed
        if h["enable_y"]:
            if repeat_at == 0 and (y_pos <= y_min or y_pos >= y_max):
                call_subroutine("YDownfeed")
            elif repeat_at == 1 and y_pos >= y_max:
                call_subroutine("YDownfeed")
            elif repeat_at == 2 and y_pos <= y_min:
                call_subroutine("YDownfeed")

        time.sleep(0.05)

# Run the main sequence
try:
    main_sequence()
except KeyboardInterrupt:
    print("Motion controller stopped.")
except Exception:
    print(traceback.format_exc())
