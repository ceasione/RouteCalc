import json
from app import settings
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional

DATA_PATH = Path(settings.STATEPARK_NOSQL_LOC)
CURRENCY_PRIORITY = {'USD': 3, 'EUR': 2, 'UAH': 1}
CURRENCY_RATES = {'UAH': 1.0, 'USD': 41.0, 'EUR': 45.0}


class Currency:

    iso_code: str

    @staticmethod
    def get_preferred(cur1, cur2):
        prio1 = CURRENCY_PRIORITY[cur1.iso_code]
        prio2 = CURRENCY_PRIORITY[cur2.iso_code]
        return cur1 if prio1 >= prio2 else cur2

    def __init__(self, iso_code: str):
        if iso_code not in CURRENCY_RATES.keys():
            raise ValueError(f'Currency not set: {iso_code}')
        self.iso_code = iso_code

    def __str__(self):
        return self.iso_code

    def rate(self):
        return CURRENCY_RATES[self.iso_code]


@dataclass
class State:
    """
    State represents a country and have departure and arrival ratios
    (which can be reassigned by the Depots although)
    If Depot doesn't have its ratios - corresponding State's ratios
    is used instead

    Represents a country (state) with associated currency and transport ratios.

    The State object holds information about a country's ISO code, currency, and
    its default departure and arrival ratios used to make calculations.
    These ratios can be overridden by a Depot, if available. If not,
    the State's ratios are used as fallback values.

    Attributes:
        iso_code (str): ISO country code.
        currency (str or Currency): Currency used in the state; converted to a Currency instance on init.
        state_name (str): Human-readable name of the country/state.
        departure_ratio (float): Ratio used for calculating departure-related costs.
        arrival_ratio (float): Ratio used for calculating arrival-related costs.

    Methods:
        __post_init__(): Ensures currency is an instance of Currency.
        from_dict(dct): Creates a State instance from a dictionary.
        to_dict(): Converts the State to a serializable dictionary, stringifying the currency.
    """
    iso_code: str
    currency: str or Currency
    state_name: str
    departure_ratio: float
    arrival_ratio: float

    def __post_init__(self):
        if isinstance(self.currency, str):
            self.currency = Currency(self.currency)

    @classmethod
    def from_dict(cls, dct):
        return cls(**dct)

    def to_dict(self):
        data = asdict(self)
        data['currency'] = str(self.currency)
        return data


class StateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, State):
            return obj.to_dict()
        return json.JSONEncoder.default(self, obj)


class StatePark:
    """
    A container class for managing a collection of `State` instances.

    Provides functionality to load states from a JSON file, save them back,
    convert them to a dictionary format, and retrieve individual states by
    their ISO code.

    Attributes:
        park (List[State]): The list of State objects currently in the park.

    Methods:
        from_file(filename): Class method to create a StatePark from a JSON file.
        to_file(filename): Saves the current StatePark to a JSON file.
        as_dict(): Returns a dictionary representation of the StatePark.
        find_by_iso(iso_code): Returns the State with the given ISO code.
    """
    park: List[State]

    def __init__(self, already_park: Optional[List[State]] = None):
        self.park = []
        if already_park is not None and isinstance(already_park, list):
            """This is used by the def from_file(cls, filename) method"""
            self.park = already_park

    @classmethod
    def from_file(cls, filename: str = DATA_PATH):
        with open(file=filename, mode='r', encoding='utf8', ) as f:
            contents = f.read()
        struct = json.loads(contents)
        park = [State.from_dict(item) for item in struct['statepark']]
        return cls(park)

    def to_file(self, filename: str = settings.STATEPARK_NOSQL_LOC):
        a_dict = self.as_dict()
        a_str = json.dumps(a_dict, ensure_ascii=False)
        with open(file=filename, mode='w') as f:
            f.write(a_str)

    def as_dict(self):
        return {
            'statepark': [state.to_dict() for state in self.park]
        }

    def find_by_iso(self, iso_code: str) -> State:
        """
        Find and return State by iso code
        :param iso_code: (str) ('UA', 'GB', 'PL') ...
        :return: State object
        """
        try:
            return next((state for state in self.park if state.iso_code == iso_code))
        except StopIteration:
            raise ValueError(f'No such state: {iso_code}')


if __name__ == '__main__':
    DATA_PATH = Path('../../../') / settings.STATEPARK_NOSQL_LOC


statepark = StatePark.from_file(DATA_PATH)
