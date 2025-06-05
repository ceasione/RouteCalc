from app import settings
import json
from abc import ABC


APIADR = settings.GOOGLE_APIADR
APIKEY = settings.GOOGLE_APIKEY


class LatLngAble(ABC):
    """
    Abstract base class for objects that represent geographic coordinates.

    This class provides equality and hashing behavior for latitude/longitude pairs,
    rounded to a precision of 6 decimal places for equality and for hashing.

    Attributes:
        lat (float): Latitude of the location.
        lng (float): Longitude of the location.

    Methods:
        __eq__(other): Compares two LatLngAble instances with precision rounding.
        __hash__(): Returns a hash based on rounded latitude and longitude.
    """
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
    """
    Represents a geographical place with coordinates and optional metadata.

    Inherits from LatLngAble to provide latitude/longitude-based equality and hashing.

    Attributes:
        lat (float): Latitude of the place (inherited).
        lng (float): Longitude of the place (inherited).
        name (str, optional): Short or common name of the place.
        name_long (str, optional): Full or extended name of the place.
        countrycode (str, optional): ISO 3166-1 alpha-2 country code.

    Methods:
        __repr__(): Returns a string representation of the place.
        to_dict(): Returns a dictionary representation of the place's attributes.
    """

    def __init__(self, lat: float, lng: float, name=None, name_long=None, countrycode=None):
        super().__init__(lat, lng)
        self.name = name
        self.name_long = name_long
        self.countrycode = countrycode

    def __repr__(self):
        return f'{self.name} lat: {self.lat}, lng: {self.lng}'

    def to_dict(self):
        return self.__dict__


class PlaceEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Place):
            d = dict(obj.__dict__)
            del d['cache']
            return d
        return json.JSONEncoder.default(self, obj)
