
import json
import lib.utils.number_tools as number_tools
import lib.calc.vehicles as vehicles

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
                   'locale': str('ru_UA'),
                   'url': str('https://inters...')}

def __validate_transport_id(vehicle_id):

    for vehicle in vehicles.VEHICLES:

        if vehicle.id == vehicle_id:

            return vehicle_id

    raise ValueError('Unknown vehicle_id')


def __validate_request(input_dict, user_ip):

    num_validator = number_tools.get_instance()

    if input_dict['intent'] != 'calc' and input_dict['intent'] != 'callback' and input_dict['intent'] != 'acquire':
        raise ValueError('Expected intent "calc", "callback" or "acquire". Got ' + input_dict['intent'])

    if len(input_dict['from']['name_short']) < 1 or len(input_dict['to']['name_short']) < 1:
        raise ValueError('Field name_short could not be empty')

    if len(input_dict['from']['name_long']) < 1 or len(input_dict['to']['name_long']) < 1:
        raise ValueError('Field name_long could not be empty')

    return {'intent':   str(input_dict['intent']),
            'from':     {'name_short': str(input_dict['from']['name_short']),
                         'name_long': str(input_dict['from']['name_long']),
                         'lat': float(input_dict['from']['lat']),
                         'lng': float(input_dict['from']['lng']),
                         'countrycode': str(input_dict['from']['countrycode'])},
            'to':       {'name_short': str(input_dict['to']['name_short']),
                         'name_long': str(input_dict['to']['name_long']),
                         'lat': float(input_dict['to']['lat']),
                         'lng': float(input_dict['to']['lng']),
                         'countrycode': str(input_dict['to']['countrycode'])},
            'transport_id': __validate_transport_id(int(input_dict['transport_id'])),
            'phone_number': num_validator.validate_phone_ukr(input_dict['phone_number']),
            'locale': input_dict['locale'] if input_dict.get('locale') is not None else 'uk_UA',
            'url': input_dict['url'] if input_dict.get('url') is not None else 'url undefined',
            'ip': user_ip}


def __validate_numless_request(input_dict, user_ip):

    if input_dict['intent'] != 'acquire':
        raise ValueError('Expected intent "acquire". Got ' + input_dict['intent'])

    if len(input_dict['from']['name_short']) < 1 or len(input_dict['to']['name_short']) < 1:
        raise ValueError('Field name_short could not be empty')

    if len(input_dict['from']['name_long']) < 1 or len(input_dict['to']['name_long']) < 1:
        raise ValueError('Field name_long could not be empty')

    return {'intent':   str(input_dict['intent']),
            'from':     {'name_short': str(input_dict['from']['name_short']),
                         'name_long': str(input_dict['from']['name_long']),
                         'lat': float(input_dict['from']['lat']),
                         'lng': float(input_dict['from']['lng']),
                         'countrycode': str(input_dict['from']['countrycode'])},
            'to':       {'name_short': str(input_dict['to']['name_short']),
                         'name_long': str(input_dict['to']['name_long']),
                         'lat': float(input_dict['to']['lat']),
                         'lng': float(input_dict['to']['lng']),
                         'countrycode': str(input_dict['to']['countrycode'])},
            'transport_id': __validate_transport_id(int(input_dict['transport_id'])),
            'phone_number': None,
            'locale': input_dict['locale'] if input_dict.get('locale') is not None else 'uk_UA',
            'url': input_dict['url'] if input_dict.get('url') is not None else 'url undefined',
            'ip': user_ip}


def preprocess(request):

    if isinstance(request.json, str):
        input_dict = json.loads(request.json)
    elif isinstance(request.json, dict):
        input_dict = request.json
    else:
        raise TypeError('Expected input json be str or dict')

    if input_dict['intent'] == 'acquire':
        return __validate_numless_request(input_dict, request.remote_addr)
    else:
        return __validate_request(input_dict, request.remote_addr)
