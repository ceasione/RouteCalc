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
    print(r.text)

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
    print(r.text)


do_submit_calculation_test()
# calculate_test()