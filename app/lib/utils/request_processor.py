
from typing import Tuple
import flask
from app.lib.utils import number_tools
from app.lib.calc.loadables.vehicles import VEHICLES
from app.lib.utils.DTOs import RequestDTO
from app.lib.calc.place import Place
from app.lib.utils.logger import logger


class ValidationError(Exception):
    ...


ALLOWED_INTENTS = {'calc', 'callback', 'acquire'}


def pre(request_: flask.Request) -> Tuple[dict, str]:
    raw = request_.get_json(force=True)
    return raw, request_.remote_addr


def intent(raw: dict, dto: RequestDTO):
    _intent = raw['intent'].strip()
    if _intent not in ALLOWED_INTENTS:
        raise ValidationError('Unexpected intent, got: '+raw['intent'])

    dto.intent = _intent


def origin(raw: dict, dto: RequestDTO):
    _origin = raw['from']
    _name_short = _origin['name_short']
    _name_long = _origin['name_long']

    if not _name_short:
        raise ValidationError('Place from name_short could not be empty')
    if not _name_long:
        raise ValidationError('Place from name_long could not be empty')

    dto.origin = Place(float(_origin['lat']),
                       float(_origin['lng']),
                       _origin['name_short'],
                       _origin['name_long'],
                       _origin['countrycode'])


def destination(raw: dict, dto: RequestDTO):
    _destination = raw['to']
    _name_short = _destination['name_short']
    _name_long = _destination['name_long']

    if not _name_short:
        raise ValidationError('Place to name_short could not be empty')
    if not _name_long:
        raise ValidationError('Place to name_long could not be empty')

    dto.destination = Place(float(_destination['lat']),
                            float(_destination['lng']),
                            _destination['name_short'],
                            _destination['name_long'],
                            _destination['countrycode'])


def transport(raw: dict, dto: RequestDTO):
    transport_id = int(raw['transport_id'])
    try:
        dto.vehicle = VEHICLES.get_by_id(transport_id)
    except ValueError:
        raise ValidationError(f'Unknown vehicle ID: {transport_id}')


def phone_number(raw: dict, dto: RequestDTO):
    _phone_number = raw['phone_number']

    if _phone_number is not None:
        dto.phone_num = number_tools.validate_phone_ukr(_phone_number)


def locale(raw: dict, dto: RequestDTO):
    dto.locale = raw['locale'].strip()


def url(raw: dict, dto: RequestDTO):
    _url = raw['url']
    dto.url = _url


def process(request_raw: flask.Request) -> RequestDTO:
    """
    Process and validate a flask.Request (typically received from the frontend) to create
    and populate a RequestDTO object that's convenient for further use

      input_example = {'intent': str,
                       'from': {'name_short': str,
                                'name_long': str,
                                'lat': float,
                                'lng': float,
                                'countrycode': str},
                       'to':   {'name_short': str,
                                'name_long': str,
                                'lat': float,
                                'lng': float,
                                'countrycode': str},
                       'transport_id': int,
                       'phone_number': str,
                       'locale': str,
                       'url': str}

    :param: request_raw: flask.Request object
    :return: RequestDTO object
    :raises: ValidationError
    """
    raw, ip = pre(request_raw)

    dto = RequestDTO()
    pipeline = (
        intent,
        origin,
        destination,
        transport,
        phone_number,
        locale,
        url
    )

    for stage in pipeline:
        try:
            stage(raw, dto)
        except (TypeError, IndexError, KeyError, AttributeError, ValueError) as e:
            logger.error(f'Failed to validate stage: {stage.__name__}')
            logger.exception(e)
            raise ValidationError(e)

    dto.ip = ip
    return dto
