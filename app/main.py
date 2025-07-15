
from app.lib.utils.logger import logger
from app.lib.utils import storage
storage.ensure_all()  # noqa: E402
from flask import Flask
from flask import request
import json
from flask import Response
from app.lib.utils import compositor
from app.lib.calc.loadables import vehicles
from app.lib.apis import smsapi, telegramapi2
from app.lib.apis.telegramapi3 import Telegramv3Interface, tg_interface_manager
from app.lib.utils.QueryLogger import QUERY_LOGGER
from flask_cors import CORS
from app.lib.utils.blacklist import BLACKLIST
import app.lib.utils.request_processor as request_processor
import app.lib.calc.calc_itself as calc_itself
from app.lib.utils.DTOs import CalculationDTO
from app.lib.utils import number_tools
from app.lib.utils.number_tools import WrongNumberError
from app.lib.calc.calc_itself import ZeroDistanceResultsError
import dataclasses
import app.settings as settings


logger.info(f'Running on dev machine: {settings.DEV_MACHINE}')
app = Flask(__name__)
CORS = CORS(app)


def __gen_response(http_status: int, json_status: str, details: str = '', workload: dict = None) -> Response:

    """
    Additional layer for generating a standardized JSON HTTP response.

    It returns a Flask `Response` object containing a JSON payload with the specified
    status, optional details message, and an optional workload (typically a `CalculationDTO` object).
    It also adds a CORS header to allow cross-origin requests.

    :param http_status: HTTP status code to return (e.g., 200, 400, 500).
    :type http_status: int
    :param json_status: Application-level status string indicating result of the operation.
    :type json_status: str
    :param details: Optional string providing additional information about the response.
    :type details: str
    :param workload: Optional data payload to include in the response (e.g., calculation results).
    :type workload: dict or None
    :return: A Flask Response object with JSON content and appropriate headers.
    :rtype: flask.Response
    """

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

    BLACKLIST.blacklist(req)
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

    resp = Response(response=json.dumps(vehicles.VEHICLES.as_list, cls=vehicles.VehicleEncoder, ensure_ascii=False),
                    content_type='application/json; charset=utf-8')
    resp.headers.add('Access-Control-Allow-Origin', '*')
    return resp


@app.route('/calculate/', methods=['POST'])
def calculate():
    """
    Handle POST requests to perform a route calculation based on input data.

    This endpoint performs the following steps:
    1. Parses and validates the incoming request using a preprocessing function.
    2. Processes request and making CalculationDTO containing result
    3. Composes a Telegram message with calculation details.
    4. Logs the request and response data.
    5. Checks if the request IP is blacklisted and adjusts the message accordingly.
    6. Sends a Telegram message with the calculation summary.
    7. Returns a structured JSON response to the frontend.

    :return: A Flask response object containing a JSON payload with status and data or error details.
    :rtype: flask.Response
    """

    # Step 1: Preprocess request
    request_dto = request_processor.process(request)
    logger.debug('Acquired request has been processed. Got Request DTO')

    # Step 2: Perform the calculationn
    calculation_dto = calc_itself.process_request(request_dto)
    logger.debug('Calculation was succesfully performed. Got Calculation DTO')

    # Step 3: Prepare TG message
    tg_msg = compositor.compose_telegram_message_text(
        intent=request_dto.intent,
        calculation=calculation_dto,
        url=request_dto.url,
        ip=request_dto.ip,
        phone_num=request_dto.phone_num)

    # Step 4: Log request and calculation
    with QUERY_LOGGER as qlogger:
        qlogger.log_calculation(phone_number=request_dto.phone_num,
                                query=json.dumps(request_dto.to_dict(), ensure_ascii=False),
                                response=json.dumps([tg_msg, 'nosms'], ensure_ascii=False))
    logger.debug('Query Logger has succesfully logged calculation')

    # Step 5: Check if IP blacklisted
    if BLACKLIST.check(request_dto.ip):
        tg_msg = '*BLACKLISTED*\n\n'+tg_msg

    # Step 6: Notify managers via Telegram Bot
    telegramapi2.send_silent(tg_msg)
    logger.debug('Telegram message has been sent to silent chat')

    # Step 7: Response to frontend
    return __gen_response(200, 'WORKLOAD', workload=dataclasses.asdict(calculation_dto))


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
    dto = CalculationDTO.from_dict(request.json['dto'])
    num = number_tools.validate_phone_ukr(request.json['num'])
    ip = request.remote_addr

    # Step 2 Prepare TG and SMS message
    sms_msg = compositor.make_sms_text(dto)
    tg_msg = compositor.compose_telegram_message_text(
        intent='callback',
        calculation=dto,
        url=request.json['url'],
        ip=ip,
        phone_num=num)

    # Step 3: Log request and calculation
    with QUERY_LOGGER as qlogger:
        qlogger.log_calculation(phone_number=num,
                                query=json.dumps(dataclasses.asdict(dto), ensure_ascii=False),
                                response=json.dumps([tg_msg, sms_msg], ensure_ascii=False))

    # Step 4: Check for blacklist and make notifications
    if not BLACKLIST.check(num, ip):
        # Not blacklisted -> Send TG message to managers and SMS to client
        telegramapi2.send_loud(tg_msg)
        smsapi.send_sms(num, sms_msg)
    else:
        # Blacklisted -> Send modified TG message to managers only -> Spreading blacklist by mapping num and ip
        BLACKLIST.spread(num, ip)
        telegramapi2.send_loud('*BLACKLISTED*\n\n'+tg_msg)

    # Step 5: Return resopnse to frontend
    return __gen_response(200, 'CALLBACK_SCHEDULED')


