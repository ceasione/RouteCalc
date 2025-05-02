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
pip install numpy
pip install matplotlib
pip install seaborn
pip install tensorflow
pip install keras
"""

CACHE = cache.cache_instance_factory()
LOGGER = query_logger_factory()
MAX_REQUESTS = settings.MAX_REQUESTS

app = Flask(__name__)
CORS = CORS(app)


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
        calculation_dto = calc_itself.calculate_route_ai(rqst)
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
        tg_msg = '*BLACKLISTED*\n\n'+tg_msg
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
                       query=json.dumps(dto.to_dict(), ensure_ascii=False),
                       response=json.dumps([tg_msg, sms_msg], ensure_ascii=False))

    blacklisted = blacklist.check(num, ip)
    if not blacklisted:
        telegramapi2.send_loud(tg_msg)
        smsapi.send_sms(num, sms_msg)
    elif blacklisted:
        blacklist.spread(num, ip)
        telegramapi2.send_loud('*BLACKLISTED*\n\n'+tg_msg)

    return __gen_response(200, 'CALLBACK_SCHEDULED')


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
