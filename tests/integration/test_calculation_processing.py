
import pytest
from app.lib.utils.DTOs import RequestDTO, CalculationDTO
import app.lib.calc.calc_itself as calc_itself


@pytest.mark.integration
def test_request_processing(fixture_request_dto):
    calc_dto: CalculationDTO = calc_itself.process_request(fixture_request_dto)
