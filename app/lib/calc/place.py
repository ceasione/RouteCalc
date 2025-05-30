from app import settings
# from app.lib.utils import cache
import json
from abc import ABC


APIADR = settings.GOOGLE_APIADR
APIKEY = settings.GOOGLE_APIKEY


class LatLngAble(ABC):
    def __init__(self, lat: float, lng: float):
        self.lat: float = lat
        self.lng: float = lng

    def __eq__(self, other):
        if not isinstance(other, LatLngAble):
            raise NotImplemented

        return all((
            round(self.lat, 6) == round(other.lat, 6),
            round(self.lng, 6) == round(other.lng, 6)
        ))

    def __hash__(self):
        return hash((round(self.lat), round(self.lng)))


class Place(LatLngAble):

    def __init__(self,
                 lat: float,
                 lng: float,
                 name=None,
                 name_long=None,
                 countrycode=None):
        super().__init__(lat, lng)
        self.name = name
        self.name_long = name_long
        self.countrycode = countrycode

    def __repr__(self):
        return f'Place [{self.name} lat: {self.lat}, lng: {self.lng}]'

    def to_dict(self):
        d = self.__dict__
        return d

    @classmethod
    def from_rqst(cls, rqst):
        return cls(rqst['lat'],
                   rqst['lng'],
                   name=rqst['name_short'],
                   name_long=rqst['name_long'],
                   countrycode=rqst['countrycode'])

    @classmethod
    def from_dict(cls, dct):
        return cls(lat=dct['lat'],
                   lng=dct['lng'],
                   name=dct['name'],
                   name_long=None)


class PlaceEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Place):
            d = dict(obj.__dict__)
            del d['cache']
            return d
        return json.JSONEncoder.default(self, obj)
