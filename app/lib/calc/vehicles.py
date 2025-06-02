import json
from dataclasses import dataclass
from dataclasses import asdict
from pathlib import Path
from app.settings import VEHICLES_LOC
from typing import List, Sequence
import logging


DATA_PATH = Path(VEHICLES_LOC)


@dataclass
class Vehicle:
    """
    Represents a transport type used for cost calculations and selection.

    A Vehicle instance encapsulates all necessary parameters for:
    - Pricing and logistics calculations
    - UI display and localization
    - Text generation and user interaction

    Attributes:
        id (int): Unique identifier for the vehicle.
        name (str): Vehicle name (default language).
        name_ua (str): Vehicle name in Ukrainian.
        price (float): Base price for using this vehicle.
        order (int): Display or processing order priority.
        length (float): Vehicle length in meters.
        width (float): Vehicle width in meters.
        height (float): Vehicle height in meters.
        weight_capacity (float): Maximum weight capacity in tons.
        space_capacity (int): Volume or item count capacity.
        cargoes_possible (str): Description of possible cargo types (default language).
        cargoes_possible_ua (str): Description of possible cargo types in Ukrainian.
        picture (str): URL or path to the vehicle image.
        price_per_ton (bool): Whether pricing is calculated per ton (default: False).
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


class Vehicles(Sequence):

    """
    Represents a collection of Vehicle objects loaded from a JSON file.

    This class implements the Sequence interface, allowing iteration,
    indexing, and length queries over the loaded vehicles.

    Attributes:
        _vehicles (List[Vehicle]): Internal list of Vehicle instances.

    Methods:
        as_list(): Returns the internal list of vehicles.
    """

    _vehicles: List[Vehicle]

    def __init__(self, fname=DATA_PATH):
        self._vehicles = []
        with open(fname, 'r', encoding='utf-8') as f:
            vehicles = json.load(f)
        for vehicle in vehicles:
            self._vehicles.append(Vehicle(**vehicle))

    def __iter__(self):
        return iter(self._vehicles)

    def __getitem__(self, index):
        return self._vehicles[index]

    def __len__(self):
        return len(self._vehicles)

    def as_list(self):
        return self._vehicles


class VehicleEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Vehicle):
            return asdict(obj)
        return json.JSONEncoder.default(self, obj)


# ------------- TESTING ---------------


def initialize_file_storage():
    """
    Initialize the vehicle data file with default hardcoded values.

    This function should be run only once during the initial setup.
    It attempts to create a new file at DATA_PATH and writes a predefined
    list of Vehicle objects to it in JSON format using the VehicleEncoder.

    If the file already exists, the function does nothing except log the
    FileExistsError exception.

    Returns:
        None
    """
    init_vehicles = [
        Vehicle(
            id=0,
            name='Тент 20',
            name_ua='Тент 20',
            price=45.0,
            order=1,
            length=13.6,
            width=2.45,
            height=2.70,
            weight_capacity=22,
            space_capacity=90,
            cargoes_possible='Любые грузы на паллетах, в бегах и мешках',
            cargoes_possible_ua='Будь-які вантажі на палетах, беги і мішки',
            picture='https://api.intersmartgroup.com/static/icons/tent20-v2.svg'),
        Vehicle(
            id=6,
            name='Тент 10',
            name_ua='Тент 10',
            price=37.5,
            order=2,
            length=8.5,
            width=2.45,
            height=2.7,
            weight_capacity=10,
            space_capacity=60,
            cargoes_possible='Любые грузы на паллетах, в бегах и мешках',
            cargoes_possible_ua='Будь-які вантажі на палетах, беги і мішки',
            picture='https://api.intersmartgroup.com/static/icons/tent10.svg'),
        Vehicle(
            id=1,
            name='Тент 5',
            name_ua='Тент 5',
            price=32.0,
            order=3,
            length=7.0,
            width=2.45,
            height=2.50,
            weight_capacity=5,
            space_capacity=45,
            cargoes_possible='Любые грузы на паллетах, в бегах и мешках',
            cargoes_possible_ua='Будь-які вантажі на палетах, беги і мішки',
            picture='https://api.intersmartgroup.com/static/icons/gaz.svg'),
        Vehicle(
            id=2,
            name='Зерновоз',
            name_ua='Зерновоз',
            price=45.0,
            order=4,
            length=10.0,
            width=2.40,
            height=2.0,
            weight_capacity=25,
            space_capacity=50,
            cargoes_possible='Сыпучие грузы навалом',
            cargoes_possible_ua='Насипні вантажі навалом',
            price_per_ton=True,
            picture='https://api.intersmartgroup.com/static/icons/grain_carrier.svg'),
        Vehicle(
            id=3,
            name='Автоцистерна',
            name_ua='Автоцистерна',
            price=65.0,
            order=5,
            length=0.0,
            width=0.0,
            height=0.0,
            weight_capacity=25,
            space_capacity=30,
            cargoes_possible='Наливные грузы, химические либо пищевые',
            cargoes_possible_ua='Рідкі вантажі, хімічні або харчові',
            price_per_ton=True,
            picture='https://api.intersmartgroup.com/static/icons/oil_carrier.svg'),
        Vehicle(
            id=4,
            name='Микроавтобус',
            name_ua='Мікроавтобус',
            price=18.0,
            order=6,
            length=3.0,
            width=1.5,
            height=1.8,
            weight_capacity=1,
            space_capacity=8,
            cargoes_possible='Любые грузы, вещи, мебель',
            cargoes_possible_ua='Будь-які вантажі, речі, меблі',
            picture='https://api.intersmartgroup.com/static/icons/bus.svg'),
        Vehicle(
            id=5,
            name='Автовоз',
            name_ua='Автовоз',
            price=20.0,
            order=7,
            length=3.0,
            width=2.0,
            height=2.0,
            weight_capacity=2.8,
            space_capacity=0,
            cargoes_possible='Одно легковое авто',
            cargoes_possible_ua='Одне легкове авто',
            picture='https://api.intersmartgroup.com/static/icons/vehicle_carrier.svg')
    ]

    try:
        with open(DATA_PATH, mode='x') as file:
            file.write(json.dumps(init_vehicles, cls=VehicleEncoder, ensure_ascii=False, indent=1))
    except FileExistsError as e:
        logging.exception(e)


if __name__ == '__main__':
    DATA_PATH = Path('../../../') / VEHICLES_LOC
    initialize_file_storage()


# ------------- TESTING ---------------


VEHICLES = Vehicles()
