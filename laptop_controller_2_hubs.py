# SPDX-License-Identifier: MIT

"""
Laptop → Multi-Pybricks Hub Controller

This program:
1. Connects to multiple Pybricks hubs (Cup Hub and Bottle Hub).
2. Manages separate communication buffers for each.
3. Provides a dedicated logic loop for coordinating tasks between them.
4. Uses specific target messages to safely wait for tasks to finish.
"""

import asyncio
from contextlib import suppress
from bleak import BleakScanner, BleakClient

# ============================================================
# CONFIGURATION
# ============================================================

PYBRICKS_COMMAND_EVENT_CHAR_UUID = "c5f50002-8280-46da-89f4-6d8051e4aeef"

# ============================================================
# HUB CONNECTION CLASS
# ============================================================

class PybricksHub:
    """Manages the BLE connection and messaging for a single Pybricks Hub."""
    
    def __init__(self, name: str):
        self.name = name
        self.client = None
        
        # Signals that hub is ready for another command
        self.ready_event = asyncio.Event()
        
        # Signals that hub has sent the specific message we are waiting for
        self.response_event = asyncio.Event()
        
        # Buffer for assembling BLE packet fragments
        self.rx_buffer = bytearray()
        
        # Stores latest received hub message
        self.latest_response = ""
        
        # Tracks the specific message we are waiting to receive
        self.target_message = None 

    async def connect(self):
        """Finds and connects to the hub."""
        print(f"[{self.name}] Scanning...")
        device = await BleakScanner.find_device_by_name(self.name)
        
        if device is None:
            print(f"[{self.name}] Error: Could not find hub.")
            return False

        def handle_disconnect(_):
            print(f"\n[{self.name}] Disconnected.")

        self.client = BleakClient(device, disconnected_callback=handle_disconnect)
        await self.client.connect()
        
        await self.client.start_notify(
            PYBRICKS_COMMAND_EVENT_CHAR_UUID,
            self._handle_rx
        )
        print(f"[{self.name}] Connected successfully.")
        return True

    def _handle_rx(self, _, data: bytearray):
        """Internal callback to handle incoming BLE data."""
        # Ignore non-stdout packets
        if data[0] != 0x01:
            return

        # Remove Pybricks protocol byte and add to buffer
        payload = data[1:]
        self.rx_buffer.extend(payload)

        # Process complete newline-delimited messages
        while b"\n" in self.rx_buffer:
            line, _, remainder = self.rx_buffer.partition(b"\n")
            self.rx_buffer[:] = remainder

            received_message = line.decode().strip()

            if received_message == "READY":
                self.ready_event.set()
            else:
                self.latest_response = received_message
                print(f"[{self.name}] says: {self.latest_response}")
                
                # Check if this message is the specific one we are waiting for
                if self.target_message and self.target_message in received_message:
                    self.response_event.set()
                    self.target_message = None # Reset it after we find it

    async def send(self, command: str):
        """Sends a command string to the hub."""
        # Wait for hub ready signal
        await self.ready_event.wait()
        
        # Prepare for next READY
        self.ready_event.clear()

        payload = (command + "\n").encode()
        await self.client.write_gatt_char(
            PYBRICKS_COMMAND_EVENT_CHAR_UUID,
            b"\x06" + payload,
            response=True
        )

    async def wait_for(self, target: str):
        """Pauses the script until the hub sends a message containing the target string."""
        self.target_message = target
        self.response_event.clear()
        await self.response_event.wait()

    async def disconnect(self):
        """Safely closes the connection."""
        if self.client and self.client.is_connected:
            await self.client.disconnect()


# ============================================================
# MAIN PROGRAM
# ============================================================

async def main():
    
    # 1. Initialize hub objects
    cup_hub = PybricksHub("Cup Hub")
    bottle_hub = PybricksHub("Bottle Hub")

    # 2. Connect to all hubs
    print("Initializing connections...")
    
    cup_connected = await cup_hub.connect()
    bottle_connected = await bottle_hub.connect()

    if not (cup_connected and bottle_connected):
        print("Failed to connect to all required hubs. Exiting.")
        return

    print("\nAll hubs connected! Start the hub programs using the hub buttons.")
    
    # Wait for the user to press the button on both hubs (triggering the first READY)
    print("Waiting for both hubs to send READY signal...")
    await asyncio.gather(
        cup_hub.ready_event.wait(),
        bottle_hub.ready_event.wait()
    )
    
    print("\n--- SYSTEM READY ---")

    try:
        while True:
            
            # ============================================================
            # >>> START OF CUSTOM COORDINATION LOGIC
            # ============================================================
            
            # This is a basic prompt to keep the loop alive manually. 
            # In a fully autonomous system, you could replace this prompt 
            # with computer vision triggers or timed sequences.
            user_input = input("\nPress Enter to run a cycle, or 'q' to quit: ").strip()
            
            if user_input.lower() == 'q':
                break

            print("\n[Coordination Logic Executing...]")
            
            """
            ============================================================
            HUB COMMUNICATION API REFERENCE
            ============================================================
            Use the following methods to coordinate your connected hubs.

            1. SENDING COMMANDS
               Send a string message to a specific hub.
               -> await my_hub.send("COMMAND_STRING")

            2. WAITING FOR SPECIFIC REPLIES (Recommended)
               Pause the script until the hub replies with a specific string.
               This safely ignores intermediate messages or echoes.
               -> await my_hub.wait_for("EXPECTED_REPLY")

            3. READING THE LAST MESSAGE (Non-blocking)
               Access the most recently received string from the hub at any 
               time without pausing the script.
               -> current_status = my_hub.latest_response

            4. SIMULTANEOUS EXECUTION
               Execute actions on multiple hubs at the exact same time.
               -> await asyncio.gather(
                      hub_a.send("TASK_1"),
                      hub_b.send("TASK_2")
                  )
                  
            5. SIMULTANEOUS WAITING
               Pause the script until MULTIPLE hubs finish their tasks.
               -> await asyncio.gather(
                      hub_a.wait_for("TASK_1_DONE"),
                      hub_b.wait_for("TASK_2_DONE")
                  )
            ============================================================
            """

            # Example: Send message to Cup Hub
            # await cup_hub.send("MOVE:1")
            # await cup_hub.wait_for("ARRIVED") 
            
            # Example: Send message to Bottle Hub
            # await bottle_hub.send("POUR:50")
            # await bottle_hub.wait_for("DONE_POURING")
            
            print("[Coordination Logic Complete]")

            # ============================================================
            # <<< END OF CUSTOM COORDINATION LOGIC
            # ============================================================

    finally:
        # 3. Clean up and disconnect
        print("\nShutting down connections...")
        
        # Send 'bye' command to safely shut down the Python scripts on the hubs
        await asyncio.gather(
            cup_hub.send("bye"),
            bottle_hub.send("bye")
        )
        
        # Give hubs a tiny moment to process the bye command before killing the Bluetooth link
        await asyncio.sleep(0.5) 
        
        await cup_hub.disconnect()
        await bottle_hub.disconnect()
        print("Program complete.")

# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    with suppress(asyncio.CancelledError):
        asyncio.run(main())