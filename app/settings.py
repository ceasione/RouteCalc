
import os
from dotenv import load_dotenv
from pathlib import Path


load_dotenv(Path('storage/.env'), verbose=True)


DEV_MACHINE = True if os.getenv('DEV_MACHINE') == 'true' else False
LOGLEVEL = os.getenv('LOGLEVEL', 'INFO')

GOOGLE_APIADR = os.getenv('GOOGLE_APIADR', 'https://maps.googleapis.com/maps/api/distancematrix/json')
GOOGLE_APIKEY_PROD = os.getenv('GOOGLE_APIKEY_PROD')
GOOGLE_APIKEY_DEV = os.getenv('GOOGLE_APIKEY_DEV')
GOOGLE_APIKEY = GOOGLE_APIKEY_DEV if DEV_MACHINE else GOOGLE_APIKEY_PROD

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
SMS_ALPHANAME = os.getenv('SMS_ALPHANAME', 'Inter Smart')
SMS_TEXT_REDIAL_PHONE = os.getenv('SMS_TEXT_REDIAL_PHONE', '+380687070075')
SMS_BLACKLIST = list()

TELEGRAM_BOT_APIKEY = os.getenv('TELEGRAM_BOT_APIKEY')
TELEGRAM_DIRECT_CHAT_ID = os.getenv('TELEGRAM_DIRECT_CHAT_ID')
TELEGRAM_SILENT_CHAT_ID = os.getenv('TELEGRAM_SILENT_CHAT_ID')
TELEGRAM_LOUD_CHAT_ID = os.getenv('TELEGRAM_LOUD_CHAT_ID')
TELEGRAM_DEVELOPER_CHAT_ID = os.getenv('TELEGRAM_DEVELOPER_CHAT_ID')

TELEGRAMV3_BASE_APIURL = os.getenv('TELEGRAMV3_BASE_APIURL',
                                   'https://api.intersmartgroup.com')
TELEGRAMV3_WEBHOOK_ADDRESS = os.getenv('TELEGRAMV3_WEBHOOK_ADDRESS', '/tg-webhook-routecalc/')
TELEGRAMV3_BOT_APIKEY = os.environ['TELEGRAMV3_BOT_APIKEY']  # Use different method to raise when its missing
TELEGRAMV3_DEVELOPER_CHAT_ID = os.environ['TELEGRAMV3_DEVELOPER_CHAT_ID']
TELEGRAMV3_SILENT_CHAT_ID = os.environ['TELEGRAMV3_SILENT_CHAT_ID']
TELEGRAMV3_LOUD_CHAT_ID = os.environ['TELEGRAMV3_LOUD_CHAT_ID']

