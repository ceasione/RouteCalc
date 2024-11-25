import settings
from lib.utils import cache
import json


APIADR = settings.GOOGLE_APIADR
APIKEY = settings.GOOGLE_APIKEY


class Place:

    def __init__(self, lat, lng, place_id=None, area=None, name=None, name_long=None, atr_super=False,
                 arrival_ratio=1.0, arrival_ratio_reason='',
                 departure_ratio=1.0, departure_ratio_reason=''):
        self.lat = lat
        self.lng = lng
        self.id = place_id
        self.area = area
        self.name = name
        self.name_long = name_long
        self.super = atr_super
        self.arrival_ratio = arrival_ratio
        self.arrival_ratio_reason = arrival_ratio_reason
        self.departure_ratio = departure_ratio
        self.departure_ratio_reason = departure_ratio_reason
        self.cache = cache.cache_instance_factory()

    def to_dict(self):
        d = self.__dict__
        del d['cache']
        return d

    @classmethod
    def from_dict(cls, dict):
        return cls(lat=dict['lat'],
                   lng=dict['lng'],
                   place_id=dict['id'],
                   area=dict['area'],
                   name=dict['name'],
                   name_long=None,
                   atr_super=dict['super'],
                   arrival_ratio=dict['arrival_ratio'],
                   arrival_ratio_reason=dict['arrival_ratio_reason'],
                   departure_ratio=dict['departure_ratio'],
                   departure_ratio_reason=dict['departure_ratio_reason'])

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
