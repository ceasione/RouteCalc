from lib.calc.place import Place
import settings
from lib.utils.cache import Cache
import sqlite3
import json


APIADR = settings.GOOGLE_APIADR
APIKEY = settings.GOOGLE_APIKEY
DB_LOCATION = settings.DEPOT_DB_LOC
NOSQL_LOCATION = settings.DEPOT_NOSQL_LOC

# Database creation script to make a base from scratch
"""
CREATE TABLE "DepotPark" (
  "id"  INTEGER NOT NULL UNIQUE,
  "area"  TEXT NOT NULL COLLATE RTRIM,
  "name"  TEXT NOT NULL COLLATE RTRIM,
  "super"  INTEGER NOT NULL DEFAULT 0,
  "arrival_ratio"  REAL NOT NULL DEFAULT 1.0,
  "arrival_ratio_reason"  TEXT COLLATE RTRIM,
  "departure_ratio"  REAL NOT NULL DEFAULT 1.0,
  "departure_ratio_reason"  TEXT COLLATE RTRIM,
  "lat"  REAL NOT NULL,
  "lng"  REAL NOT NULL,
  PRIMARY KEY("id")
);
"""


class DepotPark:
    # def __new__(cls):
    #     # Singleton
    #     if not hasattr(cls, 'instance'):
    #         cls.instance = super(DepotPark, cls).__new__(cls)
    #     return cls.instance

    def __init__(self, already_park: [Place] = None):
        if already_park is not None and isinstance(already_park, list):
            self.park = already_park
        else:
            # raise RuntimeError('Deprecated function')
            self.park = list()
            for db_row in self.__read_db():
                self.park.append(Place(lat=db_row['lat'],
                                       lng=db_row['lng'],
                                       place_id=db_row['id'],
                                       area=db_row['area'],
                                       name=db_row['name'],
                                       atr_super=db_row['super'],
                                       arrival_ratio=db_row['arrival_ratio'],
                                       arrival_ratio_reason=db_row['arrival_ratio_reason'],
                                       departure_ratio=db_row['departure_ratio'],
                                       departure_ratio_reason=db_row['departure_ratio_reason']))

    def __read_db(self):
        self.conn = sqlite3.connect(DB_LOCATION, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.c = self.conn.cursor()
        self.c.execute("""
                        SELECT * FROM DepotPark;
                       """)
        rows = self.c.fetchall()
        # park = list()
        for row in rows:
            yield dict(id=row['id'],
                       area=row['area'],
                       name=row['name'],
                       super=row['super'],
                       arrival_ratio=row['arrival_ratio'],
                       arrival_ratio_reason=row['arrival_ratio_reason'],
                       departure_ratio=row['departure_ratio'],
                       departure_ratio_reason=row['departure_ratio_reason'],
                       lat=row['lat'],
                       lng=row['lng'])

        self.conn.close()

    @classmethod
    def from_file(cls, filename):
        # Reconstructing an object from file
        try:
            with open(file=filename, mode='r', encoding='utf8', ) as f:
                contents = f.read()
            struct = json.loads(contents)
            park = [Place.from_dict(item) for item in struct['park']]
            return cls(park)
        except Exception as e:
            raise e

    def as_dict(self):
        d = dict()
        d['park'] = [place.to_dict() for place in self.park]
        return d

    def select_closest_depot_raw(self, place):
        # Raw because we can do this more efficient by query several places at one GET-request
        # Find out which one of the depots is the closest to given place
        # Return Place
        closest_depot = self.park[0]
        for current_depot in self.park:
            if place.distance_to(current_depot) < place.distance_to(closest_depot):
                closest_depot = current_depot
        return closest_depot

    def select_closest_starting_depot(self, place):
        # Make a cache search and schedule to search cache-misses
        # Make a call to server
        # Cache it
        # Then select minimal

        distances = Cache().fetch_cached_distance(self.park, [place])
        zipped = list(zip(distances, self.park))
        distances.sort()
        for pair in zipped:
            if pair[0] == distances[0]:
                return pair[1]

    def select_closest_ending_depot(self, place):

        distances = Cache().fetch_cached_distance([place], self.park)
        zipped = list(zip(distances, self.park))
        distances.sort()
        for pair in zipped:
            if pair[0] == distances[0]:
                return pair[1]


def test_depotpark_storage_restoring():
    dp = DepotPark()
    a_dict = dp.as_dict()
    a_str = json.dumps(a_dict, ensure_ascii=False)
    with open(file='dbs/depotpark_nosql.json', mode='w') as f:
        f.write(a_str)
    dp2 = DepotPark.from_file(filename=NOSQL_LOCATION)
    if sum(1 for place in dp.park if isinstance(place, Place)) == \
            sum(1 for place in dp2.park if isinstance(place, Place)):
        print('test_depotpark_storage_restoring() COMPLETE')
    else:
        print('test_depotpark_storage_restoring() FAILED')


# test_depotpark_storage_restoring()
