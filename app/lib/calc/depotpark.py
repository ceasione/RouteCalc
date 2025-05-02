from app.lib.calc.place import Place
from app.impsettings import settings
import sqlite3
import json
from app.lib.calc.depot import Depot
from app.lib.utils import utils, cache

APIADR = settings.GOOGLE_APIADR
APIKEY = settings.GOOGLE_APIKEY
DB_LOCATION = settings.DEPOT_DB_LOC


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


class NoDepots(RuntimeError):
    pass


class DepotPark:

    def __init__(self, already_park: [Place] = None):
        self.cache = cache.cache_instance_factory()
        if already_park is not None and isinstance(already_park, list):
            """This is used by the def from_file(cls, filename) method"""
            self.park = already_park
        else:
            """This part will soon be deleted"""
            self.park = list()
            for db_row in self.__read_db():
                self.park.append(Depot(lat=db_row['lat'],
                                       lng=db_row['lng'],
                                       name=db_row['name'],
                                       state_iso='UA',
                                       departure_ratio=db_row['departure_ratio'],
                                       arrival_ratio=db_row['arrival_ratio']))

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
            park = [Depot.from_dict(item) for item in struct['depotpark']]
            return cls(park)
        except Exception as e:
            raise e

    def as_dict(self):
        d = dict()
        d['depotpark'] = [place.to_dict() for place in self.park]
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

    def filter_by(self, iso_code: str):
        if iso_code is None:
            return self.park
        iso_code = iso_code.capitalize()
        some = list()
        for depot in self.park:
            if iso_code == depot.state.iso_code.capitalize():
                some.append(depot)
        if len(some) == 0:
            raise NoDepots(f'No available depots at {iso_code} iso_code')
        return some

    # def select_closest(self, list_from: [Place], list_to: [Place], many_to_one: bool):
    #
    #     # Check and return as soon as duplicate is found
    #     for from_item in list_from:
    #         for to_item in list_to:
    #             match = from_item.lat == to_item.lat and \
    #                     from_item.lng == to_item.lng
    #             if match:
    #                 return from_item if many_to_one else to_item
    #
    #     distances = self.cache.fetch_cached_distance(list_from, list_to)
    #     distances.sort()
    #     if many_to_one:
    #         return distances[0].place_from
    #
    #     else:
    #         #  one to many
    #         return distances[0].place_to

    def select_closest_starting_depot(self, place):
        """DEPRECATED"""
        # Make a cache search and schedule to search cache-misses
        # Make a call to server
        # Cache it
        # Then select minimal

        distances = self.cache.fetch_cached_distance(self.park, [place])
        zipped = list(zip(distances, self.park))
        distances.sort()
        for pair in zipped:
            if pair[0] == distances[0]:
                return pair[1]

    def select_closest_ending_depot(self, place):
        """DEPRECATED"""
        distances = self.cache.fetch_cached_distance([place], self.park)
        zipped = list(zip(distances, self.park))
        distances.sort()
        for pair in zipped:
            if pair[0] == distances[0]:
                return pair[1]


def test_depotpark_storage_restoring():
    dp = DepotPark()
    a_dict = dp.as_dict()
    a_str = json.dumps(a_dict, ensure_ascii=False)
    with open(file=settings.DEPOTPARK_NOSQL_LOC, mode='w') as f:
        f.write(a_str)
    dp2 = DepotPark.from_file(filename=settings.DEPOTPARK_NOSQL_LOC)
    if sum(1 for place in dp.park if isinstance(place, Place)) == \
            sum(1 for place in dp2.park if isinstance(place, Place)):
        utils.log_safely('test_depotpark_storage_restoring() COMPLETE')
    else:
        utils.log_safely('test_depotpark_storage_restoring() FAILED')


# test_depotpark_storage_restoring()
DEPOTPARK = DepotPark.from_file(filename=settings.DEPOTPARK_NOSQL_LOC)
pass
