from app.lib.calc.place import Place
from app import settings
import sqlite3
import json
from app.lib.calc.depot import Depot
from app.lib.utils import cache
import logging

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

    def filter_by(self, iso_code: str):
        if iso_code is None:
            return self.park
        iso_code = iso_code.capitalize()
        some = [depot for depot in self.park if depot.state.iso_code.capitalize() == iso_code]
        if len(some) < 1:
            raise NoDepots(f'No available depots at {iso_code} iso_code')
        return some


def test_depotpark_storage_restoring():
    dp = DepotPark()
    a_dict = dp.as_dict()
    a_str = json.dumps(a_dict, ensure_ascii=False)
    with open(file=settings.DEPOTPARK_NOSQL_LOC, mode='w') as f:
        f.write(a_str)
    dp2 = DepotPark.from_file(filename=settings.DEPOTPARK_NOSQL_LOC)
    if sum(1 for place in dp.park if isinstance(place, Place)) == \
            sum(1 for place in dp2.park if isinstance(place, Place)):
        logging.debug('test_depotpark_storage_restoring() COMPLETE')
    else:
        logging.debug('test_depotpark_storage_restoring() FAILED')


DEPOTPARK = DepotPark.from_file(filename=settings.DEPOTPARK_NOSQL_LOC)
