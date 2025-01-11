from copy import copy

import settings
from lib.utils import cache
import json
import lib.calc.statepark as statepark
from lib.calc.place import Place
from lib.calc.statepark import State


APIADR = settings.GOOGLE_APIADR
APIKEY = settings.GOOGLE_APIKEY


class Depot(Place):

    def __init__(self, lat: float, lng: float,
                 name: str, state_iso: str,
                 departure_ratio: float = None,
                 arrival_ratio: float = None):
        super().__init__(lat=lat,
                         lng=lng,
                         name=name)
        self.state: State = statepark.statepark.find_by_iso(state_iso)
        if departure_ratio is not None:
            self.departure_ratio = departure_ratio
        if arrival_ratio is not None:
            self.arrival_ratio = arrival_ratio
        self.cache = cache.cache_instance_factory()

    def __getattr__(self, item):
        return getattr(self.state, item)

    @classmethod
    def from_dict(cls, dct):
        departure_ratio = None
        arrival_ratio = None
        if 'departure_ratio' in dct:
            departure_ratio = dct['departure_ratio']
        if 'arrival_ratio' in dct:
            arrival_ratio = dct['arrival_ratio']
        return cls(lat=dct['lat'],
                   lng=dct['lng'],
                   name=dct['name'],
                   state_iso=dct['state'],
                   departure_ratio=departure_ratio,
                   arrival_ratio=arrival_ratio)

    def to_dict(self):
        d = copy(self.__dict__)
        d['state'] = d['state'].iso_code
        del d['cache']
        return d


class DepotEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Depot):
            return obj.to_dict()
        return json.JSONEncoder.default(self, obj)
