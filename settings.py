import socket

GOOGLE_APIADR = 'https://maps.googleapis.com/maps/api/distancematrix/json'

GOOGLE_APIKEY_PROD = 'AIzaSyCQKtjuswR2c5fqEJng9k4hDKjWvgDnQLQ'
GOOGLE_APIKEY_DEV = 'AIzaSyAzEn9je1TvxCJSVIU7UIbv_p7UI8O4rMc'

if socket.gethostname() == 'ltone':
    GOOGLE_APIKEY = GOOGLE_APIKEY_DEV
    isDeveloperPC = True
else:
    GOOGLE_APIKEY = GOOGLE_APIKEY_PROD
    isDeveloperPC = False

GOOGLE_MAX_REQUEST_PLACES = 25

DEPOT_DB_LOC = 'dbs/DepotPark_v3.0.sqlite'
DEPOTPARK_NOSQL_LOC = 'dbs/depotpark_nosql.json'
STATEPARK_NOSQL_LOC = 'dbs/statepark_nosql.json'
CACHE_LOCATION = 'dbs/cache.sqlite'

LOADS_NOSQL_LOC = 'dbs/loads.json'

SMS_APIADR = 'https://im.smsclub.mobi/sms/send'
SMS_APIKEY = 'XXIxH1w1dLNEGmR'
SMS_ALPHANAME = 'Inter Smart'
SMS_BLACKLIST = ('380953459607', '380687070075', '380995617113', '380634472972')
BLACKLIST_FILE_LOC = '../routecalc_blacklist.txt'

TELEGRAM_BOT_APIKEY = '5030273725:AAGOindAi5C4VSvlMsi_hVK2W9IQH13ySwQ'
TELEGRAM_DIRECT_CHAT_ID = '51147855'
TELEGRAM_SILENT_CHAT_ID = '-700974331'
TELEGRAM_LOUD_CHAT_ID = '-649504862'
TELEGRAM_DEVELOPER_CHAT_ID_deprecated = '-756003763'
TELEGRAM_DEVELOPER_CHAT_ID = '-1002397696315'
TELEGRAM_LOADS_CHAT_ID = '-1002403956868'

LOG_DB_LOCATION = 'dbs/QueryLog.sqlite'

MAX_REQUESTS = 3

WORKING_DIR = '/home/olivercromwell/Python-Scrapy/RouteCalc/'

SMS_TEXT_REDIAL_PHONE = '+380687070075'
