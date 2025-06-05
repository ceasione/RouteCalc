from app.lib.calc.place import Place
from app.lib.calc.loadables.vehicles import Vehicle
from dataclasses import dataclass


@dataclass
class CalculationDTO:

    place_a_name: str
    place_a_name_long: str
    place_b_name: str
    place_b_name_long: str
    map_link: str
    place_chain: str
    chain_map_link: str
    distance: str
    transport_id: int
    transport_name: str
    transport_capacity: int
    price: str
    price_per_ton: str
    price_per_km: str
    is_price_per_ton: bool
    currency: str
    currency_rate: float
    pfactor_vehicle: str
    pfactor_departure: str
    pfactor_arrival: str
    pfactor_distance: str
    locale: str

    @classmethod
    def from_dict(cls, dct):
        return cls(**dct)


@dataclass
class RequestDTO:

    intent: str = None
    origin: Place = None
    destination: Place = None
    vehicle: Vehicle = None
    phone_num: str = None
    locale: str = None
    url: str = None
    ip: str = None

    def to_dict(self):
        return {
            'intent': self.intent,
            'origin': self.origin.to_dict(),
            'destination': self.destination.to_dict(),
            'vehicle': self.vehicle.id,
            'phone_num': self.phone_num,
            'locale': self.locale,
            'url': self.url,
            'ip': self.ip
        }
