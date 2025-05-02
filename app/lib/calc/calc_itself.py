
from app.lib.calc.place import Place
from app.lib.calc import depotpark, vehicles
from app.lib.utils import utils
import math
from app.lib.calc.statepark import Currency
from app.lib.calc.depotpark import NoDepots
from app.lib.ai.model import PRICE_AI_PREDICTOR
from app.lib.utils import compositor


DEPOT_PARK = depotpark.DEPOTPARK


def __calculate_distance(route):
    return route[0].distance_to(route[1])[0].distance + \
           route[1].distance_to(route[2])[0].distance + \
           route[2].distance_to(route[3])[0].distance


def __distance_ratio(dist: float) -> float:
    if dist < 0.0:
        raise RuntimeError('Calculated distance appeared to be negative')
    kdist = dist / 1000.0  # dist valued in meters kdist in kilometers
    # Hardcoded weights. See /RouteCalc_data/docs/distance_ratio_weights.xlsx
    d = 0.900
    e = 0.009
    f = 0.870
    g = 0.150
    h = 0.700
    return round(d / (math.log(e * kdist + f) + g) + h, 3)


def __select_vehicle(vehicle_id):
    for vehicle in vehicles.VEHICLES:
        if vehicle.id == vehicle_id:
            return vehicle

    
# def calculate_route(rqst):
#
#     place_a = Place(rqst['from']['lat'], rqst['from']['lng'],
#                     name=rqst['from']['name_short'],
#                     name_long=rqst['from']['name_long'],
#                     countrycode=rqst['from']['countrycode'])
#     place_b = Place(rqst['to']['lat'], rqst['to']['lng'],
#                     name=rqst['to']['name_short'],
#                     name_long=rqst['to']['name_long'],
#                     countrycode=rqst['to']['countrycode'])
#
#     try:
#         starting_depot = DEPOT_PARK.select_closest(DEPOT_PARK.filter_by(place_a.countrycode),
#                                                    [place_a],
#                                                    many_to_one=True)
#     except NoDepots:
#         starting_depot = DEPOT_PARK.select_closest(DEPOT_PARK.filter_by(None),
#                                                    [place_a],
#                                                    many_to_one=True)
#     try:
#         ending_depot = DEPOT_PARK.select_closest([place_b],
#                                                  DEPOT_PARK.filter_by(place_b.countrycode),
#                                                  many_to_one=False)
#     except NoDepots:
#         ending_depot = DEPOT_PARK.select_closest([place_b],
#                                                  DEPOT_PARK.filter_by(None),
#                                                  many_to_one=False)
#
#     route = [starting_depot, place_a, place_b, ending_depot]
#     visible_route = utils.__merge_same(route)
#     distance = __calculate_distance(route)  # distance in meters
#     ratio = 1.0 * starting_depot.departure_ratio * ending_depot.arrival_ratio * __distance_ratio(distance)
#     selected_vehicle = __select_vehicle(rqst['transport_id'])
#     price = float(selected_vehicle.price) * ratio
#
#     cost = (distance / 1000) * price  # distance in kilometers
#     currency = Currency.get_preferred(starting_depot.currency, ending_depot.currency)
#
#     return {'vehicle': selected_vehicle,
#             'total_distance': distance,
#             'price': price / currency.rate(),
#             'pfactor_vehicle': selected_vehicle.price,
#             'pfactor_departure': starting_depot.departure_ratio,
#             'pfactor_arrival': ending_depot.arrival_ratio,
#             'pfactor_distance': __distance_ratio(distance),
#             'cost': cost / currency.rate(),
#             'currency': str(currency),
#             'currency_rate': currency.rate(),
#             'route': visible_route,
#             'place_a': place_a,
#             'place_b': place_b,
#             'client_phone': rqst['phone_number']}


