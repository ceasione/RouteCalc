from flask import Flask
from flask import request
import json
from flask import Response
from app.lib.utils import compositor, cache
from app.lib.calc import vehicles
from app.lib.apis import smsapi, telegramapi2
from app.lib.utils.QueryLogger import query_logger_factory
from flask_cors import CORS
import app.lib.utils.blacklist as blacklist
import app.lib.utils.request_processor as request_processor
import app.lib.calc.calc_itself as calc_itself
from app.lib.utils.DTOs import CalculationDTO
import app.lib.utils.number_tools as number_tools
from app.lib.apis.googleapi import ZeroDistanceResultsError
from app.lib.utils.number_tools import WrongNumberError
from app.lib.loads.loads import Loads
from app.lib.loads.interface import TelegramInterface
from app.impsettings import settings

"""
pip install flask
pip install flask-cors
pip install requests

pip uninstall python-telegram-bot
pip uninstall urllib3
pip install urllib3==1.26.16
pip install python-telegram-bot==13.15
pip install pyngrok
"""

CACHE = cache.cache_instance_factory()
LOGGER = query_logger_factory()
MAX_REQUESTS = settings.MAX_REQUESTS

app = Flask(__name__)
CORS = CORS(app)


LOADS = Loads.from_file_storage(settings.LOADS_NOSQL_LOC)

if settings.isDeveloperPC:
    from pyngrok import ngrok
    tunnel = ngrok.connect('http://localhost:5000')
    INTERFACE = TelegramInterface(loads=LOADS,
                                  webhook_url=f'{tunnel.public_url}/webhook-aibot/',
                                  chat_id=settings.TELEGRAM_DEVELOPER_CHAT_ID)
else:
    INTERFACE = TelegramInterface(loads=LOADS)


def __gen_response(http_status: int, json_status: str, details: str = '', workload: CalculationDTO = None) -> Response:
    if json_status not in ('SMS_SENT',
                           'SMS_ERROR',
                           'MAX_DAILY_REQUESTS_EXCEEDED',
                           'REGION_NOT_IMPLEMENTED',
                           'CALLBACK_SCHEDULED',
                           'ERROR',
                           'BLACKLISTED',
                           'WORKLOAD',
                           'ZeroDistanceResultsError',
                           'WrongNumberError'):
        raise RuntimeError('Internal error 8')

    resp = Response(response=json.dumps({'status': json_status,
                                         'details': details,
                                         'workload': workload},
                                        ensure_ascii=False),
                    status=http_status,
                    content_type='application/json; charset=utf-8')

    resp.headers.add('Access-Control-Allow-Origin', '*')
    return resp


def __gen_response2(http_status: int, json_status: str, message: str = None, workload=None) -> Response:
    resp = Response(response=json.dumps({'status': json_status,
                                         'message': message,
                                         'workload': workload},
                                        ensure_ascii=False),
                    status=http_status,
                    content_type='application/json; charset=utf-8')

    resp.headers.add('Access-Control-Allow-Origin', '*')
    return resp


@app.route('/blacklist/<string:req>', methods=['GET'])
def blacklist_add(req: str):
    # https://api.intersmartgroup.com/blacklist/192.168.0.1
    # https://api.intersmartgroup.com/blacklist/380951234567
    blacklist.append(req)
    return __gen_response(201, f'BLACKLISTED', req)


@app.route('/get-available-vehicles/', methods=['GET'])
def get_vehicles():
    resp = Response(response=json.dumps(vehicles.VEHICLES, cls=vehicles.VehicleEncoder, ensure_ascii=False),
                    content_type='application/json; charset=utf-8')
    resp.headers.add('Access-Control-Allow-Origin', '*')
    return resp


@app.route('/calculate/', methods=['POST'])
def calculate():
    try:
        rqst = request_processor.preprocess(request)
    except (TypeError, ValueError, KeyError) as e:
        return __gen_response(400, 'ERROR', details=str(e.args))

    try:
        calculation_dto = compositor.make_calculation_dto(calc_itself.calculate_route(rqst), rqst['locale'])
    except ZeroDistanceResultsError as e:
        try:
            telegramapi2.send_developer(
                f'ZeroDistanceResultsError\n\nRequest = {json.dumps(rqst, ensure_ascii=False)}\n\nException = {str(e)}',
                e)
        finally:
            return __gen_response(404, 'ZeroDistanceResultsError', details=str(e))
    except Exception as e:
        try:
            telegramapi2.send_developer(
                f'Unspecified calc error\n\nRequest = {json.dumps(rqst, ensure_ascii=False)}\n\nException = {str(e)}',
                e)
        finally:
            return __gen_response(500, 'ERROR', details='Unspecified calculation error')

    tg_msg = compositor.compose_telegram(
        rqst['intent'],
        calculation_dto,
        rqst['url'],
        rqst['ip'],
        rqst["phone_number"])

    try:
        LOGGER.put_request(phone_number='nosms',
                           query=json.dumps(rqst, ensure_ascii=False),
                           response=json.dumps([tg_msg, 'nosms'], ensure_ascii=False))
    except Exception as e:
        try:
            telegramapi2.send_developer(
                f'LOGGER.put_request error\n\nException = {str(e)}', e)
        finally:
            pass

    blacklisted = blacklist.check_ip(rqst['ip'])
    if blacklisted:
        tg_msg = f'*BLACKLISTED*\n\n{tg_msg}'
    telegramapi2.send_silent(tg_msg)
    return __gen_response(200, 'WORKLOAD', workload=calculation_dto.to_dict())


