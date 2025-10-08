# Imports
import os.path
import subprocess


class Notifications:
    def __init__(self, app_name: str, app_icon_path: str = None) -> None:
        # Make provided variables accessible across the class
        self._app_name: str = app_name
        self._app_icon_path: str | None = app_icon_path if app_icon_path else None

        # Make sure the app icon exists if it was provided
        if self._app_icon_path:
            if not os.path.exists(self._app_icon_path):
                raise FileNotFoundError("Couldn't find app icon!")
            # Change the icon path to the absolute path because notify-send sucks
            self._app_icon_path = os.path.abspath(self._app_icon_path)

        return

    # A function to create a notification for KDE Plasma using the notify-send tool
    # for profile switching
    ## Probably should remove this because I'm not using it
    async def createProfileSwitchNotification(self, profile_name: str, notification_id: int = None) -> int:
        """
        Creates a notification using ``notify-send`` to indicate a profile change.

        :param profile_name: The name of the profile that was switched to.
        :param notification_id: The ID of the notification to replace, if any.

        :returns: ``int`` - The ID of the notification.

        :raises None:
        """

        # Create a variable with the command to run to show the notification
        command: list = [
            "notify-send",  # Run the notify-send command
            "--app-name", self._app_name,  # Set the app title
            "--expire-time=5000",  # Set the notification expiration time to 5 seconds
            "-p",  # Print the ID of the notification
            f"Profile Change",  # Set the title/summary
            f"Switched to profile \"{profile_name.title()}.\""
        ]

        # Set the app icon if present
        if self._app_icon_path:
            command.append("--icon")
            command.append(self._app_icon_path)

        if notification_id:
            # If the notification ID to replace is specified, add it to the command at the second index
            command.insert(1, f"--replace-id={notification_id}")

        # Run the command to show the notification
        result: subprocess.CompletedProcess = subprocess.run(
            command, capture_output=True, text=True  # And store the output from the command
        )

        # Set the notification ID to be the notification's returned ID
        notification_id: int = int(str(result.stdout).strip())

        return notification_id

    async def createNotification(
            self,
            message: str,
            title: str = None,
            notification_id: int = None,
            expire_time: int = 5000
    ) -> int:
        """
        Creates a notification using ``notify-send`` to indicate a message to the user.
        This is by default a warning message.

        :param title: The title of the notification. Optional.
        :param message: The message to display in the notification.
        :param expire_time: The time it takes for the notification to expire in milliseconds.
         Optional. Default is 5,000, or five seconds.
        :param notification_id: The ID of an existing notification to replace. Optional.

        :returns: ``int`` - The ID of the notification.

        :raises None:
        """

        if not title:
            title = "Warning"

        # Create a variable with the command to run to show the notification
        command: list[str] = [
            "notify-send",  # Run the notify-send command
            "--app-name", self._app_name,  # Set the app title
            "--expire-time", str(expire_time),  # Set the notification expiration time
            "-p",  # Print the ID of the notification
            title.title(),  # Set the title/summary
            message
        ]

        # Set the app icon if present
        if self._app_icon_path:
            command.append("--icon")
            command.append(self._app_icon_path)

        # If the notification ID to replace is specified, add it to the command at the second index
        if notification_id:
            command.insert(1, f"--replace-id={notification_id}")

        # Run the command to show the notification
        result: subprocess.CompletedProcess = subprocess.run(
            command, capture_output=True, text=True  # And store the output from the command
        )

        # Set the notification ID to be the notification's returned ID
        notification_id: int = int(str(result.stdout).strip())

        return notification_id
