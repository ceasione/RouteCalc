
import pytest
import unittest
from unittest.mock import Mock
from app.lib.calc.place import Place
from app.lib.calc.loadables.depot import Depot
from app.lib.calc.loadables.vehicles import Vehicle
from app.lib.utils.DTOs import RequestDTO
from app.lib.calc.calc_itself import plan_route, calculate, process_request


@pytest.fixture
def place_a():
    return Place(lat=50.0, lng=30.0, name="Kyiv", countrycode="UA")


@pytest.fixture
def place_b():
    return Place(lat=49.0, lng=32.0, name="Cherkasy", countrycode="UA")


@pytest.fixture
def depot():
    dct = {
        "lat": 51.2126936,
        "lng": 24.7234919,
        "name": "Ковель",
        "state_iso": "UA",
        "depot_id": 3,
        "departure_ratio": 0.95,
        "arrival_ratio": 0.85
    }
    return Depot(**dct)


@pytest.fixture
def vehicle():
    dct = {
        "id": 6,
        "name": "Тент 10",
        "name_ua": "Тент 10",
        "price": 37.5,
        "order": 2,
        "length": 8.5,
        "width": 2.45,
        "height": 2.7,
        "weight_capacity": 10,
        "space_capacity": 60,
        "cargoes_possible": "Любые грузы на паллетах, в бегах и мешках",
        "cargoes_possible_ua": "Будь-які вантажі на палетах, беги і мішки",
        "picture": "https://api.intersmartgroup.com/static/icons/tent10.svg",
        "price_per_ton": False
    }
    return Vehicle(**dct)


@pytest.fixture
def depot_park(depot):
    mock_park = Mock()
    mock_park.filter_by.side_effect = lambda cc: [depot] if cc == "UA" or cc is None else []
    return mock_park


def test_plan_route_success(place_a, place_b, depot_park):
    mock_dist = Mock()
    mock_dist.place_from = depot_park.filter_by("UA")[0]
    mock_dist.place_to = depot_park.filter_by("UA")[0]

    matrix_mock = Mock(return_value=[mock_dist])

    with unittest.mock.patch("app.lib.calc.calc_itself.DistanceResolvers.matrix", matrix_mock):
        result = plan_route(place_a, place_b, dptpark=depot_park)

    assert len(result) == 4
    assert result[0] == depot_park.filter_by("UA")[0]


def test_calculate_basic(place_a, place_b, depot, vehicle):
    mock_distance = Mock()
    mock_distance.distance = 100000  # 100 km

    route = (depot, place_a, place_b, depot)

    def mock_dist_resolver(f, t):
        return [mock_distance]

    def mock_predictor(dep_a, dep_b, veh, dist):
        return 20.0  # 20 UAH/km

    distance, price, cost = calculate(route, vehicle, mock_dist_resolver, mock_predictor)

    assert distance == 300_000  # 3 segments * 100km
    assert price == 20.0
    assert cost == 6000.0


def test_process_request_basic(monkeypatch, place_a, place_b, depot, vehicle):
    request = RequestDTO(origin=place_a, destination=place_b, vehicle=vehicle, locale="uk_UA")

    # Monkeypatch plan_route
    monkeypatch.setattr("app.lib.calc.calc_itself.plan_route", lambda a, b: (depot, a, b, depot))

    # Patch dist resolver
    mock_dist = Mock()
    mock_dist.distance = 100000

    monkeypatch.setattr("app.lib.calc.calc_itself.DistanceResolvers.matrix", lambda f, t: [mock_dist])
    monkeypatch.setattr("app.lib.calc.calc_itself.Predictors.ml", lambda d1, d2, v, d: 20.0)

    currency_mock = Mock()
    currency_mock.rate.return_value = 1.0
    currency_mock.iso_code = "UAH"

    monkeypatch.setattr("app.lib.calc.calc_itself.Currency.get_preferred", lambda a, b: currency_mock)

    monkeypatch.setattr("app.lib.calc.calc_itself.compositor.generate_map_url", lambda *args: "https://map")
    monkeypatch.setattr("app.lib.calc.calc_itself.compositor.generate_place_chain", lambda *args: "Kyiv–Cherkasy")
    monkeypatch.setattr("app.lib.calc.calc_itself.compositor.format_cost", lambda cost: f"{cost:.2f}")
    monkeypatch.setattr("app.lib.calc.calc_itself.compositor.round_cost", lambda cost: round(cost, 2))

    result = process_request(request)

    assert isinstance(result.price, str)
    assert float(result.price_per_km) > 0
