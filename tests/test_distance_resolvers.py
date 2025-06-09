import pytest
from app.lib.calc.calc_itself import DistanceResolvers, ZeroDistanceResultsError
from app.lib.calc.distance import Distance


@pytest.fixture
def dummy_cache(mocker):
    return mocker.Mock()


@pytest.fixture
def dummy_api(mocker):
    return mocker.Mock()


def test_matrix_basic_resolution(place_1, place_2, dummy_cache, dummy_api):
    dummy_cache.cache_look.return_value = 490000
    dummy_api.resolve_distances.return_value = ([], [])  # Nothing left for API

    result = DistanceResolvers.matrix([place_1], [place_2], cache_=dummy_cache, gapi_=dummy_api)

    assert len(result) == 1
    assert isinstance(result[0], Distance)
    assert result[0].resolved
    assert result[0].distance == 490000


def test_matrix_resolves_with_api_fallback(place_1, place_2, dummy_cache, dummy_api):
    dummy_cache.cache_look.return_value = None

    dist = Distance(place_1, place_2, 490000)
    dummy_api.resolve_distances.return_value = ([dist], [])

    result = DistanceResolvers.matrix([place_1], [place_2], cache_=dummy_cache, gapi_=dummy_api)

    assert len(result) == 1
    assert result[0].resolved
    assert result[0].distance == 490000


def test_matrix_raises_when_unresolved(place_1, place_2, dummy_cache, dummy_api):
    dummy_cache.cache_look.return_value = None
    dummy_api.resolve_distances.return_value = ([], [Distance(place_1, place_2)])

    with pytest.raises(ZeroDistanceResultsError):
        DistanceResolvers.matrix([place_1], [place_2], cache_=dummy_cache, gapi_=dummy_api)


# --- Edge Case Tests ---


def test_matrix_empty_inputs(dummy_cache, dummy_api):
    dummy_api.resolve_distances.return_value = ([], [])
    with pytest.raises(ZeroDistanceResultsError):
        result = DistanceResolvers.matrix([], [], cache_=dummy_cache, gapi_=dummy_api)


def test_matrix_identical_place_is_skipped(place_1, dummy_cache, dummy_api):
    # Even though it's "A" to "A", it should be ignored in _produce_distances_from_places
    result = DistanceResolvers._produce_distances_from_places([place_1], [place_1])
    assert result == []


def test_matrix_duplicate_inputs_are_handled(place_1, place_2, dummy_cache, dummy_api):
    dummy_cache.cache_look.return_value = 500
    dummy_api.resolve_distances.return_value = ([], [])
    result = DistanceResolvers.matrix([place_1, place_1], [place_2, place_2], cache_=dummy_cache, gapi_=dummy_api)

    # It will produce 4 pairs since place_a != place_b even if repeated
    assert len(result) == 4
    for d in result:
        assert d.distance == 500
