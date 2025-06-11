
import os
import socket
from dotenv import load_dotenv

load_dotenv()

GOOGLE_APIADR = os.getenv('GOOGLE_APIADR')
DEV_HOSTNAME = os.getenv('DEV_HOSTNAME')
isDeveloperPC = True if DEV_HOSTNAME == 'ltone' else False
GOOGLE_APIKEY_PROD = os.getenv('GOOGLE_APIKEY_PROD')
GOOGLE_APIKEY_DEV = os.getenv('GOOGLE_APIKEY_DEV')
GOOGLE_APIKEY = GOOGLE_APIKEY_DEV if socket.gethostname() == DEV_HOSTNAME else GOOGLE_APIKEY_PROD

DEPOTPARK_LOC = os.getenv('DEPOTPARK_LOC', 'storage/depotpark.json')
STATEPARK_LOC = os.getenv('STATEPARK_LOC', 'storage/statepark.json')
VEHICLES_LOC = os.getenv('VEHICLES_LOC', 'storage/vehicles.json')
CURRENCY_LOC = os.getenv('CURRENCY_LOC', 'storage/currencies.json')

DEPOTPARK_RESERVE_LOC = os.getenv('DEPOTPARK_RESERVE_LOC', 'initial_storage/depotpark.json')
STATEPARK_RESERVE_LOC = os.getenv('STATEPARK_RESERVE_LOC', 'initial_storage/statepark.json')
VEHICLES_RESERVE_LOC = os.getenv('VEHICLES_RESERVE_LOC', 'initial_storage/vehicles.json')
CURRENCY_RESERVE_LOC = os.getenv('CURRENCY_RESERVE_LOC', 'initial_storage/currencies.json')

CACHE_LOC = os.getenv('CACHE_LOC', 'storage/cache.sqlite')
CACHE_RESERVE_LOC = os.getenv('CACHE_RESERVE_LOC', 'initial_storage/cache.sqlite')

QUERYLOG_DB_LOC = os.getenv('QUERYLOG_DB_LOC', 'storage/QueryLog.sqlite')
QUERYLOG_DB_RESERVE_LOC = os.getenv('QUERYLOG_DB_RESERVE_LOC', 'initial_storage/QueryLog.sqlite')

AI_MODEL_LOC = os.getenv('AI_MODEL_LOC', 'storage/4L1500*30*40*0.01.leakyrelu.keras')
AI_MODEL_RESERVE_LOC = os.getenv('AI_MODEL_RESERVE_LOC', 'initial_storage/4L1500*30*40*0.01.leakyrelu.keras')

BLACKLIST_FILE_LOC = os.getenv('BLACKLIST_FILE_LOC', 'storage/blacklist.txt')
BLACKLIST_RESERVE_LOC = os.getenv('BLACKLIST_RESERVE_LOC', 'initial_storage/blacklist.txt')

SMS_APIADR = os.getenv('SMS_APIADR', 'https://im.smsclub.mobi/sms/send')
SMS_APIKEY = os.getenv('SMS_APIKEY')
SMS_ALPHANAME = os.getenv('SMS_ALPHANAME')
SMS_TEXT_REDIAL_PHONE = os.getenv('SMS_TEXT_REDIAL_PHONE', '+380687070075')
SMS_BLACKLIST = list()

TELEGRAM_BOT_APIKEY = os.getenv('TELEGRAM_BOT_APIKEY')
TELEGRAM_DIRECT_CHAT_ID = os.getenv('TELEGRAM_DIRECT_CHAT_ID')
TELEGRAM_SILENT_CHAT_ID = os.getenv('TELEGRAM_SILENT_CHAT_ID')
TELEGRAM_LOUD_CHAT_ID = os.getenv('TELEGRAM_LOUD_CHAT_ID')
TELEGRAM_DEVELOPER_CHAT_ID = os.getenv('TELEGRAM_DEVELOPER_CHAT_ID')

LOGLEVEL = os.getenv('LOGLEVEL', 'INFO')
