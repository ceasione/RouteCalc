

class WrongNumberError (ValueError):
    pass


class NumValidator:

    def __init__(self):
        self.suppress_warning = None
        self.ukr_codes = ('38039', '38067', '38068', '38096', '38097', '38098',
                          '38050', '38066', '38095', '38099', '38063', '38093',
                          '38073', '38091', '38092', '38094')

    def __isdigit(self, char):
        self.suppress_warning = None
        if len(char) != 1:
            raise RuntimeError()

        if char in '0123456789':
            return True
        else:
            return False

    def __is_all_digits(self, string):
        for char in string:
            if not self.__isdigit(char):
                return False
        return True

    def __starts_with_special(self, string):
        return string.startswith(self.ukr_codes)

    def is_valid_phone_ukr(self, phone_number):

        if not isinstance(phone_number, str):
            return False
        if len(phone_number) != 12:
            return False
        if not self.__is_all_digits(phone_number):
            return False
        if not self.__starts_with_special(phone_number):
            return False

        return True

    def validate_phone_ukr(self, phone_number):

        if not isinstance(phone_number, str):
            raise TypeError('Phone number should be a string')
        if len(phone_number) != 12:
            raise ValueError('Phone number expected length is 12. Got '+str(len(phone_number)))
        if not self.__is_all_digits(phone_number):
            raise ValueError('Phone number chars expected all numbers')
        if not self.__starts_with_special(phone_number):
            raise WrongNumberError(phone_number)

        return phone_number


singleton = NumValidator()


def get_instance():
    return singleton
