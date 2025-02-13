import datetime
import _md5
import random
import time
from settings import LOADS_NOSQL_LOC
import json


class NoSuchLoadID(RuntimeError):
    pass


class AllowedStagesViolation(RuntimeError):
    pass


class Load:
    ALLOWED_STAGES = ['start', 'engage', 'drive', 'clear', 'finish', 'history']

    def __init__(self, cls, _type, stage, start, engage, clear, finish, client_num, driver_name, driver_num,
                 _id=None, last_update=None):
        if stage not in cls.ALLOWED_STAGES:
            raise RuntimeError(f'Unknown stage: {stage}')
        if _type not in ['internal', 'external']:
            raise RuntimeError(f'Unknown Load type: {_type}. Accepted only ["internal", "external"]')
        if _id is None:
            random_data = str(random.getrandbits(256)).encode('utf-8')
            _id = _md5.md5(random_data).hexdigest()
        if last_update is None:
            last_update = datetime.datetime.now()
        else:
            last_update = datetime.datetime.strptime('2025-02-13 12:03:40.852055', '%Y-%m-%d %H:%M:%S.%f')

        self.id = _id
        self.type = _type
        self.stage = stage
        self.stages = dict(
            start=start,
            engage=engage,
            drive=None,
            clear=clear,
            finish=finish
        )
        self.last_update = last_update
        self.client_num = client_num
        self.driver = dict(
            name=driver_name,
            num=driver_num
        )

    @classmethod
    def from_dict(cls, _dct):
        return cls(cls=cls,
                   _type=_dct['type'],
                   stage=_dct['stage'],
                   start=_dct['stages']['start'],
                   engage=_dct['stages']['engage'],
                   clear=_dct['stages']['clear'],
                   finish=_dct['stages']['finish'],
                   client_num=_dct['client_num'],
                   driver_name=_dct['driver']['name'],
                   driver_num=_dct['driver']['num'],
                   _id=_dct['id'],
                   last_update=_dct['last_update'])

    def save_to_dict(self):
        return dict(
            id=self.id,
            type=self.type,
            stage=self.stage,
            stages=self.stages,
            last_update=str(self.last_update),
            client_num=self.client_num,
            driver=self.driver
        )

    def expose_to_dict(self):
        return dict(
            id=self.id,
            type=self.type,
            stage=self.stage,
            stages=self.stages,
            last_update=self.last_update.strftime("%H:%M")
        )

    def get_driver_details(self, client_num):
        time.sleep(2)
        if client_num == self.client_num:
            return dict(
                driver_name=self.driver['name'],
                driver_num=self.driver['num']
            ), 'success', 200
        else:
            return dict(), 'Client match fail', 401

    def change_state(self, cls, new_stage):
        if new_stage not in cls.ALLOWED_STAGES:
            raise AllowedStagesViolation(f'Somebody tried to set stage that are not allowed ({new_stage})')
        self.stage = new_stage


class Loads:

    def __init__(self):
        self.loads = list()

    def add_load(self, load: Load):
        self.loads.append(load)

    @classmethod
    def from_loads_storage(cls, _dct):
        if _dct['loads_storage_version'] not in ['1.0']:
            raise RuntimeError(f'This loads_storage_version ({_dct["loads_storage_version"]}) is not supported')
        instance = cls()
        for load in _dct['loads']:
            instance.add_load(Load.from_dict(load))
        return instance

    def to_loads_storage(self):
        _loads = list()
        for load in self.loads:
            _loads.append(load.save_to_dict())
        return dict(
            loads_storage_version='1.0',
            timestamp=str(datetime.datetime.now()),
            loads=_loads
        )

    def expose_to_dict(self):
        _loads = list()
        for load in self.loads:
            _loads.append(load.expose_to_dict())
        return _loads

    def get_active_loads(self):
        _loads = list()
        for load in self.loads:
            if load.stage != 'history':
                _loads.append(load.expose_to_dict())
        return _loads

    def get_load_by_id(self, _id):
        for load in self.loads:
            if load.stage != 'history' and load.id == _id:
                return load
        raise NoSuchLoadID(f'There is no Loads with ID: {_id} in a memory storage')


with open(file=LOADS_NOSQL_LOC, mode='r', encoding='utf8', ) as f:
    contents = f.read()
dct = json.loads(contents)

loads_instance = Loads().from_loads_storage(dct)  # This is the main entrance


def base_input():
    loads_instance.add_load(Load(cls=Load,
                                 _type='internal',
                                 stage='start',
                                 start='Староконстантиновка',
                                 engage=None,
                                 clear=None,
                                 finish='Николаев',
                                 client_num='380953459607',
                                 driver_name='Микола',
                                 driver_num='380991231213',
                                 _id=None,
                                 last_update=None))
    loads_instance.add_load(Load(cls=Load,
                                 _type='internal',
                                 stage='drive',
                                 start='Староконстантиновка',
                                 engage=None,
                                 clear=None,
                                 finish='Николаев',
                                 client_num='380953459607',
                                 driver_name='Микола',
                                 driver_num='380991231213',
                                 _id=None,
                                 last_update=None))
    loads_instance.add_load(Load(cls=Load,
                                 _type='internal',
                                 stage='finish',
                                 start='Староконстантиновка',
                                 engage=None,
                                 clear=None,
                                 finish='Николаев',
                                 client_num='380953459607',
                                 driver_name='Микола',
                                 driver_num='380991231213',
                                 _id=None,
                                 last_update=None))
    loads_instance.add_load(Load(cls=Load,
                                 _type='external',
                                 stage='start',
                                 start='Староконстантиновка',
                                 engage='Киев',
                                 clear='Вроцлав',
                                 finish='Варшава',
                                 client_num='380953459607',
                                 driver_name='Микола',
                                 driver_num='380991231213',
                                 _id=None,
                                 last_update=None))
    loads_instance.add_load(Load(cls=Load,
                                 _type='external',
                                 stage='engage',
                                 start='Староконстантиновка',
                                 engage='Киев',
                                 clear='Вроцлав',
                                 finish='Варшава',
                                 client_num='380953459607',
                                 driver_name='Микола',
                                 driver_num='380991231213',
                                 _id=None,
                                 last_update=None))
    loads_instance.add_load(Load(cls=Load,
                                 _type='external',
                                 stage='drive',
                                 start='Староконстантиновка',
                                 engage='Киев',
                                 clear='Вроцлав',
                                 finish='Варшава',
                                 client_num='380953459607',
                                 driver_name='Микола',
                                 driver_num='380991231213',
                                 _id=None,
                                 last_update=None))
    loads_instance.add_load(Load(cls=Load,
                                 _type='external',
                                 stage='clear',
                                 start='Староконстантиновка',
                                 engage='Киев',
                                 clear='Вроцлав',
                                 finish='Варшава',
                                 client_num='380953459607',
                                 driver_name='Микола',
                                 driver_num='380991231213',
                                 _id=None,
                                 last_update=None))
    loads_instance.add_load(Load(cls=Load,
                                 _type='external',
                                 stage='finish',
                                 start='Староконстантиновка',
                                 engage='Киев',
                                 clear='Вроцлав',
                                 finish='Варшава',
                                 client_num='380953459607',
                                 driver_name='Микола',
                                 driver_num='380991231213',
                                 _id=None,
                                 last_update=None))


def storage_init():
    _str = json.dumps(loads_instance.to_loads_storage(), ensure_ascii=False)
    with open(file=LOADS_NOSQL_LOC, mode='w') as file:
        file.write(_str)
