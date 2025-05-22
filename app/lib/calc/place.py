from app import settings
from app.lib.utils import cache
import json
from abc import ABC


APIADR = settings.GOOGLE_APIADR
APIKEY = settings.GOOGLE_APIKEY


class LatLngAble(ABC):
    def __init__(self, lat: float, lng: float):
        self.lat: float = lat
        self.lng: float = lng
        self.cache = cache.cache_instance_factory()

    def distance_to(self, place_to):
        """
        Method to easily fetch distance from self to place_to
        :param place_to: Place
        :return: lib.calc.distance.Distance object
        """
        return self.cache.fetch_cached_distance([self], [place_to])[0]

    def distance_from(self, place_from):
        """
        Method to easily fetch distance from place_from to self
        :param place_from: Place
        :return: lib.calc.distance.Distance object
        """
        return self.cache.fetch_cached_distance([place_from], [self])[0]

    def _select_closest(self, list_from, list_to):
        """
        Select from two lists of Places a pair with minimum distance between them
        :param list_from: [Place, ]
        :param list_to: [Place, ]
        :return: lib.calc.distance.Distance object
        """
        distances = self.cache.fetch_cached_distance(list_from, list_to)
        distances.sort()
        return distances[0]

    def chose_starting_depot(self, park):
        """
        Chooses the closest depot from places in park to this Place
        :param park: Depotpark
        :return: Depot
        """
        return self._select_closest(park, [self]).place_from

    def chose_ending_depot(self, park):
        """
        Chooses the closest depot from this Place to the places in park
        :param park: Depotpark
        :return: Depot
        """
        return self._select_closest([self], park).place_to


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


class PlaceEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Place):
            d = dict(obj.__dict__)
            del d['cache']
            return d
        return json.JSONEncoder.default(self, obj)
