import json
from app.impsettings import settings


class Currency:

    @classmethod
    def get_preferred(cls, cur1, cur2):
        priority = {'USD': 3, 'EUR': 2, 'UAH': 1}

        cur1_priority = priority[cur1.iso_code]
        cur2_priority = priority[cur2.iso_code]

        if cur1_priority >= cur2_priority:
            return cur1
        else:
            return cur2

    rates = {'UAH': 1.0,
             'USD': 41.0,
             'EUR': 45.0}

    def __init__(self, iso_code):
        if iso_code not in self.rates.keys():
            raise ValueError(f'Currency not set: {iso_code}')
        self.iso_code = iso_code

    def __str__(self):
        return self.iso_code

    def rate(self):
        return self.rates[self.iso_code]


class State:  # As a country as an area not a state of an element or smth

    def __init__(self, iso_code: str, currency: str, state_name: str, departure_ratio: float, arrival_ratio: float):
        self.iso_code = iso_code
        self.currency = Currency(currency)
        self.state_name = state_name
        self.departure_ratio = departure_ratio
        self.arrival_ratio = arrival_ratio

    @classmethod
    def from_dict(cls, dct):
        return cls(iso_code=dct['iso_code'],
                   currency=dct['currency'],
                   state_name=dct['state_name'],
                   departure_ratio=dct['departure_ratio'],
                   arrival_ratio=dct['arrival_ratio'])

    def to_dict(self):
        return {
            'iso_code': self.iso_code,
            'currency': str(self.currency),
            'state_name': self.state_name,
            'departure_ratio': self.departure_ratio,
            'arrival_ratio': self.arrival_ratio}


class StateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, State):
            return obj.to_dict()
        return json.JSONEncoder.default(self, obj)


class StatePark:

    def __init__(self, already_park: [State] = None):
        if already_park is not None and isinstance(already_park, list):
            """This is used by the def from_file(cls, filename) method"""
            self.park = already_park
        else:
            """This part will soon be deleted"""
            self.park = []

    @classmethod
    def from_file(cls, filename=settings.STATEPARK_NOSQL_LOC):
        # Reconstructing from file
        try:
            with open(file=filename, mode='r', encoding='utf8', ) as f:
                contents = f.read()
            struct = json.loads(contents)
            park = [State.from_dict(item) for item in struct['statepark']]
            return cls(park)
        except Exception as e:
            raise e

    def to_file(self, filename=settings.STATEPARK_NOSQL_LOC):
        # Saving to file
        a_dict = self.as_dict()
        a_str = json.dumps(a_dict, ensure_ascii=False)
        with open(file=filename, mode='w') as f:
            f.write(a_str)

    def as_dict(self):
        d = dict()
        d['statepark'] = [state.to_dict() for state in self.park]
        return d

    def find_by_iso(self, iso_code):
        for state in self.park:
            if state.iso_code == iso_code:
                return state
        raise RuntimeError(f'No such state: {iso_code}')


# statepark_init = StatePark([State(iso_code='UA', state_name='Ukraine', departure_ratio=1.0, arrival_ratio=1.0)])
# statepark_init.to_file(filename=f'../../{settings.STATEPARK_NOSQL_LOC}')
# statepark = StatePark.from_file(f'../../{settings.STATEPARK_NOSQL_LOC}')
statepark = StatePark.from_file(settings.STATEPARK_NOSQL_LOC)