def plan_route(place_a, place_b):
    """
    Makes a complete route a vehicle should pass to complete an order
    :param place_a: Place from
    :param place_b: Place to
    :return: planned route
    """
    try:
        in_country_depots = DEPOT_PARK.filter_by(place_a.countrycode)
        starting_depot = place_a.chose_starting_depot(in_country_depots)

        in_country_depots = DEPOT_PARK.filter_by(place_b.countrycode)
        ending_depot = place_b.chose_ending_depot(in_country_depots)
    except NoDepots:
        all_depots = DEPOT_PARK.park
        starting_depot = place_a.chose_starting_depot(all_depots)
        ending_depot = place_b.chose_ending_depot(all_depots)
    return starting_depot, place_a, place_b, ending_depot


def calculate_route_ai(rqst):
    place_a = Place.from_rqst(rqst['from'])
    place_b = Place.from_rqst(rqst['to'])
    vehicle = __select_vehicle(rqst['transport_id'])
    route = plan_route(place_a, place_b)
    starting_depot, ending_depot = route[0], route[3]
    visible_route = route[1:-1]
    distance = __calculate_distance(route)  # distance in meters
    price = PRICE_AI_PREDICTOR.predict(route[0], route[3], vehicle)
    cost = (distance / 1000) * price  # distance in kilometers
    currency = Currency.get_preferred(starting_depot.currency, ending_depot.currency)
    return compositor.make_calculation_dto(
        details={
            'vehicle': vehicle,
            'total_distance': distance,
            'price': price / currency.rate(),
            'pfactor_vehicle': vehicle.price,
            'pfactor_departure': starting_depot.departure_ratio,
            'pfactor_arrival': ending_depot.arrival_ratio,
            'pfactor_distance': __distance_ratio(distance),
            'cost': cost / currency.rate(),
            'currency': str(currency),
            'currency_rate': currency.rate(),
            'route': visible_route,
            'place_a': place_a,
            'place_b': place_b,
            'client_phone': rqst['phone_number']},
        locale=rqst['locale'])


def calculate_route_reduced(rqst):
    place_a = Place(rqst['from']['lat'], rqst['from']['lng'],
                    name=rqst['from']['name_short'],
                    name_long=rqst['from']['name_long'],
                    countrycode=rqst['from']['countrycode'])
    place_b = Place(rqst['to']['lat'], rqst['to']['lng'],
                    name=rqst['to']['name_short'],
                    name_long=rqst['to']['name_long'],
                    countrycode=rqst['to']['countrycode'])

    try:
        starting_depot = DEPOT_PARK.select_closest(DEPOT_PARK.filter_by(place_a.countrycode),
                                                   [place_a],
                                                   many_to_one=True)
    except NoDepots:
        starting_depot = DEPOT_PARK.select_closest(DEPOT_PARK.filter_by(None),
                                                   [place_a],
                                                   many_to_one=True)
    try:
        ending_depot = DEPOT_PARK.select_closest([place_b],
                                                 DEPOT_PARK.filter_by(place_b.countrycode),
                                                 many_to_one=False)
    except NoDepots:
        ending_depot = DEPOT_PARK.select_closest([place_b],
                                                 DEPOT_PARK.filter_by(None),
                                                 many_to_one=False)

    route = [starting_depot, ending_depot]

    # distance_true = starting_depot.distance_to(ending_depot)[0].distance  # distance in meters
    distance = starting_depot.distance_haversine(ending_depot)*1.33
    if distance < 50000.0:
        distance = 50000.0
    ratio = 1.0 * starting_depot.departure_ratio * ending_depot.arrival_ratio * __distance_ratio(distance)
    selected_vehicle = __select_vehicle(rqst['transport_id'])
    price = float(selected_vehicle.price) * ratio

    cost = (distance / 1000) * price  # distance in kilometers
    currency = Currency.get_preferred(starting_depot.currency, ending_depot.currency)

    return {'vehicle': selected_vehicle,
            'total_distance': distance,
            'price': price / currency.rate(),
            'pfactor_vehicle': selected_vehicle.price,
            'pfactor_departure': starting_depot.departure_ratio,
            'pfactor_arrival': ending_depot.arrival_ratio,
            'pfactor_distance': __distance_ratio(distance),
            'cost': cost / currency.rate(),
            'currency': str(currency),
            'currency_rate': currency.rate(),
            'route': route,
            'place_a': place_a,
            'place_b': place_b,
            'client_phone': rqst['phone_number']}
