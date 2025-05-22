
from app import settings


class Blacklist:

    def __init__(self):
        self.fname = settings.BLACKLIST_FILE_LOC
        self.list = self.__load_file(self.fname)

    @staticmethod
    def __load_file(fname) -> list:
        """
        Opens file, reads and renovates :self.list: with fresh copy
        :return: None
        """
        with open(fname, 'r') as file:
            return [line.strip() for line in file]

    def blacklist(self, req: str) -> None:
        """
        Adds an item (it supposed to be a phone number or an ip adress) to blacklist
        and appends item to the file
        Mode 'a' open for writing, appending to the end of the file if it exists

        :param req: (str) item to add
        :return: None
        """
        self.list.append(req)
        with open(settings.BLACKLIST_FILE_LOC, 'a') as file:
            file.write(f'{req}\n')

    def check(self, *args) -> bool:
        """
        Return True if any of items of :param args: is blacklisted
        Otherwise return False
        :param args: Tuple[str, ...]
        :return: True or False
        """
        return any(arg in self.list for arg in args)

    def spread(self, phone_number, client_ip) -> bool:
        """
        This method ensures pair of arguments are blacklisted
        Blacklisting other if one is present.

        :param phone_number: (str) Phone number to check
        :param client_ip: (str) IP to check
        :return: True if blacklist was modified, else False
        """
        num_present = self.check(phone_number)
        ip_present = self.check(client_ip)

        match (num_present, ip_present):
            case (True, False):
                self.blacklist(client_ip)
                return True
            case (False, True):
                self.blacklist(phone_number)
                return True
            case _:
                return False


BLACKLIST = Blacklist()
