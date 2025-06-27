import pytest
import requests
import json


@pytest.fixture
def headers():
    return {
        "Content-Type": "application/json; charset=utf-8"
    }


@pytest.fixture
def response_payload_assert():
    return {
        "status": "WORKLOAD",
        "details": "",
        "workload": {
            "place_a_name": "Сміла",
            "place_a_name_long": "Сміла, Смілянська міськрада, Черкаська область",
            "place_b_name": "Здолбунів",
            "place_b_name_long": "Здолбунів, Здолбунівський район, Рівненська область",
            "map_link": "https://www.google.com.ua/maps/dir/49.227717,31.852233/50.5089112,26.2566443/",
            "place_chain": "Черкаси - Сміла - Здолбунів - Рівне",
            "chain_map_link": "https://www.google.com.ua/maps/dir/49.3781683,32.0557625/49.227717,31.852233/50.5089112,26.2566443/50.6454164,26.2704279/",
            "distance": 591.0,
            "transport_id": 1,
            "transport_name": "Тент 5",
            "transport_capacity": 5,
            "price": 15462.48396,
            "price_per_km": 26.18,
            "is_price_per_ton": False,
            "locale": "ru_UA"
             }
    }


@pytest.fixture
def submit_payload():
    ...


@pytest.mark.network
def test_calculate(flask_request_calculate, headers):

    url = 'http://localhost:5000/calculate/'
    data = json.dumps(flask_request_calculate, ensure_ascii=False)
    response = requests.post(url, data.encode('utf-8'), headers=headers).json()
    assert response.get('status') == 'WORKLOAD'
    workload = response.get('workload')
    assert isinstance(workload.get('place_a_name'), str)
    assert isinstance(workload.get('place_b_name'), str)
    assert float(workload.get('distance')) > 0.0
    assert float(workload.get('price').replace(' ', '')) > 0.0


@pytest.mark.network
def test_submit():
    # TODO implement
    ...


@pytest.mark.network
def test_get_available_vehicles(headers):
    url = 'http://localhost:5000/get-available-vehicles/'
    response = requests.get(url, headers=headers).json()
    assert len(response) == 7
    for item in response:
        assert len(item) == 14
        assert isinstance(item.get('id'), int)
