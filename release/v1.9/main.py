from lib.calc.place import Place
from lib.calc.depotpark import DepotPark
from lib.utils.cache import Cache
from flask import Flask
from flask import request
import json
from lib.calc import vehicles
from flask import Response
from copy import copy
from lib.utils import compositor, number_tools, utils
from lib.apis import smsapi, telegramapi2
from lib.utils.QueryLogger import query_logger_factory
import settings
from flask_cors import CORS
import traceback

"""
pip install flask
pip install flask-cors
pip install requests
pip install python-telegram-bot --upgrade
"""


DEPOT_PARK = DepotPark()
CACHE = Cache()
LOGGER = query_logger_factory()
MAX_REQUESTS = settings.MAX_REQUESTS

app = Flask(__name__)
CORS = CORS(app)


@app.route('/get-available-vehicles/', methods=['GET'])
def get_vehicles():

    resp = Response(response=json.dumps(vehicles.VEHICLES, cls=vehicles.VehicleEncoder, ensure_ascii=False),
                    content_type='application/json; charset=utf-8')
    resp.headers.add('Access-Control-Allow-Origin', '*')

    return resp


request_example = {'intent': str('calc'+'callback'),
                   'from': {'name_short': str(''),
                            'name_long': str(''),
                            'lat': float(0),
                            'lng': float(0),
                            'countrycode': str('')},
                   'to':   {'name_short': str(''),
                            'name_long': str(''),
                            'lat': float(0),
                            'lng': float(0),
                            'countrycode': str('')},
                   'transport_id': int(0),
                   'phone_number': str('12 digits'),
                   'locale': str('ru_UA')}


def __validate_transport_id(vehicle_id):

    for vehicle in vehicles.VEHICLES:

        if vehicle.id == vehicle_id:

            return vehicle_id

    raise ValueError('Unknown vehicle_id')


def __select_vehicle(vehicle_id):

    for vehicle in vehicles.VEHICLES:

        if vehicle.id == vehicle_id:

            return vehicle


def __validate_request(input_json):

    num_validator = number_tools.get_instance()
    obj = json.loads(input_json)

    if obj['intent'] != 'calc' and obj['intent'] != 'callback':
        raise ValueError('Expected intent "calc" or "callback". Got ' + obj['intent'])

    if len(obj['from']['name_short']) < 1 or len(obj['to']['name_short']) < 1:
        raise ValueError('Field name_short could not be empty')

    if len(obj['from']['name_long']) < 1 or len(obj['to']['name_long']) < 1:
        raise ValueError('Field name_long could not be empty')

    return {'intent':   str(obj['intent']),
            'from':     {'name_short': str(obj['from']['name_short']),
                         'name_long': str(obj['from']['name_long']),
                         'lat': float(obj['from']['lat']),
                         'lng': float(obj['from']['lng']),
                         'countrycode': str(obj['from']['countrycode'])},
            'to':       {'name_short': str(obj['to']['name_short']),
                         'name_long': str(obj['to']['name_long']),
                         'lat': float(obj['to']['lat']),
                         'lng': float(obj['to']['lng']),
                         'countrycode': str(obj['to']['countrycode'])},
            'transport_id': __validate_transport_id(int(obj['transport_id'])),
            'phone_number': num_validator.validate_phone_ukr(obj['phone_number']),
            'locale': obj['locale'] if obj.get('locale') is not None else 'ru_UA'}  # need to test this line !!!


def __calculate_distance(a, b, c, d):

    return 0 + \
           a.distance_to(b)[0].distance + \
           b.distance_to(c)[0].distance + \
           c.distance_to(d)[0].distance


def __distance_ratio(dist: float) -> float:
    # dist valued in meters
    # kdist valued in kilometers
    kdist = dist/1000.0

    if kdist < 0.0:
        raise RuntimeError('Calculated distance appeared to be negative')
    elif 0.0 <= kdist < 50.0:
        return 2.8
    elif 50.0 <= kdist < 100.0:
        return 2.2
    elif 100.0 <= kdist < 170.0:
        return 1.6
    elif 170.0 <= kdist < 200.0:
        return 1.3
    elif 200.0 <= kdist < 300.0:
        return 1.1
    elif 300.0 <= kdist < 600.0:
        return 1.0
    elif 600.0 <= kdist < 800.0:
        return 0.97
    elif 800.0 <= kdist < 1000.0:
        return 0.93
    elif 1000.0 <= kdist < 1200.0:
        return 0.86
    elif 1200.0 <= kdist < 1500.0:
        return 0.80
    else:
        return 0.78


