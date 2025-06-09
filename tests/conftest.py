
import pytest
from app.lib.calc.place import Place
from app.lib.calc.loadables.depot import Depot
from app.lib.calc.loadables.vehicles import Vehicle


@pytest.fixture
def place_1():
    return Place(52.4604285, 13.2736697, name="Berlin")


@pytest.fixture
def place_2():
    return Place(51.5132744, 7.4652797, name="Dortmund")


@pytest.fixture
def place_3():
    return Place(48.1362927, 11.5821307, name="Munchen")


@pytest.fixture
def depot_1():
    dct = {
        "lat": 49.2477324,
        "lng": 28.5117743,
        "name": "Вінниця",
        "state_iso": "UA",
        "depot_id": 0,
        "departure_ratio": 1.0,
        "arrival_ratio": 1.0
    }
    return Depot(**dct)


@pytest.fixture
def depot_2():
    dct = {
        "lat": 46.4824242,
        "lng": 30.7610396,
        "name": "Одеса",
        "state_iso": "UA",
        "depot_id": 24,
        "departure_ratio": 0.7,
        "arrival_ratio": 1.2
    }
    return Depot(**dct)


@pytest.fixture
def vehicle_1():
    dct = {
        "id": 0,
        "name": "Тент 20",
        "name_ua": "Тент 20",
        "price": 45.0,
        "order": 1,
        "length": 13.6,
        "width": 2.45,
        "height": 2.7,
        "weight_capacity": 22,
        "space_capacity": 90,
        "cargoes_possible": "Любые грузы на паллетах, в бегах и мешках",
        "cargoes_possible_ua": "Будь-які вантажі на палетах, беги і мішки",
        "picture": "https://api.intersmartgroup.com/static/icons/tent20-v2.svg",
        "price_per_ton": False
    }
    return Vehicle(**dct)


@pytest.fixture
def place_4():
    return Place(49.227717, 31.852233, name='Сміла')


@pytest.fixture
def place_5():
    return Place(50.5089112, 26.2566443, name='Здолбунів')


@pytest.fixture
def vehicle_2():
    dct = {
        'id': 1,
        'name': 'Тент 5',
        'name_ua': 'Тент 5',
        'price': 32.0,
        'order': 3,
        'length': 7.0,
        'width': 2.45,
        'height': 2.5,
        'weight_capacity': 5,
        'space_capacity': 45,
        'cargoes_possible': 'Любые грузы на паллетах, в бегах и мешках',
        'cargoes_possible_ua': 'Будь-які вантажі на палетах, беги і мішки',
        'picture': 'https://api.intersmartgroup.com/static/icons/gaz.svg',
        'price_per_ton': False
    }
    return Vehicle(**dct)

