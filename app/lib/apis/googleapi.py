
from app import settings
import requests
from app.lib.calc.distance import Distance
from typing import Iterable, Tuple, List, Set
from app.lib.calc.place import LatLngAble, Place
import backoff
from app.lib.utils.logger import logger


class GoogleApiRequestError(Exception):
    """
    Raises when any of errors occurs during request or response processing
    """


class API:

    def __init__(self):
        self.apiadr = settings.GOOGLE_APIADR
        self.apikey = settings.GOOGLE_APIKEY

    @staticmethod
    def _chunks(lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    @staticmethod
    def _parse_api_response(
            api_response: dict,
            origins: List[LatLngAble],
            destinations: List[LatLngAble]) -> List[Distance]:
        """
        Parses a Google Distance Matrix API response and extracts distance data between each origin-destination pair.

        :param api_response: Original response from API already in form of dict
        :param origins: List of origins the request was made
        :param destinations: List of origins the request was made

        It is very important to use exactly the same origins and destinations
        (and their order) that used in request
        :return: List of Distances
        """
        extracted_distances = []
        try:
            for i, row in enumerate(api_response['rows']):
                for j, element in enumerate(row['elements']):
                    if element['status'] == 'OK':
                        extracted_distances.append(Distance(
                            place_from=Place(lat=origins[i].lat, lng=origins[i].lng),
                            place_to=Place(lat=destinations[j].lat, lng=destinations[j].lng),
                            distance=element['distance']['value']
                        ))
        except (IndexError, KeyError):
            logger.exception('Failed to process Google Matrix API response')
            pass
        return extracted_distances

    @backoff.on_exception(backoff.expo,
                          requests.exceptions.RequestException,
                          max_time=15)
    def _make_api_request(self, origins_params: str, dest_params: str) -> dict:

        url_params = {'origins': origins_params,
                      'destinations': dest_params,
                      'mode': 'driving',
                      'key': self.apikey}
        return requests.get(self.apiadr, url_params).json()

    @staticmethod
    def _make_places_url_param(places: Iterable[LatLngAble]) -> str:
        """
        Constructs a URL parameter string in the form "lat1,lng1|lat2,lng2|..."
        from a list of place-like objects with .lat and .lng attributes.
        :param places: Iterable of LatLngAbles
        :return: URL parameter string
        """
        places_params = [f'{place.lat},{place.lng}' for place in places]
        return '|'.join(places_params)

    @staticmethod
    def _split_origins_destinations(
            dists: Iterable[Distance]
    ) -> Tuple[Set['LatLngAble'], Set['LatLngAble']]:
        """
        Builds two sets of unique origin and destination places from a collection of Distance objects.
        :param dists: Distances to resolve
        :return: Two sets of LatLngAbles to further provide them to an API request
        """
        origins = set()
        destinations = set()
        for distance in dists:
            origins.add(distance.place_from)
            destinations.add(distance.place_to)
        return origins, destinations

    def resolve_distances(self, unresolved: List[Distance]) -> Tuple[List[Distance], List[Distance]]:
        """
        Resolves a list of unresolved Distance objects by querying the Distance Matrix API in chunks.

        This method divides the provided origins and destinations into chunks that comply with the API's
        request limits, sends requests for all origin-destination pairs, and collects the resulting distance data.

        Each unresolved Distance is matched against the acquired data. If a match is found (based on equality),
        it is added to the resolved list and removed from the unresolved list.
        :param unresolved: Distances to resolve.
        :return: List of Resolved distances, List of Unresolved distances (in case of errors or API reasons)
        """

        origins, destinations = self._split_origins_destinations(unresolved)

        # Maximum of 25 origins or 25 destinations per request
        # Maximum 100 elements per request.
        chunk_size = 25 if len(origins) * len(destinations) <= 100 else 10
        chunks_of_origins = [chunk for chunk in self._chunks(list(origins), chunk_size)]
        chunks_of_destinations = [chunk for chunk in self._chunks(list(destinations), chunk_size)]

        # Requesting each chunk and extending result with each response
        acquired = []
        for chunk_orig in chunks_of_origins:
            for chunk_dest in chunks_of_destinations:
                api_response = self._make_api_request(
                    self._make_places_url_param(chunk_orig),
                    self._make_places_url_param(chunk_dest)
                )
                acquired.extend(self._parse_api_response(api_response, chunk_orig, chunk_dest))

        resolved = []
        for distance_candidate in unresolved.copy():
            try:
                # Here we are making resolved list from unresolved using acquired as base
                # Populating resolved while depopulating unresolved

                # Looking for match between one of unresolved and all the acquired
                index = acquired.index(distance_candidate)

                # Removing from unresolved appending to resolved
                distance_candidate.distance = acquired[index].distance  # Resolving distance
                resolved.append(distance_candidate)  # Appending recently resolved distance to resolved list
                unresolved.remove(distance_candidate)  # Removing recently resolved distance from unresolved list

            except ValueError:
                # List.index() Raises ValueError if the value is not present.
                # In this case it means that candidate was not resolved and
                # stays where it was. Do nothing
                pass
        return resolved, unresolved


GAPI = API()


# --------- TESTS ---------


def get_real_data():
    data = {
        'Leipzig':    (51.3397836,  12.3716368),
        'Dresden':    (51.0511947,  13.7396424),
        'Bratislava': (48.1475428,  17.1120985),
        'Wienn':      (48.2081985,  16.3710148),
        'Turin':      (45.0702042,   7.6873754),
        'Lisbon':     (38.7218354,  -9.1390602),
        'Santa Cruz': (28.4639704, -16.2523460),
        'Nowhere':    (38.6753128, -101.0819318)
    }

    return [
        Distance(Place(*data['Leipzig'], name='Leipzig'), Place(*data['Wienn'], name='Wienn')),
        Distance(Place(*data['Leipzig'], name='Leipzig'), Place(*data['Turin'], name='Turin')),
        Distance(Place(*data['Dresden'], name='Dresden'), Place(*data['Turin'], name='Turin')),
        Distance(Place(*data['Nowhere'], name='Nowhere'), Place(*data['Santa Cruz'], name='Santa Cruz')),  # Unresolve
        Distance(Place(*data['Bratislava'], name='Bratislava'), Place(*data['Lisbon'], name='Lisbon')),
        Distance(Place(*data['Santa Cruz'], name='Santa Cruz'), Place(*data['Lisbon'], name='Lisbon'))
    ]


def gen_synth_data(cases_num: int, single_orig: bool = False, single_dest: bool = False):
    from random import SystemRandom
    rnd = SystemRandom()
    max_lat = 52.5519534
    min_lat = 46.1468902
    max_lng = 26.1332058
    min_lng = 4.6238894

    dists = []
    lat_from = round(rnd.uniform(min_lat, max_lat), 7)
    lng_from = round(rnd.uniform(min_lng, max_lng), 7)
    lat_to = round(rnd.uniform(min_lat, max_lat), 7)
    lng_to = round(rnd.uniform(min_lng, max_lng), 7)
    for i in range(cases_num):
        if not single_orig:
            lat_from = round(rnd.uniform(min_lat, max_lat), 7)
            lng_from = round(rnd.uniform(min_lng, max_lng), 7)
        if not single_dest:
            lat_to = round(rnd.uniform(min_lat, max_lat), 7)
            lng_to = round(rnd.uniform(min_lng, max_lng), 7)
        dists.append(Distance(
            Place(lat_from, lng_from),
            Place(lat_to, lng_to)
        ))
    return dists


def test_resolved_unresolved(distances):

    resolved, unresolved = GAPI.resolve_distances(distances)
    assert len(resolved) == 5
    assert len(unresolved) == 1
    assert 560000 < resolved[0].distance < 589000  # Leipzig Wienn 560 - 588 km
    assert 990000 < resolved[1].distance < 1068000  # Leipzig Turin 990 - 1067 km
    assert 1029000 < resolved[2].distance < 1125000  # Dresden Turin 1029 - 1125 km
    assert 2934000 < resolved[3].distance < 2942000  # Bratislava Lisbon 2934 - 2942
    assert 1803000 < resolved[4].distance < 1805000  # Santa Cruz Lisbon 1804 km


def test_chunks(distances):

    resolved, unresolved = GAPI.resolve_distances(distances)
    return resolved, unresolved


def test_mixed_data(real: List, synth: List):
    from random import SystemRandom
    rnd = SystemRandom()
    both = real + synth
    rnd.shuffle(both)
    resolved, unresolved = GAPI.resolve_distances(both)
    return resolved, unresolved


if __name__ == '__main__':
    test_resolved_unresolved(get_real_data())
    test_chunks(gen_synth_data(25, single_orig=True, single_dest=True))
    test_mixed_data(get_real_data(), gen_synth_data(4))