@app.route('/submit/', methods=['POST'])
def submit_new():
    num_validator = number_tools.get_instance()
    try:
        dto = CalculationDTO.from_dict(request.json['dto'])
        num = num_validator.validate_phone_ukr(request.json['num'])
        url = request.json['url']
        ip = request.remote_addr
    except WrongNumberError as e:
        return __gen_response(422, 'WrongNumberError', details=str(e.args))
    except (TypeError, ValueError, KeyError) as e:
        return __gen_response(400, 'ERROR', details=str(e.args))

    tg_msg = compositor.compose_telegram(
        intent='callback',
        calculation=dto,
        url=url,
        ip=ip,
        phone_num=num)

    sms_msg = compositor.make_sms_text(dto)

    LOGGER.put_request(phone_number=num,
                       query='CalculationDTO object',
                       response=json.dumps([tg_msg, sms_msg], ensure_ascii=False))

    telegramapi2.send_loud(tg_msg)
    smsapi.send_sms(num, sms_msg)
    return __gen_response(200, 'CALLBACK_SCHEDULED')


@app.route('/loads/', methods=['GET'])
def get_loads():
    _loads = LOADS.expose_active_loads()
    return __gen_response2(http_status=200, json_status='success', workload={'len': len(_loads), 'loads': _loads})


@app.route('/driver/', methods=['GET'])
def get_driver():
    # /driver?load_id=4214$auth_num=470129384701
    load_id = request.args.get('load_id')
    auth_num = request.args.get('auth_num')
    if not load_id or auth_num:
        __gen_response2(http_status=400, json_status='error', message='load_id and client_num are required')

    from app.lib.loads.loads import Load
    try:
        driver, js_status, http_status = LOADS.get_load_by_id(load_id).get_driver_details(auth_num)
        return __gen_response2(http_status, js_status, workload=driver)
    except Load.NoSuchLoadID:
        return __gen_response2(400, 'No such load ID')


@app.route(f'/webhook-aibot/', methods=['POST'])
def loads_webhook():
    own_secret = INTERFACE.own_secret
    got_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if got_secret != own_secret:
        return "Forbidden", 403
    INTERFACE.catch_webhook(request.get_json())
    return "OK", 200


# This route is designed to be easily triggered from a mobile device,
# often via a simple browser request (e.g., URL typed into browser or QR code scan).
# Using GET allows for maximum accessibility without requiring a dedicated client or POST tooling.
# https://api.intersmartgroup.com/webhook_reset/?token=WEBHOOK_RESET_SECRET_TOKEN
@app.route('/webhook_reset/', methods=['GET'])
def webhook_reset():
    global INTERFACE
    try:
        if request.args.get('token') != settings.WEBHOOK_RESET_SECRET_TOKEN:
            return "Unauthorized", 403
        INTERFACE = TelegramInterface(loads=LOADS)
        return "DONE", 200
    except Exception as e:
        return f'FAIL: {e}', 500


@app.errorhandler(RuntimeError)
def handle_runtime_error(e: Exception) -> Response:
    telegramapi2.send_developer(f'Errorhandler error caught', e)
    return __gen_response(500, 'ERROR', details='Errorhandler error caught')


@app.errorhandler(smsapi.SmsSendingError)
def handle_sms_error(e):
    telegramapi2.send_developer(f'SmsSendingError', e)
    return __gen_response(503, 'SMS_ERROR', details='SmsSendingError')


def create_app():
    settings.GOOGLE_APIKEY = settings.GOOGLE_APIKEY_PROD
    return app


if __name__ == '__main__':
    settings.GOOGLE_APIKEY = settings.GOOGLE_APIKEY_DEV
    app.run(debug=True, use_reloader=False)
