
import pytest
import app.lib.utils.request_processor as request_processor
from app.lib.utils.request_processor import ValidationError
from app.lib.utils.number_tools import WrongNumberError


class FakeFlaskRequest:

    def __init__(self, data, remote_addr):
        self.data = data
        self.remote_addr = remote_addr

    def get_json(self, force: bool) -> dict:
        return self.data


def test_process_normal(flask_request_calculate, remote_addr, dto_request_calculate):
    flask_request = FakeFlaskRequest(flask_request_calculate, remote_addr)

    dto_request = request_processor.process(flask_request)
    assert dto_request == dto_request_calculate


def test_process_bad_intent(flask_request_calculate, remote_addr):
    flask_request = FakeFlaskRequest(flask_request_calculate, remote_addr)
    flask_request.data['intent'] = 'someintent'
    with pytest.raises(ValidationError):
        request_processor.process(flask_request)


def test_process_bad_origin(flask_request_calculate, remote_addr):
    flask_request = FakeFlaskRequest(flask_request_calculate, remote_addr)

    flask_request.data['from']['lat'] = 'text at float field'
    with pytest.raises(ValidationError):
        request_processor.process(flask_request)

    flask_request.data['from']['name_short'] = ''
    with pytest.raises(ValidationError):
        request_processor.process(flask_request)

    flask_request.data['from'] = None
    with pytest.raises(ValidationError):
        request_processor.process(flask_request)

    del(flask_request.data['from'])
    with pytest.raises(ValidationError):
        request_processor.process(flask_request)


def test_process_bad_destination(flask_request_calculate, remote_addr):
    flask_request = FakeFlaskRequest(flask_request_calculate, remote_addr)

    flask_request.data['to']['lat'] = 'text at float field'
    with pytest.raises(ValidationError):
        request_processor.process(flask_request)

    flask_request.data['to']['name_short'] = ''
    with pytest.raises(ValidationError):
        request_processor.process(flask_request)

    flask_request.data['to'] = None
    with pytest.raises(ValidationError):
        request_processor.process(flask_request)

    del(flask_request.data['to'])
    with pytest.raises(ValidationError):
        request_processor.process(flask_request)


@pytest.mark.parametrize('id_', [0, 1, 2, 3, 4, 5, 6])
def test_process_good_transport(flask_request_calculate, remote_addr, id_):
    flask_request = FakeFlaskRequest(flask_request_calculate, remote_addr)
    flask_request.data['transport_id'] = id_
    request_processor.process(flask_request)


@pytest.mark.parametrize('id_', [-1, 2.5, 'test', None, 7, 8])
def test_process_bad_transport(flask_request_calculate, remote_addr, id_):
    flask_request = FakeFlaskRequest(flask_request_calculate, remote_addr)
    flask_request.data['transport_id'] = id_
    with pytest.raises(ValidationError):
        request_processor.process(flask_request)


@pytest.mark.parametrize('num', [
    123, '123', '+380423456701', '38044123456', '38044123456789101112'
])
def test_process_bad_phone(flask_request_calculate, remote_addr, num):
    flask_request = FakeFlaskRequest(flask_request_calculate, remote_addr)

    flask_request.data['phone_number'] = num
    with pytest.raises(ValidationError):
        request_processor.process(flask_request)


@pytest.mark.parametrize('num', [
    '380441234567', '380321234567', '380621234567', '380381234567', '380624234567'
])
def test_process_wrong_phone(flask_request_calculate, remote_addr, num):
    flask_request = FakeFlaskRequest(flask_request_calculate, remote_addr)

    flask_request.data['phone_number'] = num
    with pytest.raises(WrongNumberError):
        request_processor.process(flask_request)


@pytest.mark.parametrize('num', [
    '380391234567', '380671234567', '380981234567', '380951234567', '380734234567', 'nosms'
])
def test_process_good_phone(flask_request_calculate, remote_addr, num):
    flask_request = FakeFlaskRequest(flask_request_calculate, remote_addr)

    flask_request.data['phone_number'] = num
    request_processor.process(flask_request)
