import pytest
from app.lib.utils.QueryLogger import QueryLogger
import app.lib.calc.calc_itself as calc_itself


@pytest.fixture(name='fixture_calculation_dto')
def calculation_dto(fixture_request_dto):
    return calc_itself.process_request(fixture_request_dto)


@pytest.mark.integration
def test_db_read_write(fixture_request_dto, fixture_calculation_dto):
    qlogger = QueryLogger(':memory:')  # New in memory database instance
    with qlogger as ql:
        digest = ql.log_calcultaion(request_dto=fixture_request_dto, calculation_dto=fixture_calculation_dto)
        assert isinstance(digest, str)
        assert len(digest) == 40  # sha1 hexdigest()
        assert fixture_request_dto == ql.get_request_dto(digest)
        assert fixture_calculation_dto == ql.get_calculation_dto(digest)
