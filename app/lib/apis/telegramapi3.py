
from abc import ABC, abstractmethod
from typing import Optional
from app.lib.utils.logger import logger
from datetime import datetime
import traceback
from queue import Queue
from app import settings
import telegram
from telegram import Update
from telegram.ext import Dispatcher, MessageHandler, Filters, CallbackContext
import secrets


class Telegramv3Interface:
    """
    Telegramv3Interface initializes and manages a Telegram bot using webhook integration.

    This class:
    - Sets up a webhook-based Telegram bot using the provided bot token and webhook URL.
    - Defines a message dispatching system using the `telegram.ext.Dispatcher`.
    - Implements a handler chain for processing incoming text messages, currently including a handler
      for replies to existing messages within a specific subscribed chat.
    - Provides methods to send messages to designated chats (silent, loud, and developer).
    - Can report errors and exceptions to a developer chat, including full tracebacks.

    Parameters:
        botfatherkey (str): Telegram bot API token.
        webhook_url (str): Public webhook URL to receive updates from Telegram.
        chat_subscription (int): Chat ID from which replies are monitored.
        silent_chat (int): Chat ID used for quiet messages.
        loud_chat (int): Chat ID used for alerting messages.
        dev_chat (int): Chat ID where error reports or debug messages are sent.

    Main Methods:
        - process_webhook(json): Process incoming webhook update from Telegram.
        - send_silent(msg): Send a markdown message to the silent chat.
        - send_loud(msg): Send a markdown message to the loud chat.
        - send_developer(msg, cause): Send error/debug messages with optional exception trace.
        - get_own_secret(): Returns the secret used for webhook verification.

    Nested Classes:
        - AbstractHandler: An abstract base for implementing the Chain of Responsibility.
        - RepliedTextualMessage: A concrete handler that processes reply messages from a subscribed chat.

    Private Methods:
        - _send_message(): Internal utility to send a Telegram message.
        - _incoming_text_message_handler(): Entry point for the dispatcher to handle text messages.
        - _gen_secret(): Generates a secure secret token for webhook verification.
    """
    def __init__(self,
                 botfatherkey: str,
                 webhook_url: str,
                 chat_subscription: int,
                 silent_chat: int,
                 loud_chat: int,
                 dev_chat: int):

        self.bot = telegram.Bot(token=botfatherkey)
        self.dispatcher = Dispatcher(
            bot=self.bot, update_queue=Queue(), use_context=True
        )
        self.dispatcher.add_handler(MessageHandler(
            Filters.text, self._incoming_text_message_handler)
        )

        self.chat_subscription = chat_subscription  # A chat messages from which are being monitored
        self.silent_chat = silent_chat
        self.loud_chat = loud_chat
        self.dev_chat = dev_chat

        self._own_secret = self._gen_secret()
        self.bot.set_webhook(url=webhook_url, secret_token=self._own_secret)

    @staticmethod
    def _gen_secret() -> str:
        return secrets.token_urlsafe(32)

    def get_own_secret(self):
        return self._own_secret

    class AbstractHandler(ABC):
        def __init__(self, chat_subscription: int):
            self._next_handler = None
            self.chat_subscription = chat_subscription

        def set_next(self, handler):
            self._next_handler = handler
            return handler  # Enables method chaining

        @abstractmethod
        def handle(self, request):
            pass

    class RepliedTextualMessage(AbstractHandler):
        """
        This handles only messages from subscribed chats that are relpies to other messages
        """

        def __init__(self, chat_subscription: int):
            super().__init__(chat_subscription)

        def handle(self, update: Update):
            on_subscription = (update.effective_chat is not None and 
                               update.effective_chat.id == self.chat_subscription
            )
            is_reply_message = (
                update.effective_message is not None and
                update.effective_message.reply_to_message is not None
            )
            if on_subscription and is_reply_message:
                logger.debug(f'RepliedTextualMessage is going to handle this update')
            elif self._next_handler:
                logger.debug(f'RepliedTextualMessage passing update to next handler')
                self._next_handler.handle(update)
            else:
                logger.debug("No handler could handle the request.")

    def _incoming_text_message_handler(
            self,
            update: Update,
            context: CallbackContext) -> None:

        chain_of_responsibility = self.RepliedTextualMessage(self.chat_subscription)
        chain_of_responsibility.handle(update)

    def _send_message(self, chat_id: int, text: str, parse_mode: Optional[str] = 'MARKDOWN'):
        msg = self.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode
        )
        return msg.message_id

    def process_webhook(self, json):
        update = Update.de_json(json, self.bot)
        self.dispatcher.process_update(update)

    def send_silent(self, msg: str) -> int:
        """
        Sends msg to silent chat and return message id
        :param msg: Message in markdown
        :return: sent message id
        """
        return self._send_message(self.silent_chat, msg)

    def send_loud(self, msg: str):
        """
        Sends msg to loud chat and return message id
        :param msg: Message in markdown
        :return: sent message id
        """
        return self._send_message(self.loud_chat, msg)

    def send_developer(self, msg: str, cause: Optional[Exception] = None):
        try:
            timestamp = datetime.now().isoformat()

            txt_cause = 'No exception provided'
            trace = 'No exception provided'
            if cause is not None:
                txt_cause = str(cause)
                trace = str().join(traceback.format_exception(
                    type(cause), cause, cause.__traceback__
                    )
                )
            message = f"{timestamp}:\n\n" \
                      f"Message: {msg}\n\n" \
                      f"Cause: {txt_cause}\n\n" \
                      f"Traceback: '{trace}'\n"
            self._send_message(self.dev_chat, message, parse_mode=None)
            logger.error(f"DEV TG report has been sent: {msg}\n\n"
                         f"Cause: {txt_cause}\n\n"
                         f"Traceback: {trace}")
        except Exception as e:
            logger.error(f"Failed to send dev tg report\n\n"
                         f"{str(e)}\n\n"
                         f"{traceback.format_exc()}\n\n"
                         f"{msg}")


KEY = settings.TELEGRAMV3_BOT_APIKEY
BASE = settings.TELEGRAMV3_BASE_APIURL
TAIL = settings.TELEGRAMV3_WEBHOOK_ADDRESS


class TGInterfaceManager:

    def __init__(self):
        self._interface = None

    def get_interface(self) -> Telegramv3Interface:
        if not self._interface:
            self._interface = Telegramv3Interface(
                botfatherkey=settings.TELEGRAMV3_BOT_APIKEY,
                webhook_url=BASE+TAIL,
                chat_subscription=int(settings.TELEGRAMV3_SILENT_CHAT_ID),
                silent_chat=int(settings.TELEGRAMV3_SILENT_CHAT_ID),
                loud_chat=int(settings.TELEGRAMV3_LOUD_CHAT_ID),
                dev_chat=int(settings.TELEGRAMV3_DEVELOPER_CHAT_ID)
            )
        return self._interface

    def set_interface(self, tg_interface: Telegramv3Interface):
        self._interface = tg_interface


tg_interface_manager = TGInterfaceManager()
