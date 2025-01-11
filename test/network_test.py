import requests
import json


def do_submit_calculation_test():
    payload = {'intent': 'callback',
               'from': {'name_short': 'Сміла',
                        'name_long': 'Сміла, Смілянська міськрада, Черкаська область',
                        'lat': 49.227717,
                        'lng': 31.852233,
                        'countrycode': 'UA'},
               'to': {'name_short': 'Здолбунів',
                      'name_long': 'Здолбунів, Здолбунівський район, Рівненська область',
                      'lat': 50.5089112,
                      'lng': 26.2566443,
                      'countrycode': 'UA'},
               'transport_id': 1,
               'phone_number': '380953459607',
               'locale': 'ru_UA',
               'url': 'http://localhost:3000/'}

    url = 'http://localhost:5000/do-submit-calculation/'
    data = json.dumps(payload, ensure_ascii=False)
    headers = {
        "Content-Type": "application/json; charset=utf-8"
    }
    r = requests.post(url, data.encode('utf-8'), headers=headers)
    return r.text


def calculate_test():
    payload = {'intent': 'acquire',
               'from': {'name_short': 'Сміла',
                        'name_long': 'Сміла, Смілянська міськрада, Черкаська область',
                        'lat': 49.227717,
                        'lng': 31.852233,
                        'countrycode': 'UA'},
               'to': {'name_short': 'Здолбунів',
                      'name_long': 'Здолбунів, Здолбунівський район, Рівненська область',
                      'lat': 50.5089112,
                      'lng': 26.2566443,
                      'countrycode': 'UA'},
               'transport_id': 1,
               'phone_number': '',
               'locale': 'ru_UA',
               'url': 'http://localhost:3000/'}

    url = 'http://localhost:5000/calculate/'
    data = json.dumps(payload, ensure_ascii=False)
    headers = {
        "Content-Type": "application/json; charset=utf-8"
    }
    r = requests.post(url, data.encode('utf-8'), headers=headers)
    return r.text


do_submit_assert = '''{"status": "CALLBACK_SCHEDULED", "details": "", "workload": null}'''
if do_submit_calculation_test() == do_submit_assert:
    print('do_submit_calculation_test() is OK')
else:
    print('do_submit_calculation_test() FAILED')


calculate_assert = '''{"status": "WORKLOAD", "details": "", "workload": {"place_a_name": "Сміла", "place_a_name_long": "Сміла, Смілянська міськрада, Черкаська область", "place_b_name": "Здолбунів", "place_b_name_long": "Здолбунів, Здолбунівський район, Рівненська область", "map_link": "https://www.google.com.ua/maps/dir/49.227717,31.852233/50.5089112,26.2566443/", "place_chain": "Черкаси - Сміла - Здолбунів - Рівне", "chain_map_link": "https://www.google.com.ua/maps/dir/49.3781683,32.0557625/49.227717,31.852233/50.5089112,26.2566443/50.6454164,26.2704279/", "distance": 591.0, "transport_id": 1, "transport_name": "Тент 5", "transport_capacity": 5, "price": 15462.48396, "price_per_km": 26.18, "is_price_per_ton": false, "locale": "ru_UA"}}'''
if calculate_test() == calculate_assert:
    print('calculate_test() is OK')
else:
    print('calculate_test() FAILED')
