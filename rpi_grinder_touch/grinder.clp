Variables:
    HAL Float Inputs:
        x_min
        x_max
        y_min
        y_max
        z_min
        z_max
        x_position
        y_position
        z_position
        x_speed
        y_speed
        z_speed
        z_crossfeed
        y_downfeed
    HAL Bits:
        enable_x
        enable_y
        enable_z
        stop_z_at_z_limit
        stop_x_at_z_limit
        run_permission
    HAL Integers:
        crossfeed_at
        repeat_at

# Rung 0: Check Start Conditions
IF run_permission THEN
   RUN MainSequence  # Jump to Main Logic Sequence if all conditions are met
ENDIF

# Main Logic Sequence (Rungs 1 and 2 from previous logic)

# Rung 1: X-Axis Traverse to Max and Crossfeed at z_max
IF (x_position <= x_min) AND (crossfeed_at != 2) THEN
   CALL XMove_To_Max               # Move X to max
   WAIT UNTIL (x_position >= x_max)  # Wait until X reaches max

   # Execute Crossfeed at x_max if enabled
   IF enable_z == TRUE THEN
      IF repeat_at == 0 THEN
         CALL ZMove_RepeatType0
      ELSE IF repeat_at == 1 THEN
         CALL ZMove_RepeatType1
      ELSE IF repeat_at == 2 THEN
         CALL ZMove_RepeatType2
      ENDIF
   ENDIF
ENDIF

# Rung 2: X-Axis Traverse to Min and Crossfeed at z_min
IF (x_position >= x_max) AND (crossfeed_at != 3) THEN
   CALL XMove_To_Min               # Move X to min
   WAIT UNTIL (x_position <= x_min)  # Wait until X reaches min

   # Execute Crossfeed at x_min if enabled
   IF enable_z == TRUE THEN
      IF repeat_at == 0 THEN
         CALL ZMove_RepeatType0
      ELSE IF repeat_at == 1 THEN
         CALL ZMove_RepeatType1
      ELSE IF repeat_at == 2 THEN
         CALL ZMove_RepeatType2
      ENDIF
   ENDIF
ENDIF

# Rung 3: Y-Axis Downfeed Triggered by Y Limit Condition
IF enable_y == TRUE THEN
   IF repeat_at == 0 THEN
      IF (y_position <= y_min) OR (y_position >= y_max) THEN
         CALL YDownfeed
      ENDIF
   ELSE IF repeat_at == 1 THEN
      IF y_position >= y_max THEN
         CALL YDownfeed
      ENDIF
   ELSE IF repeat_at == 2 THEN
      IF y_position <= y_min THEN
         CALL YDownfeed
      ENDIF
   ENDIF
ENDIF
