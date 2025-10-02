# Imports
import logging
from logging import handlers
import tomllib
from sys import stderr, stdout
import os
from typing import Literal, Mapping, Any
from datetime import datetime


class DailyRotatingFileHandler(handlers.TimedRotatingFileHandler):
    def __init__(self, filename="latest.log", **kwargs):
        # Get the full path of the log file and make it class-accessible
        self.base_filename = os.path.abspath(filename)

        # Check if the file already exists, and if it does, archive it
        if os.path.exists(self.base_filename):
            self._archive_existing()

        # Initialize the parent class
        super().__init__(
            # The filename to use
            filename,
            # The interval to archive files at. Midnight technically means daily.
            when="midnight",
            interval=1,
            # How many old logs to keep
            backupCount=7,
            **kwargs
        )

        # Create a new stream to the latest.log file
        self.stream = self._open()

    def _archive_existing(self):
        """Archive current latest.log into MM-DD-YYYY[_N].log"""

        # Get the log's timestamp name
        timestamp: str = datetime.now().strftime("%m-%d-%Y")
        # Get the full file name for the log to be archived as an absolute path
        rollover_filename: str = os.path.join(os.path.dirname(self.base_filename), f"{timestamp}.log")

        # Go through all existing logs, and if a log with a duplicate name exists,
        # add a counter suffix to it to prevent duplicates
        counter: int = 1
        while os.path.exists(rollover_filename):
            rollover_filename = os.path.join(
                os.path.dirname(self.base_filename),
                f"{timestamp}_{counter}.log"
            )
            counter += 1

        # Rename the last latest.log to the new archival name.
        os.rename(self.base_filename, rollover_filename)

    def doRollover(self):
        # Check if the stream is active, and if it is, close it
        if self.stream:
            self.stream.close()
            self.stream = None

        # Archive the current latest.log
        if os.path.exists(self.base_filename):
            self._archive_existing()

        # Reopen new latest.log for continued logging
        self.stream = self._open()


# A custom stream handler for the console that sends errors to STDERR, and everything else to STDOUT.
## Why this isn't default behaviour I don't know...
class StreamHandler(logging.StreamHandler):
    def emit(self, record: logging.LogRecord) -> None:
        # Assign the stream it should go to based off of the level number
        if record.levelno >= logging.ERROR:
            self.stream = stderr
        else:
            self.stream = stdout

        # Send the record to the stream
        super().emit(record)

        return

# A custom formatter class that adds colors to logs depending on their type
class Formatter(logging.Formatter):
    log_colors: dict = {
        logging.DEBUG: "\033[37m",  # Dark gray
        logging.INFO: "\033[0m",  # Reset character. Info logs will use default terminal color.
        logging.WARNING: "\033[93m",  # Yellow
        logging.ERROR: "\033[91m",  # Red
        logging.FATAL: "\033[31m"  # Lighter red
    }
    reset_char: str = "\033[0m"

    def __init__(self,
                 fmt: str | None = None,
                 datefmt: str | None = None,
                 style: Literal["%", "{", "$"] = "%",
                 validate: bool = True,
                 *,
                 defaults: Mapping[str, Any] | None = None,
                 use_colors: bool = False) -> None:
        # Make the use_colors var class-accessible
        self.use_colors: bool = use_colors
        del use_colors  # Cleanup

        # Initialize the parent class
        super().__init__(fmt=fmt, datefmt=datefmt, style=style, validate=validate, defaults=defaults)

        return

    def format(self, record: logging.LogRecord) -> str:
        # Change the name CRITICAL to FATAL, because I like it
        if record.levelno == logging.FATAL:
            record.levelname = "FATAL"

        # If the formatter should use colors, return a string with the color codes
        if self.use_colors:
            return (
                # Get the color of the log type
                f"{self.log_colors.get(record.levelno, self.reset_char)}"
                f"{super().format(record)}"
                f"{self.reset_char}"
            )
        # Otherwise, return the plain log
        else:
            return f"{super().format(record)}"


def configureLogger() -> logging.Logger:
    """
    Creates a fully configured base logger for the program,
    with ANSI colors, a separate logger for console and file,
    and more.

    :return:
    """

    # Fetch the program configuration
    config: dict = tomllib.load(open("config.toml", "rb"))

    # Create the base logger
    log: logging.Logger = logging.getLogger()
    # Set it to a base of debug. This will be updated later.
    log.setLevel(logging.DEBUG)

    # Create a stream handler for the console
    console_logging_handler: logging.StreamHandler = StreamHandler()

    # Get the logging level from the config
    logging_level_str: str = str(config.get("logging_level", "info")).lower()

    # Set the logging level based on that value
    logging_level: int = logging.INFO
    if logging_level_str in {"debug", "d"}:
        logging_level = logging.DEBUG
    elif logging_level_str in {"warn", "warning", "w"}:
        logging_level = logging.WARNING
    elif logging_level_str in {"error", "err", "e"}:
        logging_level = logging.ERROR
    elif logging_level_str in {"fatal", "critical", "f", "c"}:
        logging_level = logging.FATAL

    # Finally, set the logging level
    console_logging_handler.setLevel(logging_level)

    # Create a handler for the file logger
    file_logging_handler: handlers.TimedRotatingFileHandler = DailyRotatingFileHandler("logs/latest.log")
    # Set the file logger to debug
    file_logging_handler.setLevel(logging.DEBUG)

    # Create a format for the file log handler to use
    file_logging_formatter: logging.Formatter = logging.Formatter(
        "[%(asctime)s] <%(levelname)s>: %(message)s",
        datefmt="%m/%d/%Y-%H:%M:%S"
    )

    # And a separate format that uses ANSI codes for colors for the console
    console_logging_formatter: logging.Formatter = Formatter(
        "[%(asctime)s] <%(levelname)s>: %(message)s",
        use_colors=True,
        datefmt="%m/%d/%Y-%H:%M:%S",
    )

    # Apply the formatter to both handlers
    console_logging_handler.setFormatter(console_logging_formatter)
    file_logging_handler.setFormatter(file_logging_formatter)

    # Finally, add both handlers to the logger
    log.addHandler(console_logging_handler)
    log.addHandler(file_logging_handler)

    return log
