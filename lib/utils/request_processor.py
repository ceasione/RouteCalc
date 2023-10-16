
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

def __validate_request(input_json, user_ip):

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
            'locale': obj['locale'] if obj.get('locale') is not None else 'uk_UA',
            'url': obj['url'] if obj.get('url') is not None else 'url undefined',
            'ip': user_ip}

def preprocess(request):

    if isinstance(request.json, str):
        s_request = request.json
    elif isinstance(request.json, dict):
        s_request = json.dumps(request.json, ensure_ascii=False)
        ip = request.remote_addr
    else:
        raise TypeError('Expected input json be str or dict')

    return __validate_request(s_request, request.remote_addr)
