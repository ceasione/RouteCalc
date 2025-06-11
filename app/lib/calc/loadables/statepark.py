import json
from app import settings
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Type
from app.lib.calc.loadables.loadable import Itemable, Loadable

STATE_PATH = Path(settings.STATEPARK_LOC)
STATE_TAG = 'statepark'
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
class State(Itemable):
    """
    State represents a country and have departure and arrival ratios
    (which can be reassigned by the Depots although)
    If Depot doesn't have its ratios - corresponding State's ratios
    is used instead

    Represents a country (state) with associated currency and transport ratios.
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


class StatePark(Loadable):

    """
    A container class for managing a collection of `State` instances.
    Provides functionality to retrieve individual states by their ISO code.
    """

    @property
    def data_path(self) -> Path:
        return STATE_PATH

    @property
    def item_type(self) -> Type:
        return State

    @property
    def item_tag(self) -> str:
        return STATE_TAG

    def find_by_iso(self, iso_code: str) -> State:
        """
        Find and return State by iso code
        :param iso_code: (str) ('UA', 'GB', 'PL') ...
        :return: State object
        """
        try:
            return next((state for state in self.items if state.iso_code == iso_code))
        except StopIteration:
            raise ValueError(f'No such state: {iso_code}')


statepark = StatePark().load()
