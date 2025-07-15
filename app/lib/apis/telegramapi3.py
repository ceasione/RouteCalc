
from queue import Queue
from app import settings
import telegram
from telegram import Update, ext
import secrets


APIKEY = settings.TELEGRAMV3_BOT_APIKEY
# SILENT_CHAT_ID = settings.TELEGRAM_SILENT_CHAT_ID
# LOUD_CHAT_ID = settings.TELEGRAM_LOUD_CHAT_ID
DEVELOPER_CHAT_ID = settings.TELEGRAMV3_DEVELOPER_CHAT_ID


class Telegramv3Interface:
    """
    This class instantinates an Telegram Bot webhook, and registers handlers
    to process updates.
    Provides interface to send messages.
    """
    def __init__(self,
                 botfatherkey: str,
                 webhook_url: str):

        self.bot = telegram.Bot(token=botfatherkey)
        self.dispatcher = telegram.ext.Dispatcher(
            bot=self.bot, update_queue=Queue(), use_context=True
        )
        self.dispatcher.add_handler(telegram.ext.MessageHandler(
            telegram.ext.Filters.text, self._incoming_message_handler)
        )
        self._own_secret = self._gen_secret()
        self.bot.set_webhook(url=webhook_url, secret_token=self._own_secret)

    @staticmethod
    def _gen_secret() -> str:
        return secrets.token_urlsafe(32)

    def get_own_secret(self):
        return self._own_secret

    def _incoming_message_handler(
            self,
            update: telegram.Update,
            context: telegram.ext.CallbackContext) -> None:
        ...

    def _send_message(self, chat_id, text, parse_mode=None):
        return self.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode
        )

    def process_webhook(self, json):
        update = Update.de_json(json, self.bot)
        self.dispatcher.process_update(update)


KEY = settings.TELEGRAMV3_BOT_APIKEY
BASE = settings.TELEGRAMV3_BASE_APIURL
TAIL = settings.TELEGRAMV3_WEBHOOK_ADDRESS


class TGInterfaceManager:

    def __init__(self):
        self._interface = None

    def get_interface(self):
        if not self._interface:
            self._interface = Telegramv3Interface(
                botfatherkey=KEY,
                webhook_url=BASE+TAIL
            )
        return self._interface

    def set_interface (self, tg_interface: Telegramv3Interface):
        self._interface = tg_interface


tg_interface_manager = TGInterfaceManager()
