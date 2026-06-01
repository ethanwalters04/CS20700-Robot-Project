# SPDX-License-Identifier: MIT

"""
MAIN SYSTEM CONTROLLER

This laptop program coordinates BOTH hubs:

1. Cup Hub
   - Moves the cup between stations

2. Bottle Hub
   - Dispenses liquids
   - Controls mixer

===============================================================
SYSTEM FLOW
===============================================================

Select recipe
    ↓
Move cup to bottle station
    ↓
Dispense liquid
    ↓
Repeat for all ingredients
    ↓
Move cup to mixer
    ↓
Mix drink
    ↓
Move cup to home station

===============================================================
PHYSICAL LAYOUT
===============================================================

station_home
    ↓
station_mixer
    ↓
station_bottle1
    ↓
station_bottle2
    ↓
station_bottle3

===============================================================
"""

import asyncio
import random
from contextlib import suppress

from bleak import BleakScanner, BleakClient


# ============================================================
# HUB CONFIGURATION
# ============================================================

# CHANGE THESE TO MATCH YOUR HUB NAMES
CUP_HUB_NAME = "Cup Hub"
BOTTLE_HUB_NAME = "Bottle Hub"

PYBRICKS_COMMAND_EVENT_CHAR_UUID = (
    "c5f50002-8280-46da-89f4-6d8051e4aeef"
)


# ============================================================
# RECIPE DEFINITIONS
# ============================================================

"""
===============================================================
RECIPE SELECTION GOES HERE
===============================================================

Each recipe is a list of ingredients.

Each ingredient contains:
    station name
    dispense duration in seconds

Example:
("station_bottle1", 2.0)

means:
    move to bottle 1
    dispense for 2 seconds

===============================================================
"""

RECIPES = [

    # Recipe 1
    [
        ("station_bottle1", 2.0),
        ("station_bottle2", 2.0),
    ],

    # Recipe 2
    [
        ("station_bottle1", 1.0),
        ("station_bottle3", 3.0),
    ],

    # Recipe 3
    [
        ("station_bottle2", 2.5),
        ("station_bottle3", 1.5),
    ],

    # Recipe 4
    [
        ("station_bottle1", 1.5),
        ("station_bottle2", 1.5),
        ("station_bottle3", 1.5),
    ],

    # Recipe 5
    [
        ("station_bottle3", 4.0),
    ],
]


# ============================================================
# HUB CONTROLLER CLASS
# ============================================================

class HubController:

    def __init__(self, hub_name):

        self.hub_name = hub_name

        self.client = None

        self.ready_event = asyncio.Event()
        self.response_event = asyncio.Event()

        self.rx_buffer = bytearray()

        self.latest_response = ""

    async def connect(self):

        print(f"Searching for {self.hub_name}...")

        device = await BleakScanner.find_device_by_name(
            self.hub_name
        )

        if device is None:
            raise Exception(
                f"Could not find hub '{self.hub_name}'"
            )

        self.client = BleakClient(
            device,
            self.handle_disconnect
        )

        await self.client.connect()

        await self.client.start_notify(
            PYBRICKS_COMMAND_EVENT_CHAR_UUID,
            self.handle_rx
        )

        print(f"Connected to {self.hub_name}")

    def handle_disconnect(self, _):

        print(f"{self.hub_name} disconnected.")

    def handle_rx(self, _, data: bytearray):

        if data[0] != 0x01:
            return

        payload = data[1:]

        self.rx_buffer.extend(payload)

        while b"\n" in self.rx_buffer:

            line, _, remainder = self.rx_buffer.partition(b"\n")
            self.rx_buffer[:] = remainder

            received_message = line.decode().strip()

            if received_message == "READY":

                self.ready_event.set()

            else:

                self.latest_response = received_message

                print(
                    f"[{self.hub_name}] "
                    f"{self.latest_response}"
                )

                # Any response ending with DONE or ARRIVED
                # is treated as task completion.
                if (
                    "DONE" in received_message
                    or "ARRIVED" in received_message
                ):
                    self.response_event.set()

    async def send(self, command):

        await self.ready_event.wait()

        self.ready_event.clear()

        self.response_event.clear()

        payload = (command + "\n").encode()

        await self.client.write_gatt_char(
            PYBRICKS_COMMAND_EVENT_CHAR_UUID,
            b"\x06" + payload,
            response=True
        )

        await self.response_event.wait()


# ============================================================
# MAIN PROGRAM
# ============================================================

async def main():

    # Create controllers
    cup_hub = HubController(CUP_HUB_NAME)
    bottle_hub = HubController(BOTTLE_HUB_NAME)

    # Connect to hubs
    await cup_hub.connect()
    await bottle_hub.connect()

    print("\nStart BOTH hub programs now.")

    await asyncio.sleep(2)

    """
    ===========================================================
    RANDOM RECIPE SELECTION HAPPENS HERE
    ===========================================================
    """

    selected_recipe = random.choice(RECIPES)

    print("\nSelected recipe:")
    print(selected_recipe)

    # ========================================================
    # EXECUTE RECIPE
    # ========================================================

    for station_name, dispense_time in selected_recipe:

        # ----------------------------------------------------
        # MOVE CUP TO BOTTLE
        # ----------------------------------------------------

        move_command = f"MOVE:{station_name}"

        print(f"\nMoving cup to {station_name}")

        await cup_hub.send(move_command)

        # ----------------------------------------------------
        # DISPENSE LIQUID
        # ----------------------------------------------------

        dispense_command = (
            f"DISPENSE:{station_name}:{dispense_time}"
        )

        print(
            f"Dispensing from {station_name} "
            f"for {dispense_time} seconds"
        )

        await bottle_hub.send(dispense_command)

    # ========================================================
    # MOVE TO MIXER
    # ========================================================

    print("\nMoving cup to mixer")

    await cup_hub.send("MOVE:station_mixer")

    # ========================================================
    # MIX DRINK
    # ========================================================

    print("\nMixing drink")

    await bottle_hub.send("MIX:3")

    # ========================================================
    # RETURN HOME
    # ========================================================

    print("\nReturning cup to home")

    await cup_hub.send("MOVE:station_home")

    print("\nDrink complete.")

    # Optional shutdown
    await cup_hub.send("bye")
    await bottle_hub.send("bye")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    with suppress(asyncio.CancelledError):
        asyncio.run(main())