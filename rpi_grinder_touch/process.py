import linuxcnc
import time
import traceback

status = linuxcnc.stat()
c = linuxcnc.command()

def print_mode():
        
        status.poll()
        if status.task_mode == linuxcnc.MODE_MANUAL:
            print("Current mode: Manual")
        elif status.task_mode == linuxcnc.MODE_AUTO:
            print("Current mode: Auto")
        elif status.task_mode == linuxcnc.MODE_MDI:
            print("Current mode: MDI")


try:
    print("EXAMPLE STARTED")
    time.sleep(10) #give linuxcnc enough time to start
    while True:

        # the thread will be terminated by the outside process, but just in case this can stop it faster:

        print("Loop")
        print_mode()
        time.sleep(0.01)

        c.mode(linuxcnc.MODE_MDI)
        c.wait_complete()
        print_mode()
        c.mdi("G1 X0.1 F1000")
        c.wait_complete()
        print_mode()
        c.mdi("G1 X0 F1000")
        c.wait_complete()

        print_mode()

except KeyboardInterrupt:
    print("Motion controller stopped.")
    #GLib.MainLoop().stop()
    raise SystemExit
except Exception:
    print(traceback.format_exc())

