import pytest
from unittest.mock import Mock
from math import isclose
from app.lib.calc.calc_itself import Predictors
from app.lib.calc.loadables.depot import Depot
from app.lib.calc.loadables.vehicles import Vehicle


@pytest.fixture
def depot_a():
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
def depot_b():
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
def vehicle():
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
def mock_model():
    model = Mock()
    model.predict.return_value = 47.0
    return model


# -------- Tests: _distance_ratio --------
@pytest.mark.parametrize("distance, expected_range", [
    (1000, (40.0, 50.0)),     # very short distance → high ratio
    (50000, (2.0, 3.0)),    # medium distance
    (300000, (1.0, 2.0)),   # long distance
])
def test_distance_ratio_behavior(distance, expected_range):
    result = Predictors._distance_ratio(distance)
    assert expected_range[0] <= result <= expected_range[1], f"Got {result} for {distance}m"


# -------- Tests: conventional method --------
def test_conventional_normal(depot_a, depot_b, vehicle):
    dist = 100_000  # 100km
    price = Predictors.conventional(depot_a, depot_b, vehicle, dist)
    assert isinstance(price, float)
    # Not exact match, but price should be influenced by ratios and distance
    assert price > 0


def test_conventional_minimum_distance(depot_a, depot_b, vehicle):
    """Should use 50km cap when distance is too short"""
    dist = 10_000  # 10km, less than cap
    result_short = Predictors.conventional(depot_a, depot_b, vehicle, dist)
    result_cap = Predictors.conventional(depot_a, depot_b, vehicle, 50_000)
    assert isclose(result_short, result_cap, rel_tol=1e-3)


# -------- Tests: ML method --------
def test_ml_prediction_uses_model(mock_model, depot_a, depot_b, vehicle):
    price = Predictors.ml(depot_a, depot_b, vehicle, _distance=123456, ml_model=mock_model)
    mock_model.predict.assert_called_once_with(depot_a.id, depot_b.id, vehicle.id)
    assert price == 47.0
