import settings
import telegram
from telegram.error import BadRequest
import traceback
from datetime import datetime
# import asyncio


APIKEY = settings.TELEGRAM_BOT_APIKEY
SILENT_CHAT_ID = settings.TELEGRAM_SILENT_CHAT_ID
LOUD_CHAT_ID = settings.TELEGRAM_LOUD_CHAT_ID
DEVELOPER_CHAT_ID = settings.TELEGRAM_DEVELOPER_CHAT_ID


bot = telegram.Bot(token=APIKEY)


def _send_message(chat_id, text, parse_mode=None):
    # asyncio.run(bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode))
    bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)


def send_message(chat_id: str, msg: str) -> None:
    try:
        _send_message(chat_id=chat_id, text=msg, parse_mode='MARKDOWN')
    except Exception as e:
        if isinstance(e, BadRequest) and "Can't parse entities" in str(e):
            _send_message(chat_id=chat_id, text=msg)
            error_message = f"{traceback.format_exc()}\n\n{msg}\n\nFailsafe msg has been sent"
            send_developer(error_message, e)
        else:
            error_message = f"{str(e)}\n\nTraceback: {traceback.format_exc()}\n\nmsg = {msg}"
            print(error_message)
            send_developer(error_message, e)


def send_silent(msg: str):
    send_message(SILENT_CHAT_ID, msg)


def send_loud(msg: str):
    send_message(LOUD_CHAT_ID, msg)


def log_safely(message):
    try:
        print(message)
    except OSError:
        pass


def send_developer(msg: str, cause: Exception) -> None:
    try:
        _send_message(chat_id=DEVELOPER_CHAT_ID, text=msg)
        timestamp = datetime.now().isoformat()
        tb = traceback.format_exception(type(cause), cause, cause.__traceback__)
        error_message = \
            f"{timestamp} Developer telegram report has been sent\n\nCause: {str(cause)}\n\nTraceback: {''.join(tb)}\n\nmsg = {msg}"
        log_safely(error_message)
    except Exception as e:
        timestamp = datetime.now().isoformat()
        error_message = f"{timestamp} Failed to send developer telegram report\n\n{str(e)}\n\nTraceback: {traceback.format_exc()}\n\nmsg = {msg}"
        log_safely(error_message)


# Test
test_text = "Application start and initialization"
send_developer(test_text, Exception('Test Exception'))
# send_message(chat_id=DEVELOPER_CHAT_ID, msg=test_text)
