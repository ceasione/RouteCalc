from app import settings
import requests
from app.lib.apis import telegramapi2
from app.lib.utils.logger import logger


APIKEY = settings.SMS_APIKEY
ALPHANAME = settings.SMS_ALPHANAME
HEADERS = {'Authorization': 'Bearer '+APIKEY}


class SmsSendingError(RuntimeError):
    pass


def send_sms(number, text):
    url = 'https://im.smsclub.mobi/sms/send'
    payload = {
        'phone': [number],
        'message': text,
        'src_addr': ALPHANAME
    }
    if not settings.DEV_MACHINE:
        response = requests.post(url, json=payload, headers=HEADERS)
        if response.status_code != 200:
            telegramapi2.send_developer(
                f'Error sending SMS\n'
                f'Status code: {response.status_code}\n'
                f'Response: {response.text}')


def get_sent_status(a_id):
    url = 'https://im.smsclub.mobi/sms/status'
    payload = {'id_sms': [a_id]}
    response = requests.post(url, json=payload, headers=HEADERS)
    response = response.json()
    logger.debug(response)


def check_balance():
    url = 'https://im.smsclub.mobi/sms/balance'
    response = requests.post(url, headers=HEADERS)
    return response.json()


def __get_available_alphanames():
    url = 'https://im.smsclub.mobi/sms/originator'
    response = requests.post(url, headers=HEADERS)
    response = response.json()
    logger.debug(response)
