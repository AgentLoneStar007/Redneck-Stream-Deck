# Imports
import logging
import tomllib

import pygame
import time
import threading
import os

## Shoutout to ChatGPT for writing this and saving me
## like 30-45 minutes of pain.
## (Also shoutout to me for adding types because we like
## type safety here.)


class MusicPlayer:
    def __init__(self):
        # Initialize the mixer
        pygame.mixer.init()

        # Create some class vars
        self._lock: threading.Lock = threading.Lock()
        self._updater_thread = None
        self._config: dict = tomllib.load(open("config.toml", 'rb'))

        # Fetch the logger
        self._log: logging.Logger = logging.getLogger()

        # Create some utility vars
        self.paused: bool = False
        self.current_time: float = 0
        self.length: float = 0
        self.file: str | None = None
        self.running: bool = False

        return

    def load(self, filepath: str):
        """Load a music file."""
        with self._lock:
            pygame.mixer.music.load(filepath)
            self.file = filepath
            self.length = pygame.mixer.Sound(filepath).get_length()
            self.current_time = 0
            self._log.debug(f"Loaded file \"{filepath}.\" Length: {self.length:.2f}s")

    def _update_time(self) -> None:
        """Track playback time in a separate thread."""

        # Update the running variable
        self.running = True

        # And keep updating the current time while the music stream is active
        while self.running:
            if not self.paused and pygame.mixer.music.get_busy():
                self.current_time += 0.1
            time.sleep(0.1)

        return

    def play(self) -> None:
        """Start playing the loaded track."""

        # Make sure a file is loaded
        if not self.file:
            self._log.error("Can't start music player, no file is loaded!")

            return

        # Start playing the song
        pygame.mixer.music.play(start=self.current_time)
        pygame.mixer.music.set_volume(self._config.get("music_volume", 0.4))

        # Update the paused variable
        self.paused = False

        # Start the update thread
        if not self._updater_thread or not self._updater_thread.is_alive():
            self._updater_thread = threading.Thread(target=self._update_time, daemon=True)
            self._updater_thread.start()

        return

    def pause(self) -> None:
        """Pause playback."""

        # Check if the stream is already paused
        if not self.paused:
            # Pause the stream
            pygame.mixer.music.pause()
            self._log.debug("Paused the music.")

            # Update the paused variable
            self.paused = True

        else:
            self._log.warning("Can't pause music because it's already paused!")

        return

    def resume(self):
        """Resume playback."""

        # Check if the stream is paused
        if self.paused:
            # Unpause the stream
            pygame.mixer.music.unpause()
            self._log.debug("Resumed the music.")

            # Update the paused variable
            self.paused = False

        else:
            self._log.warning("Can't resume music because it's not paused!")

        return

    def stop(self):
        """Stop playback."""

        # Stop the music
        pygame.mixer.music.stop()
        self._log.debug("Stopped the music.")

        # Update variables
        self.running = False
        self.current_time = 0

        return

    def seek(self, seconds: float):
        """Jump to a specific time in seconds."""

        # Handle if there's no loaded file
        if not self.file:
            self._log.error("Cannot seek position in song because no file is loaded!")
            return

        # Process the seconds arg
        if seconds < 0: seconds = 0
        if seconds > self.length: seconds = self.length

        # Set the current time variable
        self.current_time = seconds

        # Start playing from that point
        pygame.mixer.music.play(start=seconds)
        self._log.debug(f"Seeked to position {seconds:.2f}s in song.")

        # Update the paused variable
        self.paused = False

        return

    def fast_forward(self, seconds: float = 5):
        """Skip forward."""
        self.seek(self.current_time + seconds)

        return

    def rewind(self, seconds: float = 5):
        """Skip backward."""
        self.seek(self.current_time - seconds)

        return
