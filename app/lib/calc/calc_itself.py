
import math
from typing import Callable, Tuple, Iterable, List
from typing import cast
from app.lib.ai.model import ML_MODEL
from app.lib.apis import googleapi as googleapi
from app.lib.apis.googleapi import GoogleApiRequestError
from app.lib.calc.place import Place, LatLngAble
from app.lib.calc.distance import Distance
from app.lib.calc.loadables import depotpark
from app.lib.calc.loadables.statepark import Currency
from app.lib.calc.loadables.vehicles import Vehicle
from app.lib.calc.loadables.depotpark import Depot, NoDepots
from app.lib.utils.DTOs import CalculationDTO
from app.lib.utils.DTOs import RequestDTO
from app.lib.utils import cache
from app.lib.utils import compositor
from app.lib.utils.logger import logger


DEPOT_PARK = depotpark.DEPOTPARK
CACHE = cache.CACHE
GAPI = googleapi.GAPI


class ZeroDistanceResultsError(RuntimeError):
    pass


class DistanceResolvers:

    @staticmethod
    def _produce_distances_from_places(places_from: Iterable[LatLngAble],
                                       places_to: Iterable[LatLngAble]) -> List[Distance]:
        """
        Generate a list of unresolved Distance objects for every unique pair of
        (place_from, place_to) where the two places are not the same.
        :param places_from: Iterable of Places or LatLngAbles
        :param places_to: Iterable of Places or LatLngAbles
        :return: List of unresolved Distance objects
        """
        product = []
        for plc_from in places_from:
            for plc_to in places_to:
                if plc_from != plc_to:
                    product.append(Distance(plc_from, plc_to))
        return product

    @staticmethod
    def _resolve_distances_using_cache(dists: Iterable[Distance], cache_) -> Tuple[List[Distance], List[Distance]]:
        resolved = []
        unresolved = []

        for dist in dists:
            meters: float = cache_.cache_look(
                dist.place_from.lat,
                dist.place_from.lng,
                dist.place_to.lat,
                dist.place_to.lng)
            if meters is not None and isinstance(meters, (int, float)):
                dist.distance = meters
                resolved.append(dist)
            else:
                unresolved.append(dist)

        return resolved, unresolved

    @staticmethod
    def _resolve_distances_using_api(dists: Iterable[Distance], gapi_) -> Tuple[List[Distance], List[Distance]]:
        """
        Implements protocol of resolving distances with Google API
        :param dists: Iterable of unresolved Distance objects
        :param gapi_: Google API object
        :return: resolved and unresolved dists
        """
        try:
            return gapi_.resolve_distances(dists)
        except GoogleApiRequestError as e:
            logger.exception(e)
            return [], [*dists]

    @staticmethod
    def matrix(places_from: Iterable[LatLngAble], places_to: Iterable[LatLngAble],
               cache_=CACHE, gapi_=GAPI) -> List[Distance]:
        """
        Fetches distance between two Places with Google Matrix API or cache
        :param places_from: Iterable of origin Places
        :param places_to: Iterable of destination Places
        :param cache_ Cache instance retrieving distances between
        geographic coordinates (defaults to global CACHE)
        :param gapi_ Google Matrix API instance retrieving distances
        with requests (defaults to global GAPI)
        :return: List of resolved Distance objects (sorted ascending)
        that containing .distance property or None if there is no land way existed
        :raises: ZeroDistanceResultsError in case any of the methods (Cache, API)
        did not produce useful distance
        """
        resolved, unresolved = [], DistanceResolvers._produce_distances_from_places(places_from, places_to)

        accum, unresolved = DistanceResolvers._resolve_distances_using_cache(unresolved, cache_)
        resolved.extend(accum)
        logger.debug(f'Cache resolved, unresolved: {len(resolved)}, {len(unresolved)}')

        accum, unresolved = DistanceResolvers._resolve_distances_using_api(unresolved, gapi_)
        for dist in accum:
            cache_.cache_it(
                dist.place_from.lat,
                dist.place_from.lng,
                dist.place_to.lat,
                dist.place_to.lng,
                dist.distance)

        if len(accum) > 0:
            resolved.extend(accum)
            logger.debug(f'Matrix API resolved, unresolved: {len(resolved)}, {len(unresolved)}')

        if len(unresolved) > 0:
            logger.warning(f'Distance matrix API failed to resolve some Distances: '
                           f'{", ".join(d.__repr__() for d in unresolved)}')

        if len(resolved) < 1:
            logger.error(f'No distances have been resolved')
            raise ZeroDistanceResultsError

        resolved.sort()
        return resolved

    @staticmethod
    def _haversine_step(place_from: LatLngAble, place_to: LatLngAble) -> float:
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

    @staticmethod
    def haversine(places_from: Iterable[LatLngAble], places_to: Iterable[LatLngAble]) -> List[Distance]:
        """
        Making a list of Distance's based on list of origins and list of destinations.
        Uses Haversine method at self._haversine_step
        The reason we need this is that to train a ml model matrix method is too slow.
        :param places_from: (LatLngAble, ) Iterable of origins
        :param places_to: (LatLngAble, ) Iterable of destinations
        :return: List of calculated Distance objects (sorted ascending)
        """
        distances = DistanceResolvers._produce_distances_from_places(places_from, places_to)

        for dist in distances:
            dist.distance = DistanceResolvers._haversine_step(dist.place_from, dist.place_to)
        distances.sort()
        return distances


