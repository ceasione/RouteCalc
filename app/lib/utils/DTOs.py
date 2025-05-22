from app.lib.calc.place import Place
from app.lib.calc.vehicles import Vehicle
from dataclasses import dataclass


class LocaleDTO:

    ALLOWED_LOCALES = ('uk_UA', 'ru_UA')

    def __init__(self, locale: str):
        self.value = locale

        if self.value not in LocaleDTO.ALLOWED_LOCALES:
            # TODO: LOG
            self.value = LocaleDTO.ALLOWED_LOCALES[0]

    def __str__(self):
        return self.value

    def is_uk_ua(self):
        return True if self.value == 'uk_UA' else False

    def is_ru_ua(self):
        return True if self.value == 'ru_UA' else False

    def to_dict(self):
        return self.value

    @classmethod
    def from_dict(cls, dct):
        return cls(locale=dct['value'])


class CalculationDTO:
    def __init__(self,
                 place_a_name: str,
                 place_a_name_long: str,
                 place_b_name: str,
                 place_b_name_long: str,
                 map_link: str,
                 place_chain: str,
                 chain_map_link: str,
                 distance: str,
                 transport_id: int,
                 transport_name: str,
                 transport_capacity: int,
                 price: str,
                 price_per_ton: str,
                 price_per_km: str,
                 is_price_per_ton: bool,
                 currency: str,
                 currency_rate: float,
                 pfactor_vehicle: str,
                 pfactor_departure: str,
                 pfactor_arrival: str,
                 pfactor_distance: str,
                 locale: LocaleDTO):
        self.place_a_name = place_a_name
        self.place_a_name_long = place_a_name_long
        self.place_b_name = place_b_name
        self.place_b_name_long = place_b_name_long
        self.map_link = map_link
        self.place_chain = place_chain
        self.chain_map_link = chain_map_link
        self.distance = distance
        self.transport_id = transport_id
        self.transport_name = transport_name
        self.transport_capacity = transport_capacity
        self.price = price
        self.price_per_ton = price_per_ton
        self.price_per_km = price_per_km
        self.is_price_per_ton = is_price_per_ton
        self.currency = currency
        self.currency_rate = currency_rate
        self.pfactor_vehicle = pfactor_vehicle
        self.pfactor_departure = pfactor_departure
        self.pfactor_arrival = pfactor_arrival
        self.pfactor_distance = pfactor_distance
        self.locale = locale

    def to_dict(self):
        return {'place_a_name': self.place_a_name,
                'place_a_name_long': self.place_a_name_long,
                'place_b_name': self.place_b_name,
                'place_b_name_long': self.place_b_name_long,
                'map_link': self.map_link,
                'place_chain': self.place_chain,
                'chain_map_link': self.chain_map_link,
                'distance': self.distance,
                'transport_id': self.transport_id,
                'transport_name': self.transport_name,
                'transport_capacity': self.transport_capacity,
                'price': self.price,
                'price_per_ton': self.price_per_ton,
                'price_per_km': self.price_per_km,
                'is_price_per_ton': self.is_price_per_ton,
                'currency': self.currency,
                'currency_rate': self.currency_rate,
                'pfactor_vehicle': self.pfactor_vehicle,
                'pfactor_departure': self.pfactor_departure,
                'pfactor_arrival': self.pfactor_arrival,
                'pfactor_distance': self.pfactor_distance,
                'locale': self.locale.value}

    @classmethod
    def from_dict(cls, dct):
        return cls(place_a_name=dct['place_a_name'],
                   place_a_name_long=dct['place_a_name_long'],
                   place_b_name=dct['place_b_name'],
                   place_b_name_long=dct['place_b_name_long'],
                   map_link=dct['map_link'],
                   place_chain=dct['place_chain'],
                   chain_map_link=dct['chain_map_link'],
                   distance=dct['distance'],
                   transport_id=dct['transport_id'],
                   transport_name=dct['transport_name'],
                   transport_capacity=dct['transport_capacity'],
                   price=dct['price'],
                   price_per_ton=dct['price_per_ton'],
                   price_per_km=dct['price_per_km'],
                   is_price_per_ton=dct['is_price_per_ton'],
                   currency=dct['currency'],
                   currency_rate=dct['currency_rate'],
                   pfactor_vehicle=dct['pfactor_vehicle'],
                   pfactor_departure=dct['pfactor_departure'],
                   pfactor_arrival=dct['pfactor_arrival'],
                   pfactor_distance=dct['pfactor_distance'],
                   locale=LocaleDTO(dct['locale']))


# noinspection PyTypeChecker
@dataclass
class RequestDTO:

    def __init__(self):

        self.intent: str = None
        self.origin: Place = None
        self.destination: Place = None
        self.vehicle: Vehicle = None
        self.phone_num: str = None
        self.locale: LocaleDTO = None
        self.url: str = None
        self.ip: str = None

    def to_dict(self):
        return {
            'intent': self.intent,
            'origin': self.origin.to_dict(),
            'destination': self.destination.to_dict(),
            'vehicle': self.vehicle.id,
            'phone_num': self.phone_num,
            'locale': self.locale.to_dict(),
            'url': self.url,
            'ip': self.ip
        }
