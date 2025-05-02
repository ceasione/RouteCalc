from app.impsettings import settings
from app.lib.utils import cache
import json
import math


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

    def distance_to(self, place_to):
        return self.cache.fetch_cached_distance([self], [place_to])

    def distance_from(self, place_from):
        return self.cache.fetch_cached_distance([place_from], [self])

    def _select_closest(self, list_from, list_to):
        distances = self.cache.fetch_cached_distance(list_from, list_to)
        return distances.sort()[0]

    def chose_starting_depot(self, park):
        return self._select_closest(park, [self]).place_from

    def chose_ending_depot(self, park):
        return self._select_closest([self], park).place_to

    def distance_haversine(self, place_to):
        r = 6371000  # Globe radius in meters
        phi1, phi2 = math.radians(self.lat), math.radians(place_to.lat)
        dphi = math.radians(place_to.lat - self.lat)
        dlambda = math.radians(place_to.lng - self.lng)

        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return r * c


class PlaceEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Place):
            d = dict(obj.__dict__)
            del d['cache']
            return d
        return json.JSONEncoder.default(self, obj)
