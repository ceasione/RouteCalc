from copy import copy

from app import settings
from app.lib.utils import cache
import json
import app.lib.calc.statepark as statepark
from app.lib.calc.place import Place
from app.lib.calc.statepark import State


APIADR = settings.GOOGLE_APIADR
APIKEY = settings.GOOGLE_APIKEY


class Depot(Place):

    def __init__(self, lat: float, lng: float,
                 name: str, state_iso: str,
                 departure_ratio: float = None,
                 arrival_ratio: float = None,
                 _id: int = None):
        super().__init__(lat=lat,
                         lng=lng,
                         name=name)
        self.state: State = statepark.statepark.find_by_iso(state_iso)
        if departure_ratio is not None:
            self.departure_ratio = departure_ratio
        if arrival_ratio is not None:
            self.arrival_ratio = arrival_ratio
        self.cache = cache.cache_instance_factory()
        self.id = _id

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
                   arrival_ratio=arrival_ratio,
                   _id=dct['id'])

    def to_dict(self):
        d = copy(self.__dict__)
        d['state'] = d['state'].iso_code
        del d['cache']
        del d['name_long']
        del d['countrycode']
        return d


class DepotEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Depot):
            return obj.to_dict()
        return json.JSONEncoder.default(self, obj)
