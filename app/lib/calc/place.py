from app.impsettings import settings
from app.lib.utils import cache
import json


APIADR = settings.GOOGLE_APIADR
APIKEY = settings.GOOGLE_APIKEY


class Place:

    def __init__(self,
                 lat,
                 lng,
                 name=None,
                 name_long=None,
                 countrycode=None):
        self.lat = lat
        self.lng = lng
        self.name = name
        self.name_long = name_long
        self.countrycode = countrycode
        self.cache = cache.cache_instance_factory()

    def to_dict(self):
        d = self.__dict__
        del d['cache']
        return d

    @classmethod
    def from_dict(cls, dct):
        return cls(lat=dct['lat'],
                   lng=dct['lng'],
                   name=dct['name'],
                   name_long=None)

    def distance_to(self, place_to):
        return self.cache.fetch_cached_distance([self], [place_to])

    def distance_from(self, place_from):
        return self.cache.fetch_cached_distance([place_from], [self])


class PlaceEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Place):
            d = dict(obj.__dict__)
            del d['cache']
            return d
        return json.JSONEncoder.default(self, obj)
