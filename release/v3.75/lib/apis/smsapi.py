import settings
import requests
import lib.utils.utils as utils


APIKEY = settings.SMS_APIKEY
ALPHANAME = settings.SMS_ALPHANAME
HEADERS = {'Authorization': 'Bearer '+APIKEY}


class SmsSendingError(RuntimeError):
    pass


def send_sms(number, text):

    if number in settings.SMS_BLACKLIST:
        return  # rudimentary

    url = 'https://im.smsclub.mobi/sms/send'
    payload = {
        'phone': [number],
        'message': text,
        'src_addr': ALPHANAME
    }

    if not settings.isDeveloperPC:
        response = requests.post(url, json=payload, headers=HEADERS)
        if response.status_code != 200:
            raise SmsSendingError(f'status {response.status_code} {response.text}')


def get_sent_status(a_id):
    url = 'https://im.smsclub.mobi/sms/status'
    payload = {'id_sms': [a_id]}
    response = requests.post(url, json=payload, headers=HEADERS)
    response = response.json()
    utils.log_safely(response)


def check_balance():
    url = 'https://im.smsclub.mobi/sms/balance'
    response = requests.post(url, headers=HEADERS)
    return response.json()


def __get_available_alphanames():
    url = 'https://im.smsclub.mobi/sms/originator'
    response = requests.post(url, headers=HEADERS)
    response = response.json()
    utils.log_safely(response)


# test = SmsApi()
# a = __get_available_alphanames()
# print()
# test.send_sms('380953459607', 'test \ntest')
# test.get_sent_status('946036921')
# test.check_balance()
