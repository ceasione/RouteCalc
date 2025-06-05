
import sqlite3
from app import settings
import app.lib.apis.telegramapi2 as tgapi2
from typing import Optional
from app.lib.utils.logger import logger


class Cache:

    """
    A SQLite-backed caching utility for storing and retrieving distances between geographic coordinates.

    This class is designed to reduce calls to an external distance API (Google Matrix API) by maintaining
    a local cache of previously queried distances. It supports:

    - Efficient lookups of cached distances (cache_look)
    - Insertion of new distances (cache_it)

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

    def close(self):
        self.conn.close()

    SELECT_QUERY = """
        SELECT distance_meters
        FROM Distances
        WHERE (from_lat = ? and from_lng = ?) and (to_lat = ? and to_lng = ?)
    """

    def cache_look(self, from_lat: float, from_lng: float, to_lat: float, to_lng: float) -> Optional[float]:
        """
        Retrieves a cached distance value between two geographic coordinates, if available.

        Queries the local SQLite Distances table for a record matching the given origin and
        destination coordinates. If a match is found, the stored distance in meters is returned;
        otherwise, returns None.

        :param from_lat: (float) From place latitude
        :param from_lng: (float) From place longitude
        :param to_lat: (float) To place latitude
        :param to_lng: (float) To place longitude
        :return: float or None: The cached distance in meters if found, otherwise None
        """
        self.c.execute(self.SELECT_QUERY, (from_lat, from_lng, to_lat, to_lng))
        row = self.c.fetchone()
        if row:
            return float(row['distance_meters'])
        return None

    INSERT_QUERY = """
        INSERT INTO Distances (
            "from_lat",
            "from_lng",
            "to_lat",
            "to_lng",
            "distance_meters")
        VALUES (?, ?, ?, ?, ?)
    """

    def cache_it(self, from_lat: float, from_lng: float, to_lat: float, to_lng: float, distance: float) -> None:
        """
        Inserts a distance record into the cache. In case of errors, logging and do nothing

        If a `sqlite3.Error` occurs, it notifies dev team.
        :param from_lat: (float) From place latitude
        :param from_lng: (float) From place longitude
        :param to_lat: (float) To place latitude
        :param to_lng: (float) To place longitude
        :param distance: (float) distance between places in meters
        :return: None
        """
        try:
            self.c.execute(self.INSERT_QUERY, (from_lat, from_lng, to_lat, to_lng, int(distance)))
            self.conn.commit()
        except sqlite3.Error as e:
            logger.exception('Error adding item to Cache')
            tgapi2.send_developer('Error adding item to Cache', e)


CACHE = Cache()
