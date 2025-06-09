import pytest
from unittest.mock import Mock
from math import isclose
from app.lib.calc.calc_itself import Predictors


@pytest.fixture
def mock_model():
    model = Mock()
    model.predict.return_value = 47.0
    return model


# -------- Tests: _distance_ratio --------
@pytest.mark.parametrize("distance,expected_range", [
    (1000, (40.0, 50.0)),     # very short distance → high ratio
    (50000, (2.0, 3.0)),    # medium distance
    (300000, (1.0, 2.0)),   # long distance
])
def test_distance_ratio_behavior(distance, expected_range):
    result = Predictors._distance_ratio(distance)
    assert expected_range[0] <= result <= expected_range[1], f"Got {result} for {distance}m"


# -------- Tests: conventional method --------
def test_conventional_normal(depot_1, depot_2, vehicle_1):
    dist = 100_000  # 100km
    price = Predictors.conventional(depot_1, depot_2, vehicle_1, dist)
    assert isinstance(price, float)
    # Not exact match, but price should be influenced by ratios and distance
    assert price > 0


def test_conventional_minimum_distance(depot_1, depot_2, vehicle_1):
    """Should use 50km cap when distance is too short"""
    dist = 10_000  # 10km, less than cap
    result_short = Predictors.conventional(depot_1, depot_2, vehicle_1, dist)
    result_cap = Predictors.conventional(depot_1, depot_2, vehicle_1, 50_000)
    assert isclose(result_short, result_cap, rel_tol=1e-3)


# -------- Tests: ML method --------
def test_ml_prediction_uses_model(mock_model, depot_1, depot_2, vehicle_1):
    price = Predictors.ml(depot_1, depot_2, vehicle_1, _distance=123456, ml_model=mock_model)
    mock_model.predict.assert_called_once_with(depot_1.id, depot_2.id, vehicle_1.id)
    assert price == 47.0
