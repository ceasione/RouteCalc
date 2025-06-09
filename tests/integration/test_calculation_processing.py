
import pytest
from app.lib.utils.DTOs import RequestDTO, CalculationDTO
import app.lib.calc.calc_itself as calc_itself


@pytest.fixture
def request_dto(place_4, place_5, vehicle_2):
    return RequestDTO(
        intent='acquire',
        origin=place_4,
        destination=place_5,
        vehicle=vehicle_2,
        phone_num=None,
        locale='ru_UA',
        url='http://localhost:3000/',
        ip='127.0.0.1'
    )


@pytest.mark.integration
def test_request_processing(request_dto):
    calc_dto: CalculationDTO = calc_itself.process_request(request_dto)
