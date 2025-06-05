from app import settings
import json
import app.lib.calc.loadables.statepark as statepark
from app.lib.calc.place import Place
from app.lib.calc.loadables.statepark import State
from app.lib.calc.loadables.loadable import Itemable


APIADR = settings.GOOGLE_APIADR
APIKEY = settings.GOOGLE_APIKEY


class Depot(Place, Itemable):

    def __init__(self, lat: float, lng: float,
                 name: str,
                 state_iso: str,
                 depot_id: int,
                 departure_ratio: float = None,
                 arrival_ratio: float = None):

        super().__init__(lat=lat, lng=lng, name=name)
        self.state: State = statepark.statepark.find_by_iso(state_iso)
        self.id = depot_id
        self._departure_ratio = departure_ratio
        self._arrival_ratio = arrival_ratio

    @property
    def departure_ratio(self):
        # If own ratio is None we return ratio of the state (country/region)
        if not self._departure_ratio:
            return self.state.departure_ratio
        return self._departure_ratio

    @property
    def arrival_ratio(self):
        # As above
        if not self._arrival_ratio:
            return self.state.arrival_ratio
        return self._arrival_ratio

    @property
    def currency(self):
        return self.state.currency

    def to_dict(self):
        return {
            'lat': self.lat,
            'lng': self.lng,
            'name': self.name,
            'state_iso': self.state.iso_code,
            'depot_id': self.id,
            'departure_ratio': self._departure_ratio,
            'arrival_ratio': self._arrival_ratio
        }


class DepotEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Depot):
            return obj.to_dict()
        return json.JSONEncoder.default(self, obj)
