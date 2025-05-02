from app.impsettings import settings
import requests
import json
from app.lib.utils import cache
from app.lib.calc.distance import Distance


class ZeroDistanceResultsError(RuntimeError):
    pass


class API:

    def __init__(self):
        self.APIADR = settings.GOOGLE_APIADR
        self.APIKEY = settings.GOOGLE_APIKEY
        self.MAX_REQUEST_PLACES = settings.GOOGLE_MAX_REQUEST_PLACES
        self.cache = cache.cache_instance_factory()

    @staticmethod
    def __parse_distance(json_obj):

        _1 = json_obj['rows']
        _2 = _1[0]
        _3 = _2['elements']
        _4 = _3[0]
        if _4['status'] == 'ZERO_RESULTS':
            raise ZeroDistanceResultsError(_4['status'])
        _5 = _4['distance']
        _6 = _5['value']
        distance = int(_6)
        return distance

    @staticmethod
    def __parse_distances(json_obj):

        if json_obj['status'] != 'OK':
            raise RuntimeError('GOOGLE api call unexpected output: '+json_obj['status'])

        rows = json_obj['rows']
        distances = list()
        for row in rows:
            elements = row['elements']
            for element in elements:
                try:
                    distances.append(element['distance']['value'])
                except (IndexError, KeyError):
                    raise RuntimeError('GOOGLE api call unexpected output: '+json_obj['status'])

        return distances

    @staticmethod
    def __assemble_places_geo_coords(places):
        string_builder = list()
        for place in places:
            string_builder.append(str(place.lat))
            string_builder.append(str(','))
            string_builder.append(str(place.lng))
            string_builder.append(str('|'))
        string_builder.pop()
        return str().join(string_builder)

    @staticmethod
    def __chunks(lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    def __fetch_ab_distance(self, place_from, place_to):
        url_params = {'origins': self.__assemble_places_geo_coords([place_from[0]]),
                      'destinations': self.__assemble_places_geo_coords([place_to[0]]),
                      'key': self.APIKEY}
        response = requests.get(self.APIADR, url_params).text
        distance = self.__parse_distance(json.loads(response))
        return [Distance(place_from[0], place_to[0], distance)]

    def __fetch_many_to_b_distances(self, a_places_from, a_place_to):
        a_place_to = a_place_to[0]
        distances = list()

        def _run(places_from, place_to):
            url_params = {'origins': self.__assemble_places_geo_coords(places_from),
                          'destinations': self.__assemble_places_geo_coords([place_to]),
                          'key': self.APIKEY}
            response = requests.get(self.APIADR, url_params).text
            distances.extend(self.__parse_distances(json.loads(response)))

        for chunk in self.__chunks(a_places_from, self.MAX_REQUEST_PLACES):
            _run(chunk, a_place_to)

        if len(a_places_from) != len(distances):
            raise RuntimeError('Unexpected API response')
        pairs = list()
        for _zip in zip(a_places_from, distances):
            pairs.append(Distance(_zip[0], a_place_to, _zip[1]))

        return pairs

    def __fetch_a_to_many_distances(self, a_place_from, a_places_to):
        a_place_from = a_place_from[0]
        distances = list()

        def _run(place_from, places_to):
            url_params = {'origins': self.__assemble_places_geo_coords([place_from]),
                          'destinations': self.__assemble_places_geo_coords(places_to),
                          'key': self.APIKEY}
            response = requests.get(self.APIADR, url_params).text
            distances.extend(self.__parse_distances(json.loads(response)))

        for chunk in self.__chunks(a_places_to, self.MAX_REQUEST_PLACES):
            _run(a_place_from, chunk)

        if len(a_places_to) != len(distances):
            raise RuntimeError('Unexpected API response')
        pairs = list()
        for _zip in zip(a_places_to, distances):
            pairs.append(Distance(a_place_from, _zip[0], _zip[1]))

        return pairs

    def fetch_distance(self, places_from, places_to):
        # Takes list(Places) even if Place to Place -> [Place, ] to [Place, ]
        # many to many not realized

        if len(places_from) == 1 and len(places_to) > 1:
            return self.__fetch_a_to_many_distances(places_from, places_to)
        elif len(places_from) > 1 and len(places_to) == 1:
            return self.__fetch_many_to_b_distances(places_from, places_to)
        elif len(places_from) == 1 and len(places_to) == 1:
            return self.__fetch_ab_distance(places_from, places_to)
        elif len(places_from) > 1 and len(places_to) > 1:
            raise RuntimeError('Not implemented')
        else:
            raise RuntimeError('Invalid arguments')


def api_instance_factory(_singleton=API()):
    return _singleton
