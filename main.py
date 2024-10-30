
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
import traceback
import lib.utils.blacklist as blacklist
import lib.utils.request_processor as request_processor
import lib.calc.calc_itself as calc_itself


"""
pip install flask
pip install flask-cors
pip install requests
pip install python-telegram-bot --upgrade
"""


CACHE = Cache()
LOGGER = query_logger_factory()
MAX_REQUESTS = settings.MAX_REQUESTS

app = Flask(__name__)
CORS = CORS(app)


def __gen_response(http_status: int, json_status: str, details: str = '', workload: dict = None) -> Response:

    if json_status not in ('SMS_SENT',
                           'SMS_ERROR',
                           'MAX_DAILY_REQUESTS_EXCEEDED',
                           'REGION_NOT_IMPLEMENTED',
                           'CALLBACK_SCHEDULED',
                           'ERROR',
                           'BLACKLISTED',
                           'WORKLOAD'):
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
        return __gen_response(400, 'ERROR', details=str(e.args))

    try:
        route_calculations = calc_itself.calculate_route(rqst)
    except RuntimeError as e:
        telegramapi2.send_developer(f'Calculator error!\n\nRequest = {json.dumps(rqst, ensure_ascii=False)}\n\nError = {e.args}')
        return __gen_response(500, 'ERROR', details=str(e.args))

    tg_msg = compositor.compose_telegram(
        rqst['intent'], 
        route_calculations, 
        rqst['locale'], 
        rqst['url'], 
        rqst['ip'])

    sms_msg: str = compositor.make_sms_text(route_calculations["place_a"].name,
                                            route_calculations["place_b"].name,
                                            route_calculations['vehicle'].name_ua,
                                            route_calculations['vehicle'].price_per_ton,
                                            route_calculations['cost'])

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
        telegramapi2.send_loud(
            compositor.compose_telegram(
                rqst['intent'], 
                route_calculations, 
                rqst['locale'], 
                rqst['url'], 
                rqst['ip']))
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
        route_calculations = calc_itself.calculate_route(rqst)
    except RuntimeError as e:
        telegramapi2.send_developer(
            f'Calculator error!\n\nRequest = {json.dumps(rqst, ensure_ascii=False)}\n\nError = {e.args}')
        return __gen_response(500, 'ERROR', details=str(e.args))

    tg_msg = compositor.compose_telegram(
        rqst['intent'],
        route_calculations,
        rqst['locale'],
        rqst['url'],
        rqst['ip'])

    LOGGER.put_request(phone_number='smsless',
                       query=json.dumps(rqst, ensure_ascii=False),
                       response=json.dumps([tg_msg, 'smsless'], ensure_ascii=False))

    blacklisted = blacklist.check_ip(rqst['ip'])
    if blacklisted:
        telegramapi2.send_silent(f'BLACKLISTED\n\n{tg_msg}')
        return __gen_response(403, 'BLACKLISTED')
    else:
        telegramapi2.send_silent(tg_msg)
        return __gen_response(200, 'WORKLOAD', workload=compositor.compose_web(route_calculations, rqst['locale']))


@app.errorhandler(RuntimeError)
def handle_runtime_error(e: Exception) -> Response:
    telegramapi2.send_developer(f'Error')
    for stack_item in traceback.format_tb(e.__traceback__):
        telegramapi2.send_developer(stack_item)
    return __gen_response(500, 'ERROR', details=str(e.args))


@app.errorhandler(smsapi.SmsSendingError)
def handle_sms_error(e):
    return __gen_response(503, 'SMS_ERROR', details=str(e.args))


def create_app():
    settings.GOOGLE_APIKEY = settings.GOOGLE_APIKEY_PROD
    return app


if __name__ == '__main__':
    settings.GOOGLE_APIKEY = settings.GOOGLE_APIKEY_DEV
    settings.SMS_BLACKLIST = ('380953459607', )
    app.run(debug=True)
