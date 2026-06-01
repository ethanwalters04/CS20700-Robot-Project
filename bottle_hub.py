"""
BOTTLE HUB

Responsible for:
- Bottle dispensing
- Mixer control

Later this file will contain:
- Bottle motors
- Mixer lift motor
- Mixer spin motor
"""

from usys import stdin, stdout
from uselect import poll
from pybricks.tools import wait


# ============================================================
# CONFIGURATION
# ============================================================

# CHANGE THESE TO CHANGE TIMINGS
MIX_TIME_DEFAULT = 3000


# ============================================================
# DISPENSE FUNCTIONS
# ============================================================

def dispense(station_name, dispense_time):

    stdout.write(
        f"DISPENSING:{station_name}:{dispense_time}\n"
    )

    # --------------------------------------------------------
    # FUTURE DISPENSER MOTOR LOGIC GOES HERE
    # --------------------------------------------------------

    wait(int(float(dispense_time) * 1000))

    stdout.write("DISPENSE_DONE\n")


# ============================================================
# MIXER FUNCTION
# ============================================================

def mix(mix_time_seconds):

    stdout.write("LOWERING_MIXER\n")

    wait(1000)

    stdout.write("MIXING\n")

    # --------------------------------------------------------
    # FUTURE MIXER MOTOR LOGIC GOES HERE
    # --------------------------------------------------------

    wait(int(float(mix_time_seconds) * 1000))

    stdout.write("RAISING_MIXER\n")

    wait(1000)

    stdout.write("MIX_DONE\n")


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
    # DISPENSE COMMAND
    # ========================================================

    if received_message.startswith("DISPENSE:"):

        parts = received_message.split(":")

        station_name = parts[1]
        dispense_time = parts[2]

        dispense(
            station_name,
            dispense_time
        )

    # ========================================================
    # MIX COMMAND
    # ========================================================

    elif received_message.startswith("MIX:"):

        mix_time = received_message.split(":")[1]

        mix(mix_time)

    # ========================================================
    # SHUTDOWN COMMAND
    # ========================================================

    elif received_message == "bye":

        stdout.write("BOTTLE_HUB_DONE\n")

        break

    else:

        stdout.write("UNKNOWN_COMMAND\n")