
from abc import ABC, abstractmethod
from typing import Optional, Tuple
from app.lib.utils.compositor import TelegramMessageComposer
from app.lib.utils.logger import logger
from datetime import datetime
import traceback
from queue import Queue
from app import settings
import telegram
from telegram import Update, TelegramError
from telegram.ext import Dispatcher, MessageHandler, Filters, CallbackContext
import secrets
from app.lib.ai.model import PricePredictor, ML_MODEL
from app.lib.ai.trainer import Trainer
from app.lib.utils.QueryLogger import QueryLogger, QUERY_LOGGER
from app.lib.calc import calc_itself


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
                 dev_chat: int,
                 ml_model: PricePredictor = ML_MODEL,
                 database: QueryLogger = QUERY_LOGGER):

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
        self.ml_model = ml_model
        self.database = database

    @staticmethod
    def _gen_secret() -> str:
        return secrets.token_urlsafe(32)

    def get_own_secret(self):
        return self._own_secret

    class AbstractHandler(ABC):
        def __init__(self, tg_interface: 'Telegramv3Interface'):
            self._next_handler = None
            self.tg_if = tg_interface

        def set_next(self, handler):
            self._next_handler = handler
            return handler  # Enables method chaining

        @abstractmethod
        def handle(self, request):
            pass

    class TrainOnPrice(AbstractHandler):
        """
        This handles only messages from subscribed chats that are
        relpies to other messages and contains readable price
        """

        @staticmethod
        def _parse_price(message: str) -> Optional[float]:
            """
            Parse string to a float or return None if Value Error
            :param message: message to parse
            :return: float or None
            """
            try:
                return float(message)
            except ValueError:
                logger.info(f'Try to parse desired_price failed: {message}')
                return None

        def _get_message(self, chat_id: int, message_id: int
        ) -> Optional[Tuple[str, TelegramMessageComposer]]:
            with self.tg_if.database as db:
                stored_message: Tuple[str, TelegramMessageComposer] = db.get_tg_message(chat_id, message_id)
                # Tuple[str, str]: calculation_id, message_body

            if not stored_message:
                logger.info(f'No stored tg_message with chat_id={chat_id} and message_id={message_id}')
                return None

            if not isinstance(stored_message[0], str) or not len(stored_message[0]) == 40:
                logger.info(f'tg_message doesn\'t contain any calculation_id (maybe system message)')
                return None

            return stored_message

        def handle(self, update: Update):
            on_subscription = (update.effective_chat is not None and 
                               update.effective_chat.id == self.tg_if.chat_subscription
            )
            it_is_reply_message = (
                update.effective_message is not None and
                update.effective_message.reply_to_message is not None
            )
            price_is_readable = self._parse_price(update.effective_message.text) is not None

            if on_subscription and it_is_reply_message and price_is_readable:
                # 1. Try to parse Number of reply message
                desired_price = self._parse_price(update.effective_message.text)

                # 2. Get chat_id & message_id of the replied message
                chat_id = update.effective_message.reply_to_message.chat_id
                message_id = update.effective_message.reply_to_message.message_id

                # --- 3. Get correspond calculation_id ---
                calculation_id, message_composer = self._get_message(chat_id, message_id)

                # --- 4. Create Trainer, add sample, trigger training ---
                if calculation_id:
                    trainer = Trainer(self.tg_if.ml_model, self.tg_if.database)
                    trainer.add_sample(
                        calculation_id=calculation_id,
                        desired_dependent_price=desired_price
                    )
                    trainer.train()

                    # 5. Modify original message
                    with self.tg_if.database as db:
                        request_dto = db.get_request_dto(calculation_id)
                    calculation_dto = calc_itself.process_request(request_dto)
                    message_composer.calculation = calculation_dto
                    self.tg_if.edit_message(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=str(message_composer)
                    )

            elif self._next_handler:
                logger.debug(f'RepliedTextualMessage passing update to next handler')
                self._next_handler.handle(update)
            else:
                logger.debug("No handler could handle the request.")

    def _incoming_text_message_handler(
            self,
            update: Update,
            context: CallbackContext) -> None:

        chain_of_responsibility = self.TrainOnPrice(self)
        chain_of_responsibility.handle(update)

    def send_message(self,
                     chat_id: int,
                     text: str,
                     parse_mode: Optional[str] = 'MARKDOWN',
                     reply_to_message_id: Optional[int] = None,
                     ) -> Tuple[int, int] | Tuple[None, None]:
        """
        Send a message to given chat using Markdown by default.
        Return a tuple with chat_id, message_id or None if the message was not sent.
        :param chat_id: int, Telegram chat ID.
        :param text: str, Message text.
        :param parse_mode: Send Markdown or HTML. See the constants in :class:`telegram.ParseMode`
        :param reply_to_message_id: int, If you want to make a reply to the message.
        for the available modes.
        :return: tuple with chat_id, message_id or (None, None) if send failed
        """
        try:
            msg = self.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=True,
                reply_to_message_id=reply_to_message_id,
            )
            if isinstance(msg, telegram.Message):
                return chat_id, msg.message_id
        except TelegramError as e:
            logger.error(f'Message was not sent to Telegram chat {str(e)}')
        return None, None

    def edit_message(self,
                     chat_id: int,
                     message_id: int,
                     text: str,
                     parse_mode='MARKDOWN'
    ) -> Tuple[int, int] | Tuple[None, None]:
        try:
            msg = self.bot.edit_message_text(
                text=text,
                chat_id=chat_id,
                message_id=message_id,
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )
            if isinstance(msg, telegram.Message):
                return chat_id, msg.message_id
        except TelegramError as e:
            logger.error(f'Message was not sent to Telegram chat. {str(e)}')
        return None, None

    def process_webhook(self, json):
        update = Update.de_json(json, self.bot)
        self.dispatcher.process_update(update)

    def send_silent(self, msg: str) -> Optional[Tuple[int, int]]:
        """
        Sends msg to silent chat and return message id
        :param msg: Message in markdown
        :return: tuple with chat_id, message_id or (None, None) if send failed
        """
        return self.send_message(self.silent_chat, msg)

    def send_loud(self, msg: str) -> Optional[Tuple[int, int]]:
        """
        Sends msg to loud chat and return message id
        :param msg: Message in markdown
        :return: tuple with chat_id, message_id or (None, None) if send failed
        """
        return self.send_message(self.loud_chat, msg)

    @staticmethod
    def _make_trace(cause: Exception) -> str:
        return ''.join(
            traceback.format_exception(
                type(cause), cause, cause.__traceback__))

    def send_developer(self, msg: str, cause: Optional[Exception] = None) \
            -> Optional[Tuple[int, int]]:
        """
        Send message to a developer chat with trace from cause
        :param msg: message str
        :param cause: Exception cause or None
        :return: tuple with chat_id, message_id or None if send failed
        """
        timestamp = datetime.now().isoformat()
        trace = 'No Exception was provided'
        if cause:
            trace = self._make_trace(cause)

        text = f"{timestamp}:\n\n" \
                  f"Message: {msg}\n\n" \
                  f"Cause: {str(cause)}\n\n" \
                  f"Traceback: '{trace}'\n"
        chat_id, message_id = self.send_message(self.dev_chat, text, parse_mode=None)
        logger.error(f"DEV TG report has been sent: {msg}\n\n"
                     f"Cause: {str(cause)}\n\n"
                     f"Traceback: {trace}\n\n"
                     f"Chat ID: {chat_id}"
                     f"Message ID: {message_id}\n\n")
        return chat_id, message_id


class TGInterfaceManager:
    KEY = settings.TELEGRAMV3_BOT_APIKEY
    BASE = settings.TELEGRAMV3_BASE_APIURL
    TAIL = settings.TELEGRAMV3_WEBHOOK_ADDRESS

    def __init__(self):
        self._interface = None

    def get_interface(self) -> Telegramv3Interface:
        if not self._interface:
            self._interface = Telegramv3Interface(
                botfatherkey=settings.TELEGRAMV3_BOT_APIKEY,
                webhook_url=self.BASE + self.TAIL,
                chat_subscription=int(settings.TELEGRAMV3_SILENT_CHAT_ID),
                silent_chat=int(settings.TELEGRAMV3_SILENT_CHAT_ID),
                loud_chat=int(settings.TELEGRAMV3_LOUD_CHAT_ID),
                dev_chat=int(settings.TELEGRAMV3_DEVELOPER_CHAT_ID)
            )
        return self._interface

    def set_interface(self, tg_interface: Telegramv3Interface):
        self._interface = tg_interface


tg_interface_manager = TGInterfaceManager()
