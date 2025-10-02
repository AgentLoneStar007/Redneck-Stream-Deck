# Imports
import logging
import os
from pathlib import Path
from datetime import datetime


def setup() -> bool:
    """
    Checks the running environment to make sure everything is in order.

    :returns: ``bool`` - A boolean value indicating whether setup was successful.

    :raises None: This function will automatically log any issues. All that is
     required is that the program stop if False is returned.
    """

    print(f"{datetime.now().strftime("[%m/%d/%Y-%H:%M:%S]")} <INFO>: Running environment checks...")

    # Check if we have read permissions for the root directory
    if os.access(".", os.R_OK):
        pass
    else:
        print(f"\033[91m{datetime.now().strftime("[%m/%d/%Y-%H:%M:%S]")} <FATAL>: The program doesn't have read "
              "permissions for the root directory.\033[0m")

        return False

    # Check if we have write permissions as well
    if os.access(".", os.W_OK):
        pass
    else:
        print(f"\033[91m{datetime.now().strftime("[%m/%d/%Y-%H:%M:%S]")} <FATAL>: The program doesn't have write "
              f"permissions for the root directory.\033[0m")

        return False

    # Check if the .env is present
    if not Path(".env").is_file():
        # Handle if it isn't
        logging.fatal("Couldn't find the Dotenv file! Did you rename the example file?")
        print(
            f"\033[91m{datetime.now().strftime("[%m/%d/%Y-%H:%M:%S]")} <FATAL>: Couldn't find the Dotenv file! Did you "
            "rename the example file?\033[0m")

        # Return false if setup failed
        return False

    # Check if the config file is present
    if not Path("config.toml").is_file():
        # Handle if it isn't
        print(
            f"\033[91m{datetime.now().strftime("[%m/%d/%Y-%H:%M:%S]")} <FATAL>: Couldn't find the config file!\033[0m")

        # Return false if setup failed
        return False

    # Create a list of directories needed for the program to run
    needed_directories: set[str] = {"logs"}

    for directory in needed_directories:
        # Handle if the directory doesn't exist
        if not os.path.exists(directory):
            try:
                # Try to create the directory if not present
                os.makedirs(directory, exist_ok=True)

            except PermissionError:
                print(
                    f"\033[91m{datetime.now().strftime("[%m/%d/%Y-%H:%M:%S]")} <FATAL>: Failed to create needed "
                    f"directory \"{directory}\" due to a permission error.\033[0m")

                # Return false if setup failed
                return False

        else:
            # Check if we have read permissions for the directory
            if os.access(f"{directory}/", os.R_OK):
                pass
            else:
                print(
                    f"\033[91m{datetime.now().strftime("[%m/%d/%Y-%H:%M:%S]")} <FATAL>: The program doesn't have read "
                    f"permissions for the \"{directory}/\" directory.\033[0m")

                return False

            # Check if we have write permissions for it as well
            if os.access(f"{directory}/", os.W_OK):
                pass
            else:
                print(
                    f"\033[91m{datetime.now().strftime("[%m/%d/%Y-%H:%M:%S]")} <FATAL>: The program doesn't have write "
                    f"permissions for the \"{directory}/\" directory.\033[0m")

                return False

    return True
