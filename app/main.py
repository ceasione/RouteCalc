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


CACHE = cache.cache_instance_factory()
LOGGER = query_logger_factory()
MAX_REQUESTS = settings.MAX_REQUESTS

app = Flask(__name__)
CORS = CORS(app)


def __gen_response(http_status: int, json_status: str, details: str = '', workload: CalculationDTO = None) -> Response:

    """
    Additional layer for generating a standardized JSON HTTP response with validation and CORS headers.

    This function validates the `json_status` against a predefined list of allowed status values.
    If valid, it returns a Flask `Response` object containing a JSON payload with the specified
    status, optional details message, and an optional workload (typically a `CalculationDTO` object).
    It also adds a CORS header to allow cross-origin requests.

    :param http_status: HTTP status code to return (e.g., 200, 400, 500).
    :type http_status: int
    :param json_status: Application-level status string indicating result of the operation.
    :type json_status: str
    :param details: Optional string providing additional information about the response.
    :type details: str
    :param workload: Optional data payload to include in the response (e.g., calculation results).
    :type workload: CalculationDTO or None
    :raises RuntimeError: If the provided `json_status` is not in the allowed list.
    :return: A Flask Response object with JSON content and appropriate headers.
    :rtype: flask.Response
    """

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

    """
    Additional layer to generate a standardized JSON HTTP response with CORS headers.

    Constructs a Flask `Response` object containing a JSON payload with the specified status,
    message, and optional workload. Adds the `Access-Control-Allow-Origin: *` header to
    enable cross-origin requests.

    :param http_status: The HTTP status code for the response (e.g., 200, 400).
    :type http_status: int
    :param json_status: A string representing the application-level status (e.g., "ERROR", "SUCCESS").
    :type json_status: str
    :param message: Optional message providing additional information about the response.
    :type message: str, optional
    :param workload: Optional payload data to include in the response under the 'workload' key.
    :type workload: any, optional
    :return: A Flask `Response` object with JSON content and appropriate headers.
    :rtype: flask.Response
    """
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

    """
    Add an IP address or phone number to the blacklist.

    This endpoint accepts a string parameter (either an IP address or a phone number)
    via the URL path and adds it to the in-memory blacklist. It returns a confirmation
    response upon successful addition.

    Example usage:
      - https://api.intersmartgroup.com/blacklist/192.168.0.1
      - https://api.intersmartgroup.com/blacklist/380951234567

    :param req: The IP address or phone number to be blacklisted.
    :type req: str
    :return: A Flask Response object confirming the addition to the blacklist.
    :rtype: flask.Response
    """

    blacklist.append(req)
    return __gen_response(201, f'BLACKLISTED', req)


@app.route('/get-available-vehicles/', methods=['GET'])
def get_vehicles():

    """
    Return a list of available vehicles in JSON format. This is need to be listed at frontend side.

    This endpoint serializes the `VEHICLES` object using a custom JSON encoder
    and returns it as a JSON response. It also includes a CORS header to allow
    cross-origin requests.

    :return: A Flask Response object containing the serialized list of vehicles.
    :rtype: flask.Response
    """

    resp = Response(response=json.dumps(vehicles.VEHICLES, cls=vehicles.VehicleEncoder, ensure_ascii=False),
                    content_type='application/json; charset=utf-8')
    resp.headers.add('Access-Control-Allow-Origin', '*')
    return resp


