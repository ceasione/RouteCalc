import sqlite3
from app import settings
from app.lib.calc.distance import Distance
import app.lib.apis.telegramapi2 as tgapi2
import logging


class Cache:

    """
    A SQLite-backed caching utility for storing and retrieving distances between geographic coordinates.

    This class is designed to reduce calls to an external distance API (Google Matrix API) by maintaining
    a local cache of previously queried distances. It supports:

    - Efficient lookups of cached distances (cache_look)
    - Safe insertion of new distances with retry and fallback (cache_it_safe)
    - Emergency fallback to in-memory cache on persistent SQLite errors (such as disk is full)
    - Bulk distance retrieval with automatic cache population (fetch_cached_distance)

    The expected table schema is:
        CREATE TABLE "Distances" (
            "from_lat"        REAL NOT NULL,
            "from_lng"        REAL NOT NULL,
            "to_lat"          REAL NOT NULL,
            "to_lng"          REAL NOT NULL,
            "distance_meters" INTEGER NOT NULL
        );

        CREATE INDEX geo ON Distances (from_lat, from_lng, to_lat, to_lng);

    Attributes:
        CACHE_LOCATION (str): Path to the SQLite cache file, taken from `settings.CACHE_LOCATION`.
        conn (sqlite3.Connection): Active database connection (disk or memory-based).
        c (sqlite3.Cursor): Cursor object for executing SQL commands.
        emergency_mode (bool): Flag indicating whether the cache is operating in fallback (memory) mode.

    Note:
        - The `Distance` and `Place` types are assumed to be external classes with appropriate attributes.
        - This class is meant to be used as a singleton, via `cache_instance_factory()`.
    """

    def __init__(self):

        self.CACHE_LOCATION = settings.CACHE_LOCATION
        self.disk_connection = sqlite3.connect(self.CACHE_LOCATION, check_same_thread=False)
        self.memory_connection = None
        self.emergency_mode = False
        self.conn = self.disk_connection
        self.conn.row_factory = sqlite3.Row
        self.c = self.conn.cursor()
        self.g_api = None

    def __enable_emergency_mode(self):
        self.memory_connection = sqlite3.connect('file::memory:?cache=shared', uri=True, check_same_thread=False)
        self.disk_connection.backup(self.memory_connection)
        self.conn.close()
        self.conn = self.memory_connection
        self.conn.row_factory = sqlite3.Row
        self.c = self.conn.cursor()
        self.emergency_mode = True
        tgapi2.send_developer("Emergency mode enabled. Cache turned into in-memory mode.")

    def __del__(self):

        self.conn.close()

    def cache_look(self, from_lat, from_lng, to_lat, to_lng):
        """
        Retrieves a cached distance value between two geographic coordinates, if available.

        Queries the local SQLite Distances table for a record matching the given origin and
        destination coordinates. If a match is found, the stored distance in meters is returned;
        otherwise, returns None.

        :param from_lat: (float) From place latitude
        :param from_lng: (float) From place longtitude
        :param to_lat: (float) To place latitude
        :param to_lng: (float) To place longtitude
        :return: float or None: The cached distance in meters if found, otherwise None
        """
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

    def cache_it_safe(self, from_lat, from_lng, to_lat, to_lng, distance):
        """
        Safely inserts a distance record into the cache, avoiding duplicates and
        handling transient database errors.

        Before insertion, the method checks if a distance record for the given coordinate pair
        already exists. If not, it attempts to insert it. If a `sqlite3.OperationalError` occurs,
        it retries once before triggering emergency mode and notifying the developer.
        :param from_lat: (float) From place latitude
        :param from_lng: (float) From place longtitude
        :param to_lat: (float) To place latitude
        :param to_lng: (float) To place longtitude
        :param distance: int
        :return: None
        """
        for attempt in range(2):
            try:
                if not self.cache_look(from_lat, from_lng, to_lat, to_lng):  # Check if it is already present in the db
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
                    break
            except sqlite3.OperationalError as e:
                tgapi2.send_developer('sqlite3.OperationalError at Cache module', e)
                self.__enable_emergency_mode()
        else:
            tgapi2.send_developer('Run out of attempts to cache!')

    def cache_it(self, from_lat, from_lng, to_lat, to_lng, distance):
        self.cache_it_safe(from_lat, from_lng, to_lat, to_lng, distance)

    def fetch_cached_distance(self, places_from, places_to):
        """
        Retrieves distance information between each pair of Places in places_from and places_to,
        using a local cache to minimize external API calls.

        If a distance value between a pair of places is found in the cache, it is used directly.
        Otherwise, the missing distances are fetched from an external API,
        stored in the cache, and then retrived. This process is repeated up to 10 times to maximize
        cache usage before falling back to fetching all distances from the API.

        Parameters:
            places_from (list): A list of origin Place objects.
            places_to (list): A list of destination Place objects.

        Returns:
            list: A list of `Distance` objects, each representing the distance between a place_from and place_to.

        Raises:
            RuntimeError: If either places_from or places_to is not a list.
        """

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
                print('Cache hit')
                return distances
            else:
                logging.debug('Cache miss, fetching ...')

                # Avoiding circular import error
                if self.g_api is None:
                    from app.lib.apis import googleapi
                    self.g_api = googleapi.api_instance_factory()

                distances = self.g_api.fetch_distance(list(missed_from), list(missed_to))
                for distance in distances:
                    _place_from = distance.place_from
                    _place_to = distance.place_to
                    _distance = distance.distance
                    self.cache_it(_place_from.lat, _place_from.lng,
                                  _place_to.lat, _place_to.lng,
                                  _distance)
                logging.debug(f'Succesfully cached distance')

        return self.g_api.fetch_distance(places_from, places_to)


def cache_instance_factory(_singleton=Cache()):
    return _singleton
