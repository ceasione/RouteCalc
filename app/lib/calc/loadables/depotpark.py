
from app import settings
from app.lib.calc.loadables.depot import Depot
from app.lib.calc.loadables.loadable import Loadable
from pathlib import Path
from typing import Type


APIADR = settings.GOOGLE_APIADR
APIKEY = settings.GOOGLE_APIKEY
DB_LOCATION = settings.DEPOT_DB_LOC


DEPOT_PATH = Path(settings.DEPOTPARK_NOSQL_LOC)
DEPOT_TAG = 'depotpark'


class NoDepots(RuntimeError):
    pass


class DepotPark(Loadable):

    @property
    def data_path(self) -> Path:
        return DEPOT_PATH

    @property
    def item_type(self) -> Type:
        return Depot

    @property
    def item_tag(self) -> str:
        return DEPOT_TAG

    def filter_by(self, iso_code: str):
        if iso_code is None:
            return self.items
        some = [depot for depot in self.items if depot.state.iso_code.upper() == iso_code.upper()]
        if len(some) < 1:
            raise NoDepots(f'No available depots at {iso_code} iso_code')
        return some


DEPOTPARK = DepotPark().load(Path('/home/oliver/Projects/ISG.com/RouteCalc_data/dbs/depotpark_nosql.json'))
