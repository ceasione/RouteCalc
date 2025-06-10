
import pytest
from app.lib.utils.DTOs import RequestDTO, CalculationDTO
import app.lib.calc.calc_itself as calc_itself


@pytest.mark.integration
def test_request_processing(dto_request_calculate):
    calc_dto: CalculationDTO = calc_itself.process_request(dto_request_calculate)
