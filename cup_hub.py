"""
CUP HUB

Responsible for:
- Moving cup between stations
- Detecting station arrival

Later this file will contain:
- Drive motor logic
- Colour sensor logic
"""

from usys import stdin, stdout
from uselect import poll
from pybricks.tools import wait


# ============================================================
# CONFIGURATION
# ============================================================

# CHANGE THIS TO CHANGE MOVEMENT TIME
MOVE_TIME_MS = 3000


# ============================================================
# STATION FUNCTIONS
# ============================================================

def move_to_station(station_name):

    stdout.write(f"MOVING:{station_name}\n")

    # --------------------------------------------------------
    # FUTURE MOVEMENT LOGIC GOES HERE
    # --------------------------------------------------------
    #
    # Example future logic:
    #
    # drive_motor.run(200)
    #
    # while color_sensor.color() != target_colour:
    #     wait(10)
    #
    # drive_motor.stop()
    #
    # --------------------------------------------------------

    wait(MOVE_TIME_MS)

    stdout.write(f"ARRIVED:{station_name}\n")


# ============================================================
# INPUT SETUP
# ============================================================

keyboard = poll()
keyboard.register(stdin)


# ============================================================
# MAIN LOOP
# ============================================================

while True:

    stdout.write("READY\n")

    while not keyboard.poll(0):
        wait(10)

    received_message = stdin.readline().strip()

    # ========================================================
    # MOVE COMMAND
    # ========================================================

    if received_message.startswith("MOVE:"):

        station_name = received_message.split(":")[1]

        move_to_station(station_name)

    # ========================================================
    # SHUTDOWN COMMAND
    # ========================================================

    elif received_message == "bye":

        stdout.write("CUP_HUB_DONE\n")

        break

    else:

        stdout.write("UNKNOWN_COMMAND\n")