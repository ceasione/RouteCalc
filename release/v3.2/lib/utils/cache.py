import sqlite3
import settings
from lib.calc.distance import Distance


class Cache:

    # Database creation script to make a base from scratch
    """
    CREATE TABLE "Distances" (
        "from_lat"	REAL NOT NULL,
        "from_lng"	REAL NOT NULL,
        "to_lat"	REAL NOT NULL,
        "to_lng"	REAL NOT NULL,
        "distance_meters"	INTEGER NOT NULL
    );

    CREATE INDEX geo ON Distances (from_lat, from_lng, to_lat, to_lng);
    """

    def __init__(self):

        self.CACHE_LOCATION = settings.CACHE_LOCATION
        self.conn = sqlite3.connect(self.CACHE_LOCATION, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.c = self.conn.cursor()

    def __del__(self):

        self.conn.close()

    def cache_look(self, from_lat, from_lng, to_lat, to_lng):
        self.c.execute("""
            SELECT distance_meters
            FROM Distances
            WHERE (from_lat = ? and from_lng = ?) and (to_lat = ? and to_lng = ?)
            """, (from_lat, from_lng, to_lat, to_lng))
        rows = self.c.fetchall()

        if len(rows) > 0:
            row = rows[0]
            dist = row['distance_meters']

            return dist
        else:
            return None

    def cache_it(self, from_lat, from_lng, to_lat, to_lng, distance):
        if not self.cache_look(from_lat, from_lng, to_lat, to_lng):  # avoiding duplicates
            self.c.execute("""
                INSERT INTO Distances (
                    "from_lat",
                    "from_lng",
                    "to_lat",
                    "to_lng",
                    "distance_meters")
                VALUES (?, ?, ?, ?, ?)
            """, (from_lat, from_lng, to_lat, to_lng, distance))
            self.conn.commit()

    def fetch_cached_distance(self, places_from, places_to):
        from lib.apis import googleapi
        api = googleapi.api_instance_factory()
        # Takes list(Places) even if Place to Place -> [Place] to [Place]
        # 1. Check arguments
        if type(places_from) != list:
            raise RuntimeError('Wrong arguments: places_from not a list')

        if type(places_to) != list:
            raise RuntimeError('Wrong arguments: places_to not a list')

        i = 10
        while i > 0:
            i -= 1
            missed_from = set()
            missed_to = set()
            distances = list()

            for place_from in places_from:
                for place_to in places_to:
                    # Cache look
                    rest = self.cache_look(place_from.lat, place_from.lng, place_to.lat, place_to.lng)
                    if not rest:
                        missed_from.add(place_from)
                        missed_to.add(place_to)
                    else:
                        distances.append(Distance(place_from, place_to, rest))

            if len(missed_from) == 0 and len(missed_to) == 0:
                # print('Completely from cache')
                return distances
            else:
                print('Cache miss, fetching ...')
                distances = api.fetch_distance(list(missed_from), list(missed_to))
                for distance in distances:
                    _place_from = distance.place_from
                    _place_to = distance.place_to
                    _distance = distance.distance
                    self.cache_it(_place_from.lat, _place_from.lng,
                                  _place_to.lat, _place_to.lng,
                                  _distance)
                continue

        return api.fetch_distance(places_from, places_to)


def cache_instance_factory(_singleton=Cache()):
    return _singleton
