import json


class Vehicle(object):

    def __init__(self,
                 a_id,
                 name,
                 price,
                 order,
                 length,
                 width,
                 height,
                 weight_capacity,
                 space_capacity,
                 cargoes_possible,
                 price_per_ton=False,
                 picture=None):

        self.id = a_id
        self.name = name
        self.price = price
        self.order = order
        self.length = length
        self.width = width
        self.height = height
        self.weight_capacity = weight_capacity
        self.space_capacity = space_capacity
        self.cargoes_possible = cargoes_possible
        self.price_per_ton=price_per_ton
        self.picture = picture


class VehicleEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Vehicle):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)


VEHICLES = list()

VEHICLES.append(Vehicle(a_id=0,
                name='Тент 20',
                price=40.0,
                order=1,
                length=13.6,
                width=2.45,
                height=2.70,
                weight_capacity=22,
                space_capacity=90,
                cargoes_possible='Любые грузы на паллетах, в бегах и мешках',
                picture='https://api.intersmartgroup.com/static/icons/tent20.svg'))

VEHICLES.append(Vehicle(a_id=1,
                name='Тент 5',
                price=23.0,
                order=2,
                length=7.0,
                width=2.45,
                height=2.50,
                weight_capacity=5,
                space_capacity=45,
                cargoes_possible='Любые грузы на паллетах, в бегах и мешках',
                picture='https://api.intersmartgroup.com/static/icons/gaz.svg'))

VEHICLES.append(Vehicle(a_id=2,
                name='Зерновоз',
                price=56.0,
                order=3,
                length=10.0,
                width=2.40,
                height=2.0,
                weight_capacity=25,
                space_capacity=50,
                cargoes_possible='Сыпучие грузы навалом',
                price_per_ton=True,
                picture='https://api.intersmartgroup.com/static/icons/grain_carrier.svg'))

VEHICLES.append(Vehicle(a_id=3,
                name='Автоцистерна',
                price=65.0,
                order=4,
                length=0.0,
                width=0.0,
                height=0.0,
                weight_capacity=25,
                space_capacity=30,
                cargoes_possible='Наливные грузы, химические либо пищевые',
                price_per_ton=True,
                picture='https://api.intersmartgroup.com/static/icons/oil_carrier.svg'))

VEHICLES.append(Vehicle(a_id=4,
                name='Микроавтобус',
                price=16.0,
                order=5,
                length=3.0,
                width=1.5,
                height=1.8,
                weight_capacity=1,
                space_capacity=8,
                cargoes_possible='Любые грузы, вещи, мебель',
                picture='https://api.intersmartgroup.com/static/icons/bus.svg'))

VEHICLES.append(Vehicle(a_id=5,
                name='Эвакуатор',
                price=24.0,
                order=6,
                length=3.0,
                width=2.0,
                height=2.0,
                weight_capacity=2.8,
                space_capacity=0,
                cargoes_possible='Один легковой автомобиль',
                picture='https://api.intersmartgroup.com/static/icons/vehicle_carrier.svg'))

VEHICLES.append(Vehicle(a_id=6,
                name='Автовоз',
                price=19.2,  # (Эвакуатор) - 20 %
                order=7,
                length=3.0,
                width=2.0,
                height=2.0,
                weight_capacity=2.8,
                space_capacity=0,
                cargoes_possible='Восемь легковых авто',
                picture='https://api.intersmartgroup.com/static/icons/multivehicle_carrier.svg'))