class Predictors:

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
    def ml(starting_depot: Depot, ending_depot: Depot, vehicle: Vehicle, _distance: float, ml_model=ML_MODEL) -> float:
        """
        Predicts price based on the ML model that was trained on the original method invented in 2021
        The model is dynamic and supposed to be finetuned from time to time, maybe in automatic manner
        :param starting_depot: origin Depot
        :param ending_depot: destination Depot
        :param vehicle: Vehicle
        :param _distance: float. Not used. It is needed just to match attributes.
        :param ml_model: Optional parameter to replace model with mock
        :return: float, price per km on a given route and with given vehicle
        """
        return ml_model.predict(starting_depot.id, ending_depot.id, vehicle.id)


def plan_route(place_a: Place, place_b: Place, dptpark=DEPOT_PARK
               ) -> Tuple[LatLngAble, LatLngAble, LatLngAble, LatLngAble]:
    """
    Makes a complete route a vehicle should pass to complete an order
    :param place_a: Place from
    :param place_b: Place to
    :param dptpark: Depotpark or None for default
    :return: planned route
    """
    dist_resolver = DistanceResolvers.matrix
    try:
        # Acquiring distances from every filtered depots to our place, choosing the closest one
        in_country_depots = dptpark.filter_by(place_a.countrycode)
        starting_depot = dist_resolver(in_country_depots, [place_a])[0].place_from

        # Acquiring distances from our place to every filtered depots, choosing the closest one
        in_country_depots = dptpark.filter_by(place_b.countrycode)
        ending_depot = dist_resolver([place_b], in_country_depots)[0].place_to

    except (NoDepots, IndexError):  # That means the meter did not return any reasonable distance
        # Acquiring distances from our place to all depots ve have, choosing the closest one
        all_depots = dptpark.filter_by(None)
        starting_depot = dist_resolver(all_depots, [place_a])[0].place_from
        ending_depot = dist_resolver([place_b], all_depots)[0].place_to
    return starting_depot, place_a, place_b, ending_depot


def calculate(route: Tuple[LatLngAble, LatLngAble, LatLngAble, LatLngAble],
              vehicle: Vehicle,
              dist_resolver: Callable[[Iterable[LatLngAble], Iterable[LatLngAble]], List[Distance]],
              predictor: Callable[[Depot, Depot, Vehicle, float], float]) -> Tuple[float, float, float]:
    """
    Calculator itself. Makes distance calculation using meter, predicts price per km for
    given vehicle using predictor. Also makes cost calculation (= distance * price)
    :param route: Tuple of 4 LatLngAble. A route vehicle shold pass to complete an order
    :param vehicle: Vehicle object
    :param dist_resolver: One of the DistanceResolvers methods. Calculates distance between LatLngAble's
    :param predictor: One of the Predictors methods. Calculates price for given route and vehicle
    :return: (float, float, float) -> distance in meters, price in UAH per km, cost
    """
    starting_depot, ending_depot = cast(Depot, route[0]), cast(Depot, route[3])
    distance = \
        dist_resolver([route[0]], [route[1]])[0].distance + \
        dist_resolver([route[1]], [route[2]])[0].distance + \
        dist_resolver([route[2]], [route[3]])[0].distance
    price = predictor(starting_depot, ending_depot, vehicle, distance)
    cost = distance / 1000 * price  # Convert dist from m to km first as price is per kilometer
    return distance, price, cost


def process_request(request: RequestDTO) -> CalculationDTO:
    """
    Receives request dto, orchestrates calculation and produces response dto
    :param request: (RequestDTO)
    :return: (CalculationDTO)
    """
    place_a = request.origin
    place_b = request.destination
    vehicle = request.vehicle
    route = plan_route(place_a, place_b)
    starting_depot, ending_depot = cast(Depot, route[0]), cast(Depot, route[3])
    visible_route = route[1:-1]
    distance, price, cost = calculate(route, vehicle, DistanceResolvers.matrix, Predictors.ml)
    currency = Currency.get_preferred(starting_depot.currency, ending_depot.currency)
    logger.debug(f'distance, price, cost; currency: '
                 f'{distance}, {price}, {cost}; {currency.iso_code}: {currency.rate()}')
    return CalculationDTO(place_a_name=place_a.name,
                          place_a_name_long=place_a.name_long,
                          place_b_name=place_b.name,
                          place_b_name_long=place_b.name_long,
                          map_link=compositor.generate_map_url(place_a, place_b),
                          place_chain=compositor.generate_place_chain(*visible_route),
                          chain_map_link=compositor.generate_map_url(*visible_route),
                          distance=str(round(float(distance)/1000, 1)),
                          distance_unstr=round(float(distance)/1000, 1),
                          transport_id=vehicle.id,
                          transport_name=vehicle.name if request.locale == 'ru_UA' else vehicle.name_ua,
                          transport_capacity=int(vehicle.weight_capacity),
                          price=compositor.format_cost(compositor.round_cost(
                              cost/currency.rate())),
                          price_unstr=compositor.round_cost(cost/currency.rate()),
                          currency=str(currency),
                          currency_rate=currency.rate(),
                          price_per_ton=compositor.format_cost(compositor.round_cost(
                              cost / currency.rate() / float(vehicle.weight_capacity))),
                          price_per_ton_unstr=compositor.round_cost(
                              cost / currency.rate() / float(vehicle.weight_capacity)),
                          price_per_km=str(round(price/currency.rate(), 2)),
                          price_per_km_unstr=round(price/currency.rate(), 2),
                          is_price_per_ton=vehicle.price_per_ton,
                          pfactor_vehicle=str(vehicle.price),
                          pfactor_departure=str(starting_depot.departure_ratio),
                          pfactor_arrival=str(ending_depot.arrival_ratio),
                          pfactor_distance=str(0.0),
                          locale=request.locale)
