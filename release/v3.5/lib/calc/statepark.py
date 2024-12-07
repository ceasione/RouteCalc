import json
import settings


class State:  # As a country as an area not a state of an element or smth

    def __init__(self, iso_code: str, state_name: str, departure_ratio: float, arrival_ratio: float):
        self.iso_code = iso_code
        self.state_name = state_name
        self.departure_ratio = departure_ratio
        self.arrival_ratio = arrival_ratio

    @classmethod
    def from_dict(cls, dct):
        return cls(iso_code=dct['iso_code'],
                   state_name=dct['state_name'],
                   departure_ratio=dct['departure_ratio'],
                   arrival_ratio=dct['arrival_ratio'])

    def to_dict(self):
        return self.__dict__


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
pass
