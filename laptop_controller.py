1
# SPDX-License-Identifier: MIT

"""
Laptop → Pybricks Hub Station Controller

This program:

1. Connects to a Pybricks hub.
2. Waits for user station selection (1-5).
3. Sends the selected station number.
4. Waits for a response from the hub.
5. Prints the returned message.
"""

import asyncio
from contextlib import suppress
from bleak import BleakScanner, BleakClient


# ============================================================
# CONFIGURATION
# ============================================================

# CHANGE THIS TO CHANGE YOUR HUB NAME
HUB_NAME = "Cup Hub"

# Pybricks BLE communication UUID.
# Normally this does not need changing.
PYBRICKS_COMMAND_EVENT_CHAR_UUID = (
    "c5f50002-8280-46da-89f4-6d8051e4aeef"
)


# ============================================================
# MAIN PROGRAM
# ============================================================

async def main():

    main_task = asyncio.current_task()

    # Signals that hub is ready for another command
    ready_event = asyncio.Event()

    # Signals that hub has replied to our command
    response_event = asyncio.Event()

    # Buffer for assembling BLE packet fragments
    rx_buffer = bytearray()

    # Stores latest received hub message
    latest_response = ""

    # --------------------------------------------------------
    # Disconnect handler
    # --------------------------------------------------------

    def handle_disconnect(_):

        print("\nHub disconnected.")

        if not main_task.done():
            main_task.cancel()

    # --------------------------------------------------------
    # Incoming message handler
    # --------------------------------------------------------

    def handle_rx(_, data: bytearray):

        nonlocal latest_response

        # Ignore non-stdout packets
        if data[0] != 0x01:
            return

        # Remove Pybricks protocol byte
        payload = data[1:]

        # Add data to buffer
        rx_buffer.extend(payload)

        # Process complete newline-delimited messages
        while b"\n" in rx_buffer:

            line, _, remainder = rx_buffer.partition(b"\n")
            rx_buffer[:] = remainder

            # Convert bytes → string
            received_message = line.decode().strip()

            # Hub ready signal
            if received_message == "READY":
                ready_event.set()

            else:

                # Store response
                latest_response = received_message

                print(f"Hub says: {latest_response}")

                # Notify main loop that reply arrived
                # Only unlock user input after arrival
                if received_message.startswith("ARRIVED:"):
                    response_event.set()

    # --------------------------------------------------------
    # Find hub
    # --------------------------------------------------------

    device = await BleakScanner.find_device_by_name(HUB_NAME)

    if device is None:
        print(f"Could not find hub '{HUB_NAME}'")
        return

    # --------------------------------------------------------
    # Connect to hub
    # --------------------------------------------------------

    async with BleakClient(device, handle_disconnect) as client:

        await client.start_notify(
            PYBRICKS_COMMAND_EVENT_CHAR_UUID,
            handle_rx
        )

        # ----------------------------------------------------
        # Send helper function
        # ----------------------------------------------------

        async def send(command: str):

            # Wait for hub ready signal
            await ready_event.wait()

            # Prepare for next READY
            ready_event.clear()

            payload = (command + "\n").encode()

            await client.write_gatt_char(
                PYBRICKS_COMMAND_EVENT_CHAR_UUID,
                b"\x06" + payload,
                response=True
            )

        print("Start the hub program using the hub button.")

        # ====================================================
        # USER INPUT LOOP
        # ====================================================

        while True:

            station = input(
                "\nChoose station (1-5) or q to quit: "
            ).strip()

            # Quit command
            if station.lower() == "q":

                await send("bye")

                break

            # Validate input
            if station not in ["1", "2", "3", "4", "5"]:

                print("Invalid selection.")

                continue

            print(f"Sending move command to station {station}")

            # Prepare to wait for reply
            response_event.clear()

            # Send command
            await send(f"MOVE:{station}")

            # Wait until hub responds
            await response_event.wait()

        print("Program complete.")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    with suppress(asyncio.CancelledError):
        asyncio.run(main())