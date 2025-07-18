import pytest
from unittest.mock import MagicMock, patch
from app.lib.utils.QueryLogger import QueryLogger
from app.lib.utils.DTOs import RequestDTO, CalculationDTO


@pytest.fixture
def request_dto(place_4, vehicle_2):
    return RequestDTO(
        intent="calculate",
        origin=place_4,
        destination=place_4,
        vehicle=vehicle_2,
        phone_num="380501234567",
        locale="uk-UA",
        url="https://example.com",
        ip="127.0.0.1"
    )


@pytest.fixture
def calculation_dto():
    return CalculationDTO(
        place_a_name="Kyiv",
        place_a_name_long="Kyiv, Ukraine",
        place_b_name="Lviv",
        place_b_name_long="Lviv, Ukraine",
        map_link="http://map",
        place_chain="Kyiv - Lviv",
        chain_map_link="http://chainmap",
        distance="543",
        distance_unstr=543.0,
        transport_id=1,
        transport_name="Truck",
        transport_capacity=20,
        price="5000",
        price_unstr=5000.0,
        price_per_ton="250",
        price_per_ton_unstr=250.0,
        price_per_km="9.2",
        price_per_km_unstr=9.2,
        is_price_per_ton=True,
        currency="UAH",
        currency_rate=1.0,
        pfactor_vehicle="base",
        pfactor_departure="none",
        pfactor_arrival="none",
        pfactor_distance="road",
        locale="uk_UA",
        real_price=54.52,
        starting_depot_id=12,
        ending_depot_id=76,
    )


@patch("app.lib.utils.QueryLogger.sqlite3.connect")
@patch("app.lib.utils.QueryLogger.QueryLogger._generate_random_digest", return_value="mocked_digest")
def test_log_calculation(mock_digest, mock_connect, request_dto, calculation_dto):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    logger = QueryLogger()
    with logger:
        digest = logger.log_calculation(request_dto, calculation_dto)

    mock_cursor.execute.assert_called_once()
    assert mock_conn.commit.call_count == 4
    assert digest == "mocked_digest"


@patch("app.lib.utils.QueryLogger.VEHICLES.get_by_id")
@patch("app.lib.utils.QueryLogger.sqlite3.connect")
def test_get_request_dto(mock_connect, mock_get_by_id, request_dto, vehicle_1):
    mock_row = {
        "request_intent": request_dto.intent,
        "request_orig_lat": request_dto.origin.lat,
        "request_orig_lng": request_dto.origin.lng,
        "request_orig_name": request_dto.origin.name,
        "request_orig_name_long": request_dto.origin.name_long,
        "request_orig_countrycode": request_dto.origin.countrycode,
        "request_dest_lat": request_dto.destination.lat,
        "request_dest_lng": request_dto.destination.lng,
        "request_dest_name": request_dto.destination.name,
        "request_dest_name_long": request_dto.destination.name_long,
        "request_dest_countrycode": request_dto.destination.countrycode,
        "request_vehicle": request_dto.vehicle.id,
        "request_phone_num": request_dto.phone_num,
        "request_locale": request_dto.locale,
        "request_url": request_dto.url,
        "request_ip": request_dto.ip
    }

    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = mock_row
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn
    mock_get_by_id.return_value = vehicle_1

    logger = QueryLogger()
    with logger:
        dto = logger.get_request_dto("mocked_digest")

    assert dto.intent == request_dto.intent
    assert dto.phone_num == request_dto.phone_num
    assert dto.vehicle.id == vehicle_1.id
    mock_cursor.execute.assert_called_once()


@patch("app.lib.utils.QueryLogger.compositor.format_cost", side_effect=lambda x: f"formatted-{x}")
@patch("app.lib.utils.QueryLogger.sqlite3.connect")
def test_get_calculation_dto(mock_connect, mock_format_cost, calculation_dto):
    mock_row = {
        "calculation_place_a_name": calculation_dto.place_a_name,
        "calculation_place_a_name_long": calculation_dto.place_a_name_long,
        "calculation_place_b_name": calculation_dto.place_b_name,
        "calculation_place_b_name_long": calculation_dto.place_b_name_long,
        "calculation_map_link": calculation_dto.map_link,
        "calculation_place_chain": calculation_dto.place_chain,
        "calculation_chain_map_link": calculation_dto.chain_map_link,
        "calculation_distance": calculation_dto.distance_unstr,
        "calculation_transport_id": calculation_dto.transport_id,
        "calculation_transport_name": calculation_dto.transport_name,
        "calculation_transport_capacity": calculation_dto.transport_capacity,
        "calculation_price": calculation_dto.price_unstr,
        "calculation_price_per_ton": calculation_dto.price_per_ton_unstr,
        "calculation_price_per_km": calculation_dto.price_per_km_unstr,
        "calculation_is_price_per_ton": int(calculation_dto.is_price_per_ton),
        "calculation_currency": calculation_dto.currency,
        "calculation_currency_rate": calculation_dto.currency_rate,
        "calculation_pfactor_vehicle": calculation_dto.pfactor_vehicle,
        "calculation_pfactor_departure": calculation_dto.pfactor_departure,
        "calculation_pfactor_arrival": calculation_dto.pfactor_arrival,
        "calculation_pfactor_distance": calculation_dto.pfactor_distance,
        "calculation_locale": calculation_dto.locale,
        "calculation_real_price": calculation_dto.real_price,
        "calculation_starting_depot_id": calculation_dto.starting_depot_id,
        "calculation_ending_depot_id": calculation_dto.ending_depot_id
    }

    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = mock_row
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn

    logger = QueryLogger()
    with logger:
        dto = logger.get_calculation_dto("mocked_digest")

    assert dto.price == f"formatted-{calculation_dto.price_unstr}"
    assert dto.distance_unstr == calculation_dto.distance_unstr
    assert dto.transport_name == calculation_dto.transport_name
    mock_cursor.execute.assert_called_once()
