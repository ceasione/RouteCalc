
class WrongNumberError(ValueError):
    ...


ALLOWED_PREFIX = {'38039', '38067', '38068', '38096', '38097', '38098',
                  '38050', '38066', '38095', '38099', '38063', '38093',
                  '38073', '38091', '38092', '38094'}


def validate_phone_ukr(phone_number):
    """
    Validates a Ukrainian phone number string.

    Expects 12-digit string starting with one of ALLOWED_PREFIX.

    Raises:
        TypeError: if input is not a string
        ValueError: if length != 12 or contains non-digit characters
        WrongNumberError: if prefix not in allowed prefixes
    Returns:
        The validated phone_number string
    """

    if not isinstance(phone_number, str):
        raise TypeError('Phone number should be a string. It is not.')

    phone_number = phone_number.strip()

    if phone_number == 'nosms':
        return None  # This was hardcoded in frontend side and means that phone_number = None

    if len(phone_number) != 12:
        raise ValueError(f'Phone number expected length is 12. Got {len(phone_number)}')

    if not phone_number.isdigit():
        raise ValueError('Phone number chars expected to be numbers')

    if phone_number[:5] not in ALLOWED_PREFIX:
        raise WrongNumberError(f'Invalid phone number prefix: {phone_number[:5]}')

    return phone_number
