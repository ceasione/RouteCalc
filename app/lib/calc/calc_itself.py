
from app.lib.calc.place import Place
from app.lib.calc import depotpark, vehicles
import math
from app.lib.calc.statepark import Currency
from app.lib.calc.depotpark import NoDepots
from app.lib.ai.model import ML_MODEL
from app.lib.utils import compositor
from app.lib.calc.vehicles import Vehicle
from app.lib.calc.depotpark import Depot
from app.lib.calc.place import LatLngAble
from app.lib.utils.DTOs import CalculationDTO
from app.lib.utils.DTOs import RequestDTO
from typing import Callable
from typing import Tuple
from typing import cast


DEPOT_PARK = depotpark.DEPOTPARK


class DistanceMeters:

    @staticmethod
    def matrix(place_from: LatLngAble, place_to: LatLngAble) -> float:
        """
        Fetches distance between two Places with Google Matrix API or cache
        :param place_from: Place of the origin
        :param place_to: Place object of the destination
        :return: distance in meters
        """
        return float(place_from.distance_to(place_to).distance)

    @staticmethod
    def haversine(place_from: LatLngAble, place_to: LatLngAble) -> float:
        """
        Calculates distance between two Places with Haversine method
        :param place_from: Place of the origin
        :param place_to: Place object of the destination
        :return: distance in meters
        """
        r = 6371000  # Globe radius in meters
        phi1, phi2 = math.radians(place_from.lat), math.radians(place_to.lat)
        dphi = math.radians(place_to.lat - place_from.lat)
        dlambda = math.radians(place_to.lng - place_from.lng)

        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return r * c * 1.33  # Add 33% to better fit matrix distance so both of them are +- the same


class Predictors:
    ml_model = ML_MODEL

    @staticmethod
    def _distance_ratio(dist: float) -> float:
        """
        Function returns big ratio for short distances and low ratio for long distances
        It is continuous and can be viewed at /docs/distance_ratio_weights.xlsx
        :param dist: (float) distance in m
        :return: (float) ratio
        """
        kdist = dist / 1000.0  # dist valued in meters kdist in kilometers

        # Parameters can be guessed in xlsx file in interactive manner
        d = 0.900
        e = 0.009
        f = 0.870
        g = 0.150
        h = 0.700

        return round(d / (math.log(e * kdist + f) + g) + h, 3)

    @staticmethod
    def conventional(starting_depot: Depot, ending_depot: Depot, vehicle: Vehicle, distance: float) -> float:
        """
        Calculates price based on original method invented in 2021
        :param starting_depot: origin Depot
        :param ending_depot: destination Depot
        :param vehicle: Vehicle
        :param distance: float, distance in m
        :return: float, price per km on a given route and with given vehicle
        """

        # Short distances tend to produce very high ratio
        # Cap minimum distance to 50 km for model training
        if distance < 50000.0:
            distance = 50000.0

        ratio = starting_depot.departure_ratio * ending_depot.arrival_ratio * Predictors._distance_ratio(distance)
        return float(vehicle.price) * ratio

    @staticmethod
    def ml(starting_depot: Depot, ending_depot: Depot, vehicle: Vehicle, _distance: float) -> float:
        """
        Predicts price based on the ML model that was trained on the original method invented in 2021
        The model is dynamic and supposed to be finetuned from time to time, maybe in automatic manner
        :param starting_depot: origin Depot
        :param ending_depot: destination Depot
        :param vehicle: Vehicle
        :param _distance: float. Not used. It is needed just to match attributes.
        :return: float, price per km on a given route and with given vehicle
        """
        return Predictors.ml_model.predict(starting_depot.id, ending_depot.id, vehicle.id)


def __select_vehicle(vehicle_id):
    for vehicle in vehicles.VEHICLES:
        if vehicle.id == vehicle_id:
            return vehicle


def plan_route(place_a: Place, place_b: Place) -> Tuple[LatLngAble, LatLngAble, LatLngAble, LatLngAble]:
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
        all_depots = DEPOT_PARK.filter_by(None)
        starting_depot = place_a.chose_starting_depot(all_depots)
        ending_depot = place_b.chose_ending_depot(all_depots)
    return starting_depot, place_a, place_b, ending_depot


def calculate(route: Tuple[LatLngAble, LatLngAble, LatLngAble, LatLngAble],
              vehicle: Vehicle,
              meter: Callable[[LatLngAble, LatLngAble], float],
              predictor: Callable[[Depot, Depot, Vehicle, float], float]) -> Tuple[float, float, float]:

    assert len(route) == 4
    starting_depot, ending_depot = cast(Depot, route[0]), cast(Depot, route[3])
    distance = meter(route[0], route[1]) + meter(route[1], route[2]) + meter(route[2], route[3])
    price = predictor(starting_depot, ending_depot, vehicle, distance)
    cost = distance / 1000 * price  # Convert dist from m to km first as price is per kilometer
    return distance, price, cost


def process_request(request: RequestDTO) -> CalculationDTO:
    place_a = request.origin
    place_b = request.destination
    vehicle = request.vehicle
    route = plan_route(place_a, place_b)
    starting_depot, ending_depot = cast(Depot, route[0]), cast(Depot, route[3])
    visible_route = route[1:-1]
    distance, price, cost = calculate(route, vehicle, DistanceMeters.matrix, Predictors.ml)
    currency = Currency.get_preferred(starting_depot.currency, ending_depot.currency)
    return CalculationDTO(place_a_name=place_a.name,
                          place_a_name_long=place_a.name_long,
                          place_b_name=place_b.name,
                          place_b_name_long=place_b.name_long,
                          map_link=compositor.generate_map_url(place_a, place_b),
                          place_chain=compositor.generate_place_chain(*visible_route),
                          chain_map_link=compositor.generate_map_url(*visible_route),
                          distance=str(round(float(distance)/1000, 1)),
                          transport_id=vehicle.id,
                          transport_name=vehicle.name if request.locale == 'ru_UA' else vehicle.name_ua,
                          transport_capacity=vehicle.weight_capacity,
                          price=compositor.format_cost(cost),
                          currency=str(currency),
                          currency_rate=currency.rate(),
                          price_per_ton=compositor.format_cost_per_ton(cost / float(vehicle.weight_capacity)),
                          price_per_km=str(round(price, 2)),
                          is_price_per_ton=vehicle.price_per_ton,
                          pfactor_vehicle=vehicle.price,
                          pfactor_departure=str(starting_depot.departure_ratio),
                          pfactor_arrival=str(ending_depot.arrival_ratio),
                          pfactor_distance=str(0.0),
                          locale=request.locale)
