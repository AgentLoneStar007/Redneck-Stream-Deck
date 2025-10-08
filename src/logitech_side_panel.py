# Imports
import asyncio
import os.path
from logging import Logger, getLogger
from src.music_player import MusicPlayer
import tomllib


class LogitechSidePanel:
    def __init__(self) -> None:
        # Create a dictionary containing the names of each button reflecting the key code for said button
        self.button_codes: dict = {
            304: "button_1",
            305: "button_2",
            306: "button_3",
            307: "button_4",
            308: "button_5",
            309: "button_6",
            310: "button_7",
            311: "button_8",
            312: "button_9",
            313: "button_10",
            314: "button_11",
            315: "button_12",
            316: "button_13",
            317: "button_14",
            318: "button_15",
            319: "button_16",
            704: "button_17",
            705: "button_18",
            706: "button_19",
            707: "button_20",
            708: "button_21",
            709: "button_22",
            710: "button_23",
            711: "button_24",
            713: "scroll_wheel_up_26",
            714: "scroll_wheel_down_27",
            715: "button_joystick_25",
        }
        """The codes for each button with a corresponding button name as a string."""

        # The songs for each corresponding button
        self.song_mappings: dict[str, str] = {
            "button_1": "M4G1C DR34MS.mp3",
            "button_2": "Stray - Main Menu Theme - OST Soundtrack #stray #straygame.mp3",
            "button_3": "Mass Effect Trilogy - Extended Galaxy Map Theme (HD).mp3",
            "button_6": "TES V Skyrim Soundtrack - The Streets of Whiterun.mp3",
            "button_7": "Gran Turismo 5 Soundtrack feels so good - KEMMEI ADACHI (Lounge Music).mp3",
            "button_8": "Scheming Through The Zombie Apocalypse   Main Music.mp3",
            "button_11": "Grab a Cab.mp3",
            "button_12": "Team Fortress 2 Soundtrack   Red Bread.mp3",
            "button_13": "Punch-Out Wii Theme.mp3",
            "button_14": "il vento d'oro.mp3",
            "button_15": "Pepsiman Pepsiman Pepsiman   Pepsiman Remix.mp3",
            "button_16": "PIZZA TOWER - It's Pizza Time! (METAL COVER by RichaadEB).mp3"
        }

        # Create a variable showing the current profile
        self.current_profile: int = 0
        """The current profile the side panel is using."""

        # Create the music player library and make it class-accessible
        self.music_player: MusicPlayer = MusicPlayer()

        # Dynamically set the attributes of the class based on the button codes
        for key_code, button_name in self.button_codes.items():
            setattr(self, button_name, key_code)

        # Fetch the config
        self.config: dict = tomllib.load(open("config.toml", "rb"))

        # Fetch the logger
        self._log: Logger = getLogger()

        return

    async def _loadSong(self, button_name: str) -> None:
        # Get the absolute path to the music directory
        path_to_music_dir: str = os.path.abspath(self.config.get("music_directory", "music/"))

        # Check if the music directory still exists
        if not os.path.exists(path_to_music_dir):
            self._log.error("Couldn't find the music directory. Did you delete it, idiot?")
            return

        # Make sure button_1 is in the song map
        if button_name not in self.song_mappings:
            self._log.error(f"\"{button_name}\" isn't mapped to any song, stupid!")
            return

        if not self.song_mappings[button_name]:
            self._log.error(f"\"{button_name}\" doesn't have an assigned song, retard!")
            return

        # Get the full song path
        song_path: str = os.path.join(path_to_music_dir, self.song_mappings[button_name])
        del path_to_music_dir  # Cleanup

        # Make sure the song is there
        if not os.path.exists(song_path):
            self._log.error(
                f"Couldn't find the song \"{self.song_mappings[button_name]}.\" Maybe try a working file name "
                "next time?"
            )
            return

        # Load the song and play it
        self.music_player.load(song_path)
        self.music_player.play()
        self._log.debug(f"Now playing \"{self.song_mappings[button_name]}.\"")

        return

    async def handleButtonPress(self, code: int) -> None:
        self._log.debug(f"Processing event code {code}...")

        # Path for profile one(or 0)
        if self.current_profile == 0:
            ## Buttons 1-8: Music
            if code == self.button_1:
                await self._loadSong("button_1")
                return
            elif code == self.button_2:
                await self._loadSong("button_2")
                return
            elif code == self.button_3:
                await self._loadSong("button_3")
                return
            elif code == self.button_4:
                await self._loadSong("button_4")
                return
            elif code == self.button_5:
                await self._loadSong("button_5")
                return
            elif code == self.button_6:
                await self._loadSong("button_6")
                return
            elif code == self.button_7:
                await self._loadSong("button_7")
                return
            elif code == self.button_8:
                await self._loadSong("button_8")
                return

            elif code == self.button_9:
                # Do something
                return

            elif code == self.button_10:
                # Do something
                return

            ## Buttons 11-16: More music
            elif code == self.button_11:
                await self._loadSong("button_11")
                return
            elif code == self.button_12:
                await self._loadSong("button_12")
                return
            elif code == self.button_13:
                await self._loadSong("button_13")
                return
            elif code == self.button_14:
                await self._loadSong("button_14")
                return
            elif code == self.button_15:
                await self._loadSong("button_15")
                return
            elif code == self.button_16:
                await self._loadSong("button_16")
                return

            elif code == self.button_17:
                # Do something
                return
            elif code == self.button_18:
                # Do something
                return
            elif code == self.button_19:
                # Do something
                return
            elif code == self.button_20:
                # Do something
                return
            elif code == self.button_21:
                # Do something
                return
            ## Fast-forward music player
            elif code == self.button_22:
                if self.music_player.running:
                    self.music_player.fast_forward(10)
                else:
                    self._log.warning("There's no song playing! Can't fast-forward!")
                return
            ## Toggle pause on music player
            elif code == self.button_23:
                if self.music_player.running:
                    if self.music_player.paused:
                        self.music_player.resume()
                    else:
                        self.music_player.pause()
                else:
                    self._log.warning("There's no song playing! Can't toggle pause!")
                return
            ## Rewind music player
            elif code == self.button_24:
                if self.music_player.running:
                    self.music_player.rewind(10)
                else:
                    self._log.warning("There's no song playing! Can't rewind!")
                return
            elif code == self.scroll_wheel_up_26:
                # Do something
                return
            elif code == self.scroll_wheel_down_27:
                # Do something
                return
            elif code == self.button_joystick_25:
                # Do something
                return
            else:
                # Handle an unrecognized keycode (this shouldn't ever happen)
                print(f"Unrecognized code: {code}")
                return
        
        # Add more profiles as necessary

        return