def __calculate_route_details(rqst):

    place_a = Place(rqst['from']['lat'], rqst['from']['lng'],
                    name=rqst['from']['name_short'],
                    name_long=rqst['from']['name_long'])
    place_b = Place(rqst['to']['lat'], rqst['to']['lng'],
                    name=rqst['to']['name_short'],
                    name_long=rqst['to']['name_long'])

    starting_depot = copy(DEPOT_PARK.select_closest_starting_depot(place_a))
    ending_depot = copy(DEPOT_PARK.select_closest_ending_depot(place_b))
    route = [starting_depot, place_a, place_b, ending_depot]
    visible_route = utils.__merge_same(route)
    distance = __calculate_distance(route[0], route[1], route[2], route[3])  # here we have distance in meters
    ratio = 1.0 * starting_depot.departure_ratio * ending_depot.arrival_ratio * __distance_ratio(distance)
    selected_vehicle = __select_vehicle(rqst['transport_id'])
    price = float(selected_vehicle.price) * ratio

    cost = (distance / 1000) * price  # here we have to use kilometers


    return {'vehicle': selected_vehicle,
            'total_distance': distance,
            'price': price,
            'cost': cost,
            'route': visible_route,
            'place_a': place_a,
            'place_b': place_b,
            'client_phone': rqst['phone_number']}


def __gen_response(http_status: int, json_status: str, details: str = '') -> Response:

    if json_status not in ('SMS_SENT',
                           'SMS_ERROR',
                           'MAX_DAILY_REQUESTS_EXCEEDED',
                           'REGION_NOT_IMPLEMENTED',
                           'CALLBACK_SCHEDULED',
                           'ERROR'):
        raise RuntimeError('Internal error 8')

    resp = Response(response=json.dumps({'status': json_status,
                                         'details': details},
                                        ensure_ascii=False),
                    status=http_status,
                    content_type='application/json; charset=utf-8')

    resp.headers.add('Access-Control-Allow-Origin', '*')
    return resp


@app.route('/do-submit-calculation/', methods=['POST'])
def submit():

    try:
        # Strange code needed for converting, don't know why different types occur
        if isinstance(request.json, str):
            s_request = request.json
        elif isinstance(request.json, dict):
            s_request = json.dumps(request.json, ensure_ascii=False)
        else:
            raise TypeError('Expected input json be str or dict')
        # Strange code needed for converting, don't know why different types occur

        rqst = __validate_request(s_request)
    except (TypeError, ValueError, KeyError) as e:
        return __gen_response(400, 'ERROR', details=str(e.args))

    # countrycode check
    from_is_ua = rqst['from']['countrycode'] == 'UA' or rqst['from']['countrycode'] == 'ua'
    to_is_ua = rqst['to']['countrycode'] == 'UA' or rqst['to']['countrycode'] == 'ua'

    try:
        details = __calculate_route_details(rqst)
    except RuntimeError as e:
        telegramapi2.send_developer(f'Calculator error!\n\nRequest = {rqst}\n\nError = {e.args}')
        return __gen_response(500, 'ERROR', details=str(e.args))

    today_requests = LOGGER.get_today_requests_count(rqst['phone_number'])  # depends on +380 or 380 below
    # This was made for distinguish calc and callback. Callback should not increment today_requests

    if rqst['intent'] == 'calc' and today_requests <= MAX_REQUESTS:
        telegramapi2.send_silent(compositor.compose_telegram(rqst['intent'], details, rqst['locale']))
        LOGGER.put_request(phone_number=rqst["phone_number"],  # +380... or 380... for logging
                           query=s_request,
                           response=json.dumps([compositor.compose_telegram(rqst['intent'], details, rqst['locale']),
                                                compositor.compose_sms(details, rqst['locale'])], ensure_ascii=False))
        # if not from_is_ua or not to_is_ua:
        #     return __gen_response(501, 'REGION_NOT_IMPLEMENTED')

        smsapi.send_sms(rqst['phone_number'], compositor.compose_sms(details, rqst['locale']))
        return __gen_response(200, 'SMS_SENT')

    elif rqst['intent'] == 'calc' and today_requests > MAX_REQUESTS:
        telegramapi2.send_silent(compositor.compose_telegram(rqst['intent'], details, rqst['locale']))
        LOGGER.put_request(phone_number=rqst["phone_number"],  # +380... or 380... for logging
                           query=s_request,
                           response=json.dumps([compositor.compose_telegram(rqst['intent'], details, rqst['locale']),
                                                compositor.compose_sms(details, rqst['locale'])], ensure_ascii=False))
        return __gen_response(403, 'MAX_DAILY_REQUESTS_EXCEEDED')

    elif rqst['intent'] == 'callback':
        telegramapi2.send_loud(compositor.compose_telegram(rqst['intent'], details, rqst['locale']))
        LOGGER.put_request(phone_number='+'+rqst['phone_number'],  # +380... or 380... for logging
                           query=s_request,
                           response=json.dumps([compositor.compose_telegram(rqst['intent'], details, rqst['locale']),
                                                compositor.compose_sms(details, rqst['locale'])], ensure_ascii=False))
        return __gen_response(200, 'CALLBACK_SCHEDULED')

    else:
        raise RuntimeError('Internal error 9')


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
