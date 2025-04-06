from impsettings import settings
import requests

APIKEY = settings.TELEGRAM_BOT_APIKEY
SILENT_CHAT_ID = settings.TELEGRAM_SILENT_CHAT_ID
LOUD_CHAT_ID = settings.TELEGRAM_LOUD_CHAT_ID
DEVELOPER_CHAT_ID = settings.TELEGRAM_DEVELOPER_CHAT_ID
URL = f'https://api.telegram.org/bot{APIKEY}/sendMessage'


def send_silent(msg):
    payload = {'chat_id': SILENT_CHAT_ID, 'text': msg, 'parse_mode': 'MARKDOWN'}
    requests.get(URL, params=payload)


def send_loud(msg):
    payload = {'chat_id': LOUD_CHAT_ID, 'text': msg, 'parse_mode': 'MARKDOWN'}
    requests.get(URL, params=payload)


def send_developer(msg):
    payload = {'chat_id': DEVELOPER_CHAT_ID, 'text': msg, 'parse_mode': 'MARKDOWN'}
    requests.get(URL, params=payload)
