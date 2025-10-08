# Imports
import websockets
import json
import logging
from typing import Optional
from enum import Enum
import asyncio
import re
from urllib.parse import urlparse, ParseResult
from datetime import datetime
import uuid


# TODO: What's left for this websocket helper:
#  - Add a backoff strategy for the reconnect
#  - Maybe add unique subscription IDs
#  - Maybe change out handle_event to instead be able to hook to a callback
#  - MAKE WEBSOCKET CHILL WITH THE LOGS! Files are already getting huge over just minutes!

class StreamerBotWebsocket:
    class EventTypes:
        """
        Event types that can be received from Streamer.bot.
        This class will contain subclasses for each source,
        and each source will have it's possible corresponding
        events.
        """

        class Twitch(str, Enum):
            """Events that can be received from Twitch."""

            ChatMessage = "ChatMessage"
            """Will fire upon chat messages in Twitch chat."""

    class Events:
        """Events and their data that can be received from Streamer.bot."""

        class Twitch:
            """Events related to Twitch."""

            class ChatMessage:
                """A chat message from Twitch and all of its data."""

                message: dict  # Needs custom class
                user: dict  # Needs custom class
                messageId: str | None
                meta: dict  # Needs custom class
                anonymous: bool
                text: str | None
                emotes: list | None
                parts: list | None
                isReply: bool
                reply: dict  # Needs custom class
                isTest: bool
                sharedChatSource: dict  # Needs custom class
                isInSharedChat: bool
                isSharedChatHost: bool
                isFromSharedChatGuest: bool

    def __init__(
            self,
            url: str = "127.0.0.1",
            port: int = 8080,
            keep_subscriptions_upon_disconnect: bool = True
    ) -> None:
        """
        A websocket client for interfacing with the Streamer.bot Web Socket server.

        :param url: The IP address or URL Streamer.bot is at. You do not have to
         provide a protocol. If you add one, this will be removed and re-added.
         For example, use "127.0.0.1" instead of "ws://127.0.0.1."
        :param port: The port that Streamer.bot is listening on.
        :param keep_subscriptions_upon_disconnect: Whether subscriptions should retain across disconnects.

        :returns: ``None``

        :raises None:
        """

        # Make the URL and port class-accessible
        self.url: str = url
        self.port: int = port

        # Sanitize the URL by checking if a port or protocol is present,
        # and remove it if it is
        if not re.match(r'^\w+://', self.url):
            self.url = "ws://" + url
        parsed_url: ParseResult = urlparse(self.url)
        self.url = parsed_url.hostname or "127.0.0.1"

        # Create a variable to contain whether subscriptions should be kept upon disconnect
        self._keep_subscriptions: bool = keep_subscriptions_upon_disconnect

        del url, port, parsed_url, keep_subscriptions_upon_disconnect  # Cleanup

        # Create the base logger
        self._log: logging.Logger = logging.getLogger()

        # Create a variable to store whether the socket is still listening
        self._running: bool = False

        # Create the websocket itself
        self._websocket: Optional[websockets.ClientConnection] = None

        # Create a variable to show how often the connection should be checked, in seconds
        self._ping_interval: int = 5

        # Create a list to store all background tasks in
        self._tasks: list[asyncio.Task] = []

        # Create a dictionary to store subscriptions in
        self._subscriptions: dict[str, list[str]] = {}

        # Create an Asyncio _lock to prevent issues with the subscriptions list ever accidentally
        # getting accessed concurrently
        self._subscriptions_lock: asyncio.Lock = asyncio.Lock()

        return

    async def _listen_loop(self, websocket: websockets.ClientConnection):
        """Main loop to receive events."""

        async for message in websocket:
            try:
                # Parse the data
                data: dict = json.loads(message)
                # Send the data to the event handler
                await self._handle_event(data)

            except Exception as error:
                self._log.error(f"The following error occurred while processing an event: {error}")

        return

    async def _reconnect(self):
        """Attempt to reconnect to the websocket."""

        if self._running:
            await asyncio.sleep(5)
            await self.connect()

    async def _ping_loop(self):
        """Send pings periodically to keep connection alive."""

        while self._running and self._websocket:
            try:
                # Ping the websocket every interval
                await self._websocket.ping()
                await asyncio.sleep(self._ping_interval)

            # Pass the error up if it's an Asyncio cancelled error
            except asyncio.CancelledError:
                raise

            # Handle if there's an error pinging
            except Exception as error:
                self._log.warning(
                    f"Failed to ping Streamer.bot with the following error: {error}. Attempting reconnect...")
                # Attempt to reconnect
                await self._reconnect()

                return

    async def _handle_event(self, payload: dict):
        """Process data from the websocket."""

        self._log.debug(f"event: {payload}")

        ## Processor for Twitch chat messages
        if (
                payload.get("event", {}).get("source", "") == "Twitch"
        ) and (
                payload.get("event", {}).get("type", "") == self.EventTypes.Twitch.ChatMessage
        ):
            self._log.info(
                f"Received message from {payload["data"]["message"]["displayName"]}: {payload["data"]["message"]["message"]}"
            )

        return

    async def connect(self) -> None:
        """Starts the websocket connection to Streamer.bot."""

        # Update the running var
        self._running = True

        # Try to connect to Streamer.bot
        while self._running:
            try:
                self._log.debug("Attempting connection to Streamer.bot...")
                # Connect to the websocket
                self._websocket = await websockets.connect(
                    # Protocol
                    "ws://"
                    # IP/URL
                    f"{self.url}"
                    # Port
                    f":{self.port}"
                )
                self._log.info("Connected to Streamer.bot.")

                # Resubscribe to previous subscriptions
                if self._subscriptions and self._keep_subscriptions:
                    for source, events in self._subscriptions.items():
                        # Create the subscription message
                        subscription_message: dict = {
                            "request": "Subscribe",
                            "id": "reconnect",
                            "events": {source: events},
                        }
                        # Send it
                        await self._websocket.send(json.dumps(subscription_message))
                        self._log.debug(f"Re-subscribed to {source}: {events}")

                # Keep listening to the socket in the background
                self._tasks.append(asyncio.create_task(self._listen_loop(self._websocket)))
                # And keep pinging the connection to make sure it stays alive
                self._tasks.append(asyncio.create_task(self._ping_loop()))

                return

            # Handle an error in the connection
            # TODO: Maybe add a different handler for critical errors and non-critical errors
            except Exception as error:
                # TODO: Implement a back-off system!
                self._log.error(
                    f"The following error occurred in the Streamer.bot connection: {error}. Retrying in 3 seconds."
                )
                await asyncio.sleep(3)

        return

    async def subscribe(
            self,
            twitch: list[EventTypes.Twitch]
    ) -> None:
        """
        Subscribe to an event from the Streamer.bot websocket.
        Usage:
        # Subscribe to Twitch chat messages
        await websocket.subscribe(twitch=websocket.TwitchEvents.ChatMessage)
        :param twitch: All Twitch-related events to subscribe to.

        :returns: ``None``

        :raises ConnectionError: If the websocket is not connected.
        """

        # Don't do anything if no arguments were provided
        if not any([twitch]):
            return

        if not self._websocket:
            raise ConnectionError("Websocket is not connected!")

        # Create the events dictionary
        events: dict = {}
        # Add all event types to it
        if twitch:
            events["Twitch"] = [event.value for event in twitch]

        async with self._subscriptions_lock:
            # Add all subscriptions to the subscriptions dictionary for use upon reconnect
            for source, event in events.items():
                # Add the source to the subscriptions if not already present
                if source not in self._subscriptions:
                    self._subscriptions[source] = []
                for event in events:
                    # Add the event to the source if not already present
                    if event not in self._subscriptions[source]:
                        self._subscriptions[source].append(event)

        # Create the payload to be sent
        payload: dict = {
            "request": "Subscribe",
            "id": "1",  # TODO: Check if this needs to be unique
            "events": events
        }

        self._log.debug(f"Attempting to subscribe to the following events in Streamer.bot: {events}")
        await self._websocket.send(json.dumps(payload))
        self._log.debug(f"Subscribed.")

        return

    async def unsubscribe(
            self,
            unsubscribe_from_all: bool = False,
            twitch: list[EventTypes.Twitch] = None
    ) -> None:
        """
        Unsubscribe from events received from the Streamer.bot websocket.
        Usage:
        # Unsubscribe from Twitch chat messages
        await websocket.unsubscribe(twitch=websocket.TwitchEvents.ChatMessage)
        # Or unsub from all events
        await websocket.unsubscribe(unsubscribe_from_all=True)
        :param unsubscribe_from_all: A boolean value that, if set to true,
         will unsubscribe from all other arguments. Default is false.
        :param twitch: All Twitch-related events to unsubscribe from.

        :returns: ``None``

        :raises ConnectionError: If the websocket is not connected.
        """

        # Don't do anything if no arguments were provided
        if not any([twitch, unsubscribe_from_all]):
            return

        if not self._websocket:
            raise ConnectionError("Websocket is not connected!")

        async with self._subscriptions_lock:
            if not unsubscribe_from_all:
                # Create the events dictionary
                events: dict = {}

                # Add all event types to it
                if twitch:
                    events["Twitch"] = [event.value for event in twitch]

                # Remove all matching events from the subscriptions dictionary to prevent resubscribe upon reconnect
                for source, event in events.items():
                    # Check if the source is in the subscriptions list
                    if source in self._subscriptions:
                        for event in events:
                            # If the event is in the source,
                            if event in self._subscriptions[source]:
                                # Remove the event from the source
                                self._subscriptions[source].remove(event)
                        # If there are no events left for that source, remove it entirely
                        if not self._subscriptions[source]:
                            self._subscriptions.pop(source, None)

            else:
                # Create the events dictionary to be a copy of the current subscriptions
                events: dict = self._subscriptions.copy()
                self._subscriptions.clear()

        # Create the payload to be sent
        payload: dict = {
            "request": "Unsubscribe",
            "events": events,
        }

        self._log.debug(
            "Attempting to unsubscribe from all events from Streamer.bot..." if unsubscribe_from_all else (
                    f"Attempting to unsubscribe from the following events in Streamer.bot: " + str(events))
        )
        await self._websocket.send(json.dumps(payload))
        self._log.debug(f"Unsubscribed.")

    async def disconnect(self) -> None:
        """Disconnects from Streamer.bot."""

        # Update the running var
        self._running = False

        # Cancel background tasks
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

        # Disconnect the websocket if it's still active
        if self._websocket:
            await self._websocket.close()
            self._websocket = None

        self._log.debug("Closed connection to Streamer.bot.")

        return

    async def get_actions(self) -> dict:
        """
        Gets all actions in Streamer.bot.

        :return:
        """
        # Handle if the websocket isn't connected
        if not self._websocket:
            raise ConnectionError("Websocket is not connected!")

        # Create the payload
        payload: dict = {
          "request": "GetActions",
          "id": str(uuid.uuid1())
        }

        # Send the payload
        self._log.debug("Attempting to get all actions in Streamer.bot...")
        await self._websocket.send(json.dumps(payload))
        self._log.debug("Request completed.")

        return {}

    # TODO: This function still isn't done. Finish it.
    async def do_action(
            self,
            action_id: str,
            action_name: str = None,
            args: dict = None
    ) -> None:
        """
        Perform an action in Streamer.bot.

        :param action_id: The action's ID. Can be acquired from the
         get_actions() method.
        :param action_name: The action's name.
        :param args: Any arguments to pass to the action, in the
         form of a dictionary.

        :returns: ``None``

        :raises None:
        """
        # Handle if the websocket isn't connected
        if not self._websocket:
            raise ConnectionError("Websocket is not connected!")

        ## Don't judge me. I'm tired.
        if action_name and action_id:
            # Create the payload to send
            payload: dict = {
              "request": "DoAction",
              "action": {
                "id": action_id,
                "name": action_name
              },
              "args": args,
              "id": str(uuid.uuid1())
            }
        elif action_name:
            # Create the payload to send
            payload: dict = {
                "request": "DoAction",
                "action": {
                    "name": action_name
                },
                "args": args,
                "id": str(uuid.uuid1())
            }
        else:
            # Create the payload to send
            payload: dict = {
                "request": "DoAction",
                "action": {
                    "id": action_id,
                },
                "args": args,
                "id": str(uuid.uuid1())
            }

        # Send the payload
        self._log.debug("Attempting to perform an action in Streamer.bot...")
        await self._websocket.send(json.dumps(payload))
        self._log.debug("Action completed.")

        return