@app.route('/calculate/', methods=['POST'])
def calculate():
    """
    Handle POST requests to perform a route calculation based on input data.

    This endpoint performs the following steps:
    1. Parses and validates the incoming request using a preprocessing function.
    2. Runs a route calculation algorithm and handles possible errors.
    3. Composes a Telegram message with calculation details.
    4. Logs the request and response data.
    5. Checks if the request IP is blacklisted and adjusts the message accordingly.
    6. Sends a Telegram message with the calculation summary.
    7. Returns a structured JSON response to the frontend.

    :return: A Flask response object containing a JSON payload with status and data or error details.
    :rtype: flask.Response
    """

    # Step 1: Preprocess request
    try:
        rqst = request_processor.preprocess(request)
    except (TypeError, ValueError, KeyError) as e:
        return __gen_response(400, 'ERROR', details=str(e.args))

    # Step 2: Perform the calculationn
    try:
        calculation_dto = calc_itself.calculate_route_ai(rqst)
    except ZeroDistanceResultsError as e:
        telegramapi2.send_developer(
            f'No available route can be built\n\n'
            f'Request = {json.dumps(rqst, ensure_ascii=False)}\n\n'
            f'Exception = {str(e)}', e)
        return __gen_response(404, 'ZeroDistanceResultsError', details=str(e))
    except Exception as e:
        telegramapi2.send_developer(
            f'Unspecified calc error\n\n'
            f'Request = {json.dumps(rqst, ensure_ascii=False)}\n\n'
            f'Exception = {str(e)}', e)
        return __gen_response(500, 'ERROR', details='Unspecified calculation error')

    # Step 3: Prepare TG message
    tg_msg = compositor.compose_telegram(
        intent=rqst['intent'],
        calculation=calculation_dto,
        url=rqst['url'],
        ip=rqst['ip'],
        phone_num=rqst["phone_number"])

    # Step 4: Log request and calculation
    try:
        LOGGER.put_request(phone_number='nosms',
                           query=json.dumps(rqst, ensure_ascii=False),
                           response=json.dumps([tg_msg, 'nosms'], ensure_ascii=False))
    except Exception as e:
        telegramapi2.send_developer(
            f'LOGGER.put_request error\n\nException = {str(e)}', e)

    # Step 5: Check if IP blacklisted
    if blacklist.check_ip(rqst['ip']):
        tg_msg = '*BLACKLISTED*\n\n'+tg_msg

    # Step 6: Notify managers via Telegram Bot
    telegramapi2.send_silent(tg_msg)

    # Step 7: Response to frontend
    return __gen_response(200, 'WORKLOAD', workload=calculation_dto.to_dict())


@app.route('/submit/', methods=['POST'])
def submit_new():

    """
    Handle POST requests to submit a callback request based on calculation data and phone number.

    This endpoint performs the following steps:
    1. Parses and validates the incoming request, including phone number and calculation payload.
    2. Composes both an SMS message for the client and a Telegram message for notifying internal managers.
    3. Logs the incoming request and generated messages.
    4. Checks if the request is from a blacklisted phone number or IP address:
       - If not blacklisted: sends both SMS and Telegram messages.
       - If blacklisted: only sends a modified Telegram message.
    5. Returns a success response indicating the callback has been scheduled.

    :return: A Flask response object indicating the result of the submission.
    :rtype: flask.Response
    """

    # Step 1: Preprocess request
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

    # Step 2 Prepare TG and SMS message
    sms_msg = compositor.make_sms_text(dto)
    tg_msg = compositor.compose_telegram(
        intent='callback',
        calculation=dto,
        url=url,
        ip=ip,
        phone_num=num)

    # Step 3: Log request and calculation
    LOGGER.put_request(phone_number=num,
                       query=json.dumps(dto.to_dict(), ensure_ascii=False),
                       response=json.dumps([tg_msg, sms_msg], ensure_ascii=False))

    # Step 4: Check for blacklist and make actions
    if not blacklist.check(num, ip):
        # Send TG to managers and SMS to client if not blacklisted
        telegramapi2.send_loud(tg_msg)
        smsapi.send_sms(num, sms_msg)
    else:
        # Send only modified TG to managers if blacklisted. Spreading blacklist by mapping num to ip
        blacklist.spread(num, ip)
        telegramapi2.send_loud('*BLACKLISTED*\n\n'+tg_msg)

    # Step 5: Return resopnse to frontend
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
