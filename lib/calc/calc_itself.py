
from lib.calc.place import Place
from copy import copy
from lib.calc.depotpark import DepotPark
from lib.calc import vehicles
from lib.utils import utils
import math


DEPOT_PARK = DepotPark()


def __calculate_distance(a, b, c, d):

    return 0 + \
           a.distance_to(b)[0].distance + \
           b.distance_to(c)[0].distance + \
           c.distance_to(d)[0].distance


def __distance_ratio(dist: float) -> float:
    # dist valued in meters
    # kdist valued in kilometers
    if dist < 0.0:
        raise RuntimeError('Calculated distance appeared to be negative')
    kdist = dist / 1000.0
    # Hardcoded weights
    d = 0.900
    e = 0.007
    f = 1.100
    g = 0.050
    h = 0.450

    return round(d / (math.log(e * kdist + f) + g) + h, 3)


def __old_distance_ratio(dist: float) -> float:
    """This method is deprecated and will be removed in the future."""
    # dist valued in meters
    # kdist valued in kilometers
    kdist = dist/1000.0

    if kdist < 0.0:
        raise RuntimeError('Calculated distance appeared to be negative')
    elif 0.0 <= kdist < 50.0:
        return 2.8
    elif 50.0 <= kdist < 100.0:
        return 2.2
    elif 100.0 <= kdist < 170.0:
        return 1.6
    elif 170.0 <= kdist < 200.0:
        return 1.3
    elif 200.0 <= kdist < 300.0:
        return 1.1
    elif 300.0 <= kdist < 600.0:
        return 1.0
    elif 600.0 <= kdist < 800.0:
        return 0.97
    elif 800.0 <= kdist < 1000.0:
        return 0.93
    elif 1000.0 <= kdist < 1200.0:
        return 0.86
    elif 1200.0 <= kdist < 1500.0:
        return 0.80
    else:
        return 0.78
    

def __select_vehicle(vehicle_id):

    for vehicle in vehicles.VEHICLES:

        if vehicle.id == vehicle_id:

            return vehicle

    
def calculate_route(rqst):

    place_a = Place(rqst['from']['lat'], rqst['from']['lng'],
                    name=rqst['from']['name_short'],
                    name_long=rqst['from']['name_long'])
    place_b = Place(rqst['to']['lat'], rqst['to']['lng'],
                    name=rqst['to']['name_short'],
                    name_long=rqst['to']['name_long'])

    starting_depot = copy(DEPOT_PARK.select_closest_starting_depot(place_a))
    ending_depot = copy(DEPOT_PARK.select_closest_ending_depot(place_b))
    route = [starting_depot, place_a, place_b, ending_depot]
    visible_route = utils.__merge_same(route)
    distance = __calculate_distance(route[0], route[1], route[2], route[3])  # distance in meters
    ratio = 1.0 * starting_depot.departure_ratio * ending_depot.arrival_ratio * __distance_ratio(distance)
    selected_vehicle = __select_vehicle(rqst['transport_id'])
    price = float(selected_vehicle.price) * ratio

    cost = (distance / 1000) * price  # distance in kilometers

    return {'vehicle': selected_vehicle,
            'total_distance': distance,
            'price': price,
            'pfactor_vehicle': selected_vehicle.price,
            'pfactor_departure': starting_depot.departure_ratio,
            'pfactor_arrival': ending_depot.arrival_ratio,
            'pfactor_distance': __distance_ratio(distance),
            'cost': cost,
            'route': visible_route,
            'place_a': place_a,
            'place_b': place_b,
            'client_phone': rqst['phone_number']}
