
from lib.utils.cache import Cache
from flask import Flask
from flask import request
import json
from flask import Response
from lib.utils import compositor
from lib.calc import vehicles
from lib.apis import smsapi, telegramapi2
from lib.utils.QueryLogger import query_logger_factory
import settings
from flask_cors import CORS
import lib.utils.blacklist as blacklist
import lib.utils.request_processor as request_processor
import lib.calc.calc_itself as calc_itself
from lib.utils.DTOs import CalculationDTO
import lib.utils.number_tools as number_tools
from lib.apis.googleapi import ZeroDistanceResultsError
from lib.utils.number_tools import WrongNumberError


"""
pip install flask
pip install flask-cors
pip install requests
pip install python-telegram-bot --upgrade
pip install asyncio
"""


CACHE = Cache()
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


@app.route('/blacklist/<string:req>', methods=['GET'])
def blacklist_add(req: str):
    blacklist.append(req)
    return __gen_response(201, f'BLACKLISTED', req)


@app.route('/get-available-vehicles/', methods=['GET'])
def get_vehicles():

    resp = Response(response=json.dumps(vehicles.VEHICLES, cls=vehicles.VehicleEncoder, ensure_ascii=False),
                    content_type='application/json; charset=utf-8')
    resp.headers.add('Access-Control-Allow-Origin', '*')

    return resp


@app.route('/do-submit-calculation/', methods=['POST'])
def submit():

    try:
        rqst = request_processor.preprocess(request)
    except (TypeError, ValueError, KeyError) as e:
        telegramapi2.send_developer('Request processing failed', e)
        return __gen_response(400, 'ERROR', details="Request processing error")

    try:
        route_calculations = calc_itself.calculate_route(rqst)
    except Exception as e:
        message = f'Calculator itself error\n\nRequest = {json.dumps(rqst, ensure_ascii=False)}\n\nException = {str(e)}'
        telegramapi2.send_developer(message, e)
        return __gen_response(500, 'ERROR', details="Calc itself error")

    calculation_dto = compositor.make_calculation_dto(route_calculations, rqst['locale'])

    tg_msg = compositor.compose_telegram(
        rqst['intent'], 
        calculation_dto,
        rqst['url'], 
        rqst['ip'],
        rqst["phone_number"])

    sms_msg: str = compositor.make_sms_text(calculation_dto)

    LOGGER.put_request(phone_number=rqst["phone_number"],
                       query=json.dumps(rqst, ensure_ascii=False),
                       response=json.dumps([tg_msg, sms_msg], ensure_ascii=False))

    blacklisted = blacklist.check(rqst["phone_number"], rqst['ip'])
    if blacklisted:
        blacklist.spread(rqst["phone_number"], rqst['ip'])
        telegramapi2.send_silent(f'BLACKLISTED\n\n{tg_msg}')
        return __gen_response(200, 'SMS_SENT')
    
    if rqst['intent'] == 'calc':

        requests_exceeded = LOGGER.get_today_requests_count(rqst['phone_number']) > MAX_REQUESTS
        if requests_exceeded:
            telegramapi2.send_silent(f'DAILY REQUESTS EXCEEDED\n\n{tg_msg}')
            return __gen_response(403, 'MAX_DAILY_REQUESTS_EXCEEDED')

        telegramapi2.send_silent(tg_msg)
        smsapi.send_sms(rqst['phone_number'], sms_msg)
        return __gen_response(200, 'SMS_SENT')
    
    elif rqst['intent'] == 'callback':
        telegramapi2.send_loud(tg_msg)
        return __gen_response(200, 'CALLBACK_SCHEDULED')
    else:
        raise RuntimeError('Internal error 9')


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
                f'ZeroDistanceResultsError\n\nRequest = {json.dumps(rqst, ensure_ascii=False)}\n\nException = {str(e)}', e)
        finally:
            return __gen_response(404, 'ZeroDistanceResultsError', details=str(e))
    except Exception as e:
        try:
            telegramapi2.send_developer(
                f'Unspecified calculation error\n\nRequest = {json.dumps(rqst, ensure_ascii=False)}\n\nException = {str(e)}', e)
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
    settings.SMS_BLACKLIST = ('380953459607', )
    app.run(debug=True)
