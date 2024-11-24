import settings
import telegram


APIKEY = settings.TELEGRAM_BOT_APIKEY
SILENT_CHAT_ID = settings.TELEGRAM_SILENT_CHAT_ID
LOUD_CHAT_ID = settings.TELEGRAM_LOUD_CHAT_ID
DEVELOPER_CHAT_ID = settings.TELEGRAM_DEVELOPER_CHAT_ID


bot = telegram.Bot(token=APIKEY)


def send_silent(msg: str) -> None:
    bot.send_message(chat_id=SILENT_CHAT_ID, text=msg, parse_mode='MARKDOWN')


def send_loud(msg: str) -> None:
    bot.send_message(chat_id=LOUD_CHAT_ID, text=msg, parse_mode='MARKDOWN')


def send_developer(msg: str) -> None:
    bot.send_message(chat_id=DEVELOPER_CHAT_ID, text=msg, parse_mode='MARKDOWN')