@app.route(settings.TELEGRAMV3_WEBHOOK_ADDRESS, methods=['POST'])
def catch_tg_webhook():
    iface = tg_interface_manager.get_interface()
    own_secret = iface.get_own_secret()
    got_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if got_secret != own_secret:
        return "Forbidden", 403
    iface.process_webhook(request.get_json())
    return 'OK', 200


@app.errorhandler(ZeroDistanceResultsError)
def handle_zero_distance_error(e: Exception) -> Response:
    telegramapi2.send_developer(
        f'No available route can be built\n\n'
        f'Exception = {str(e)}', e)
    return __gen_response(404, 'ZeroDistanceResultsError', details=str(e))


@app.errorhandler(WrongNumberError)
def handle_wrong_number(e: Exception) -> Response:
    return __gen_response(422, 'WrongNumberError', details=str(e.args))


@app.errorhandler(request_processor.ValidationError)
def handle_validation_error(_e: Exception) -> Response:
    return __gen_response(400, 'ERROR', details='Input validation error')


@app.errorhandler(TypeError)
def handle_preprocessing_errs(_e: Exception) -> Response:
    return __gen_response(400, 'ERROR', details='Invalid input')


@app.errorhandler(LookupError)
def handle_preprocessing_errs2(_e: Exception) -> Response:
    return __gen_response(400, 'ERROR', details='Invalid input')


@app.errorhandler(RuntimeError)
def handle_runtime_error(e: Exception) -> Response:
    telegramapi2.send_developer(f'Errorhandler error caught', e)
    return __gen_response(500, 'ERROR', details='Internal server error')


@app.errorhandler(Exception)
def handle_broad(e: Exception) -> Response:
    telegramapi2.send_developer(
        f'Broad calc error\n\n'
        f'Exception = {str(e)}', e)
    return __gen_response(500, 'ERROR', details='Internal server error')


@app.errorhandler(404)
def page_not_found(_e: Exception):
    return 'Not found', 404


def create_app():
    hook_url = settings.TELEGRAMV3_BASE_APIURL + settings.TELEGRAMV3_WEBHOOK_ADDRESS
    tg_interface_manager.set_interface(
        Telegramv3Interface(
            botfatherkey=settings.TELEGRAMV3_BOT_APIKEY,
            webhook_url=hook_url,
            chat_subscription=int(settings.TELEGRAMV3_SILENT_CHAT_ID),
            silent_chat=int(settings.TELEGRAMV3_SILENT_CHAT_ID),
            loud_chat=int(settings.TELEGRAMV3_LOUD_CHAT_ID),
            dev_chat=int(settings.TELEGRAMV3_DEVELOPER_CHAT_ID)
        )
    )
    return app


if __name__ == '__main__':
    # Set up ngrok
    from pyngrok import ngrok
    tunnel = ngrok.connect('http://localhost:5000')
    tunnel_hook_url = tunnel.public_url + settings.TELEGRAMV3_WEBHOOK_ADDRESS

    # Set up tg webhook
    tg_interface_manager.set_interface(
        Telegramv3Interface(
            botfatherkey=settings.TELEGRAMV3_BOT_APIKEY,
            webhook_url=tunnel_hook_url,
            chat_subscription=int(settings.TELEGRAMV3_DEVELOPER_CHAT_ID),
            silent_chat=int(settings.TELEGRAMV3_DEVELOPER_CHAT_ID),
            loud_chat=int(settings.TELEGRAMV3_DEVELOPER_CHAT_ID),
            dev_chat=int(settings.TELEGRAMV3_DEVELOPER_CHAT_ID)
        )
    )

    # Run Flask
    app.run(debug=True, use_reloader=False)
