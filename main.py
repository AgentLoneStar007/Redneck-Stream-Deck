## Redneck Stream Deck
## A stupid project by AgentLoneStar007
## https://github.com/AgentLoneStar007

# Imports
import sys
import os
import tomllib
import traceback
import evdev
from evdev import InputDevice, ecodes
import asyncio
import logging
from dotenv import load_dotenv
from src.logitech_side_panel import LogitechSidePanel
from src.logger import configureLogger
from src.utils import setup
from src.streamer_bot_ws import StreamerBotWebsocket

# Load the dotenv file
load_dotenv()


# Dotenv variables
STREAMER_BOT_ADDRESS: str = os.getenv("STREAMER_BOT_ADDRESS")
STREAMER_BOT_PORT: int = int(os.getenv("STREAMER_BOT_PORT"))


# Function to fetch the device in /dev/input
async def fetchDevicePath(device_vendor_id: str, device_product_id: str) -> str | None:
    log.info("Looking for device...")

    # Convert the Hexadecimal(base-16) values to a decimal(base-10) value
    device_vendor_id: int = int(device_vendor_id, 16)
    device_product_id: int = int(device_product_id, 16)

    while True:
        devices: list[InputDevice] = [InputDevice(path) for path in evdev.list_devices()]

        for device in devices:
            if (device.info.vendor == device_vendor_id) and (device.info.product == device_product_id):
                return device.path

        # Wait half a second at each interval before trying again
        await asyncio.sleep(0.5)


# Main program loop
async def main() -> None:
    # Load the config
    config: dict = tomllib.load(open("config.toml", 'rb'))

    # Create the connection to Streamer.bot
    streamer_bot: StreamerBotWebsocket = StreamerBotWebsocket(
        url=STREAMER_BOT_ADDRESS,
        port=STREAMER_BOT_PORT
    )
    # Connect to it
    # TODO: This function is blocking. It needs to potentially be set as a background task.
    ## The websocket can run in the background completely separate from the main loop. It
    ## simply needs to log errors when it disconnects and when an event is attempted to be
    ## sent to it but fails to process since there's no active connection.
    #await streamer_bot.connect()
    #await streamer_bot.get_actions()

    # Create an object of the Logitech side panel class
    side_panel: LogitechSidePanel = LogitechSidePanel()

    # Handle if the device's vendor ID or product ID are unset
    if not config.get("device_vendor_id") or not config.get("device_product_id"):
        raise ValueError("You forgot to specify either your device vendor ID or product ID!")

    while True:
        # Fetch the device's path
        device_path: str = await fetchDevicePath(
            device_vendor_id=config.get("device_vendor_id"),
            device_product_id=config.get("device_product_id")
        )

        # Open the device
        device = InputDevice(device_path)

        log.info(f"Listening to events from {device_path}...")
        try:
            for event in device.read_loop():
                if event.type == evdev.ecodes.EV_ABS:  # Absolute axis event, typical for joysticks
                    abs_event: evdev.events.AbsEvent = evdev.categorize(event)
                    axis: int = abs_event.event.code
                    value: int = abs_event.event.value

                    # Print the axis code and its corresponding value (joystick position)
                    log.debug(f"Axis: {axis}, Value: {value}")

                    # You can add specific conditions to handle different axes or ranges of values
                    # Example: Move left or right based on axis 1 values
                    if axis == evdev.ecodes.ABS_X:  # Horizontal movement axis
                        if value < 128:
                            log.debug("Joystick moved left")
                        elif value > 128:
                            log.debug("Joystick moved right")

                    elif axis == evdev.ecodes.ABS_Y:  # Vertical movement axis
                        if value < 128:
                            log.debug("Joystick moved up")
                        elif value > 128:
                            log.debug("Joystick moved down")

                # Key event, button presses
                elif event.type == ecodes.EV_KEY:
                    if event.value == 1:  # Key press (value 0 is release)
                        if event.code in side_panel.button_codes:
                            # Handle a button press
                            await side_panel.handleButtonPress(code=event.code)

                        else:
                            # Print to console if the button isn't recognized
                            log.warning(f"Unrecognized button code: {event.code}")

                    else:
                        # Something can be done here upon the button release, if desired
                        pass

        except OSError:
            log.error("Lost connection to device, attempting reconnect...")


# Main program execution
if __name__ == "__main__":
    # Create the base logger
    log: logging.Logger = logging.getLogger()

    # Create a variable for the return code
    ## I do this instead of just passing "1" to sys.exit upon an error in the hopes that
    ## I might use error codes one day.
    return_code: int = 0

    # Create the program loop
    loop: asyncio.AbstractEventLoop | None = asyncio.new_event_loop()

    try:
        # Run environment checks
        if not setup():
            return_code = 1
            sys.exit(return_code)

        # Configure the logger
        log = configureLogger()

        # Run the program
        loop.run_until_complete(main())

    except KeyboardInterrupt:
        log.info("Shutting down!")

    except Exception as error:
        log.fatal(f"Process failed with the following error: {error}")
        traceback.print_exc()

        # Update the return code
        return_code = 1

    finally:
        # Gracefully stop the event loop
        loop.stop()
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()

        # Stop and return the return code
        sys.exit(return_code)
