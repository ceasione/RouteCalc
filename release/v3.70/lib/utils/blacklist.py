
import settings
from lib.utils import utils


# TODO Move blacklist from settings into here


def __renew():

    with open(settings.BLACKLIST_FILE_LOC, 'rt') as file:

        settings.SMS_BLACKLIST = list()

        for line in file:
            settings.SMS_BLACKLIST.append(line.rstrip())

    utils.log_safely(f'Successfully loaded BLACKLIST file')


def __lookup(req: str):

    return True if req in settings.SMS_BLACKLIST else False


def append(req: str):

    # print('---BEFORE---')
    # with open(settings.BLACKLIST_FILE_LOC, 'rt') as file:
    #     print(file.read())
    # print('---BEFORE---')

    with open(settings.BLACKLIST_FILE_LOC, 'at') as file:
        file.write(f'{req}\n')

    # print('---AFTER---')
    # with open(settings.BLACKLIST_FILE_LOC, 'rt') as file:
    #     print(file.read())
    # print('---AFTER---')
        

def spread(phone_number, client_ip):
    __renew()

    num_is_present = __lookup(phone_number)
    ip_is_present = __lookup(client_ip)

    if num_is_present and ip_is_present:
        return

    if num_is_present:
        append(client_ip)

    if ip_is_present:
        append(phone_number)

    __renew()


def check(phone_number, client_ip):
    __renew()

    return True if (__lookup(phone_number) or __lookup(client_ip)) else False


def check_ip(client_ip):
    __renew()
    return True if __lookup(client_ip) else False

