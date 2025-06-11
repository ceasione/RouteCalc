import json
from dataclasses import dataclass
from dataclasses import asdict
from pathlib import Path
from app import settings
from typing import Type
from app.lib.calc.loadables.loadable import Itemable, Loadable


VEHICLES_PATH = Path(settings.VEHICLES_LOC)
VEHICLES_TAG = 'vehicles'


@dataclass
class Vehicle(Itemable):
    """
    Represents a transport type used for cost calculations and selection.

    A Vehicle instance encapsulates all necessary parameters for:
    - Pricing and logistics calculations
    - UI display and localization
    - Text generation and user interaction
    """
    id: int
    name: str
    name_ua: str
    price: float
    order: int
    length: float
    width: float
    height: float
    weight_capacity: float
    space_capacity: int
    cargoes_possible: str
    cargoes_possible_ua: str
    picture: str
    price_per_ton: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


class Vehicles(Loadable):
    """
    A collection class for managing Vehicle instances, loaded from and saved to a JSON file.

    Inherits from the Loadable abstract base class, supporting persistent loading/saving
    of vehicle data and allowing iteration and access by vehicle ID.
    """
    @property
    def data_path(self) -> Path:
        return VEHICLES_PATH

    @property
    def item_type(self) -> Type[Vehicle]:
        return Vehicle

    @property
    def item_tag(self) -> str:
        return VEHICLES_TAG

    def __iter__(self):
        return iter(self.items)

    @property
    def as_list(self):
        return self.items

    def get_by_id(self, vehicle_id: int) -> Vehicle:
        try:
            return next((vehicle for vehicle in self.items if vehicle.id == vehicle_id))
        except StopIteration:
            raise ValueError(f'No such vehicle ID: {vehicle_id}')


class VehicleEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Vehicle):
            return asdict(obj)
        return json.JSONEncoder.default(self, obj)


VEHICLES = Vehicles().load()
