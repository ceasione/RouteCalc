import datetime
import _md5
import random
import time
from settings import LOADS_NOSQL_LOC
import json

import settings
from lib.apis import telegramapi2
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext
from queue import Queue
import secrets
from abc import ABC, abstractmethod
import os
import threading
import time


class NoSuchLoadID(RuntimeError):
    pass


class AllowedStagesViolation(RuntimeError):
    pass


class Load:
    ALLOWED_STAGES = ['start', 'engage', 'drive', 'clear', 'finish', 'history']

    def __init__(self, _type, stage, start, engage, clear, finish, client_num, driver_name, driver_num,
                 _id=None, last_update=None):
        if stage not in Load.ALLOWED_STAGES:
            raise RuntimeError(f'Unknown stage: {stage}')
        if _type not in ['internal', 'external']:
            raise RuntimeError(f'Unknown Load type: {_type}. Accepted only ["internal", "external"]')
        if _id is None:
            random_data = str(random.getrandbits(256)).encode('utf-8')
            _id = _md5.md5(random_data).hexdigest()
        if last_update is None:
            last_update = datetime.datetime.now()
        else:
            last_update = datetime.datetime.strptime(last_update, '%Y-%m-%d %H:%M:%S.%f')

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
        return cls(_type=_dct['type'],
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

    def change_stage(self, new_stage):
        if new_stage not in Load.ALLOWED_STAGES:
            raise AllowedStagesViolation(f'Somebody tried to set stage that are not allowed ({new_stage})')
        self.stage = new_stage
        self.last_update = datetime.datetime.now()
        Loads.instance.save_state_to_file()


class Loads:

    instance = None

    def __init__(self):
        self.loads = list()
        Loads.instance = self

    def add_load(self, load: Load):
        self.loads.append(load)
        self.save_state_to_file()

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

    def save_state_to_file(self):
        _str = json.dumps(self.to_loads_storage(), ensure_ascii=False)
        with open(file=LOADS_NOSQL_LOC, mode='w') as file:
            file.write(_str)

    def expose_to_dict(self):
        _loads = list()
        for load in self.loads:
            _loads.append(load.expose_to_dict())
        return _loads

    def get_active_loads(self):
        _loads = list()
        for load in self.loads:
            if load.stage != 'history':
                _loads.append(load)
        return _loads

    def expose_active_loads(self):
        _loads = list()
        for load in self.loads:
            if load.stage != 'history':
                _loads.append(load.expose_to_dict())
        return _loads

    def get_deleted_loads(self):
        _loads = list()
        for load in self.loads:
            if load.stage == 'history':
                _loads.append(load)
        return _loads

    def get_load_by_id(self, _id):
        for load in self.loads:
            if load.id == _id:
                return load
        raise NoSuchLoadID(f'There is no Loads with ID: {_id} in a memory storage')


class TelegramInterface:

    instance = None

    def __init__(self, webhook_url=None):
        self.bot = telegramapi2.bot
        self.dispatcher = Dispatcher(bot=self.bot, update_queue=Queue(), use_context=True)
        self.chat_id = settings.TELEGRAM_LOADS_CHAT_ID
        self.dialog_context = None
        self.dispatcher.add_handler(CommandHandler(command="start", callback=self.handle_cmd_start))
        self.dispatcher.add_handler(MessageHandler(filters=Filters.text, callback=self.handle_messages))
        self.dispatcher.add_handler(CallbackQueryHandler(callback=self.handle_inline_buttons))

        if webhook_url is None:
            webhook_url = 'https://api.intersmartgroup.com'
        self.own_secret = secrets.token_urlsafe(32)
        self.bot.set_webhook(f'{webhook_url}/webhook-aibot/', secret_token=self.own_secret)

        TelegramInterface.instance = self

    @staticmethod
    def craft_load(_load):

        load = _load.expose_to_dict()

        def craft_stage():
            if load['type'] == 'external':
                stages = {
                    'start': f'''*{load['stages']['start']} ({load['last_update']})*
{load['stages']['engage']}
{load['stages']['clear']}
{load['stages']['finish']}
''',
                    'engage': f'''{load['stages']['start']}
*{load['stages']['engage']} ({load['last_update']})*
{load['stages']['clear']}
{load['stages']['finish']}
''',
                    'drive': f'''{load['stages']['start']}
{load['stages']['engage']}
*Drive ({load['last_update']})*
{load['stages']['clear']}
{load['stages']['finish']}
''',
                    'clear': f'''{load['stages']['start']}
{load['stages']['engage']}
*{load['stages']['clear']} ({load['last_update']})*
{load['stages']['finish']}
''',
                    'finish': f'''{load['stages']['start']}
{load['stages']['engage']}
{load['stages']['clear']}
*{load['stages']['finish']} ({load['last_update']})*
''',
                    'history': f'''{load['stages']['start']}
{load['stages']['engage']}
{load['stages']['clear']}
{load['stages']['finish']}
'''
                }
                return stages[load['stage']]
            elif load['type'] == 'internal':
                stages = {
                    'start': f'''*{load['stages']['start']} ({load['last_update']})*
{load['stages']['finish']}
''',
                    'drive': f'''{load['stages']['start']}
*Drive ({load['last_update']})*
{load['stages']['finish']}
''',
                    'finish': f'''{load['stages']['start']}
*{load['stages']['finish']} ({load['last_update']})*
''',
                    'history': f'''{load['stages']['start']}
{load['stages']['finish']}
'''
                }
                return stages[load['stage']]
            else:
                raise (RuntimeError('Given load type neither internal neither external'))

        craft = f'''{craft_stage()}
{_load.driver['name']}, +{_load.driver['num']}
{load['id'][:4]}...{load['id'][-4:]}
'''

        keyboard = {
            'external': [
                [InlineKeyboardButton("Set Start", callback_data=f'set_start:{_load.id}'),
                 InlineKeyboardButton("Set Engage", callback_data=f'set_engage:{_load.id}'),
                 InlineKeyboardButton("Set Drive", callback_data=f'set_drive:{_load.id}')],
                [InlineKeyboardButton("Set Clear", callback_data=f'set_clear:{_load.id}'),
                 InlineKeyboardButton("Set Finish", callback_data=f'set_finish:{_load.id}'),
                 InlineKeyboardButton("Delete", callback_data=f'delete:{_load.id}')]
            ],
            'internal': [
                [InlineKeyboardButton("Set Start", callback_data=f'set_start:{_load.id}'),
                 InlineKeyboardButton("Set Drive", callback_data=f'set_drive:{_load.id}')],
                [InlineKeyboardButton("Set Finish", callback_data=f'set_finish:{_load.id}'),
                 InlineKeyboardButton("Delete", callback_data=f'delete:{_load.id}')]
            ]
        }
        reply_markup = InlineKeyboardMarkup(keyboard[_load.type])
        return craft, reply_markup

    @staticmethod
    def create_new_load(_str):

        lines = _str.strip().split('\n')
        method, load_type = lines[0].split(':')
        if method != 'new':
            raise RuntimeError()
        if load_type == 'external':
            """ 0 new:external
                1 Кривой Рог
                2 Днепр
                3 Черновцы
                4 Яссы
                5
                6 Козак Григорий
                7 +380501231212
                8 
                9 Client: +380953459607"""
            start = lines[1].strip()
            engage = lines[2].strip()
            clear = lines[3].strip()
            finish = lines[4].strip()
            driver_name = lines[6].strip()
            driver_num = lines[7].strip()
            client_num = lines[9].replace('Client: ', '').strip()

            if not bool(start) \
                    or not bool(engage) \
                    or not bool(clear) \
                    or not bool(finish) \
                    or not bool(driver_name) or not bool(driver_num) \
                    or not bool(client_num):
                raise RuntimeError()

            if '+' not in driver_num or '+' not in client_num:
                raise RuntimeError()

            new_load = Load(_type=load_type, stage='history',
                            start=start, engage=engage, clear=clear, finish=finish,
                            client_num=client_num.replace('+', ''),
                            driver_name=driver_name, driver_num=driver_num.replace('+', ''))

        elif load_type == 'internal':

            start = lines[1].strip()
            finish = lines[2].strip()
            driver_name = lines[4].strip()
            driver_num = lines[5].strip()
            client_num = lines[7].replace('Client: ', '').strip()

            if not bool(start) \
                    or not bool(finish) \
                    or not bool(driver_name) or not bool(driver_num) \
                    or not bool(client_num):
                raise RuntimeError()

            if '+' not in driver_num or '+' not in client_num:
                raise RuntimeError()

            new_load = Load(_type=load_type, stage='history',
                            start=start, engage=None, clear=None, finish=finish,
                            client_num=client_num.replace('+', ''),
                            driver_name=driver_name, driver_num=driver_num.replace('+', ''))
        else:
            raise RuntimeError()

        Loads.instance.add_load(new_load)
        return new_load

    class DialogState(ABC):

        def __init__(self):
            self.iface = TelegramInterface.instance
            self.loads = Loads.instance

        @abstractmethod
        def on_enter(self):
            pass

        @abstractmethod
        def handle_event(self, update):
            pass

    class StandbyState(DialogState):

        def on_enter(self):

            keyboard = [
                ['Show active', 'Show deleted'],
                ['Create new']
            ]
            main_keyboard = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            active_loads = len(Loads.instance.expose_active_loads())
            self.iface.bot.send_message(chat_id=self.iface.chat_id,
                                        text=f'Active loads: {active_loads}',
                                        reply_markup=main_keyboard,
                                        parse_mode='MARKDOWN')

        def enumerate_worker(self, *loads):
            for load in loads:
                _message, reply_markup = self.iface.craft_load(load)
                time.sleep(0.1)
                self.iface.bot.send_message(self.iface.chat_id,
                                            _message,
                                            reply_markup=reply_markup,
                                            parse_mode='MARKDOWN')
            time.sleep(0.1)
            self.iface.bot.send_message(chat_id=self.iface.chat_id,
                                        text=f'Total: {str(len(loads))}',
                                        parse_mode='MARKDOWN')

        def handle_event(self, update):
            message = update.message.text
            if message == 'Show active':
                threading.Thread(target=self.enumerate_worker, args=(self.loads.get_active_loads())).start()
                return self

            elif message == 'Show deleted':
                threading.Thread(target=self.enumerate_worker, args=(self.loads.get_deleted_loads())).start()
                return self

            elif message == 'Create new':
                draft_ext = '''
new:external
Полтава
Черновцы
Яссы
Плопени

Козак Григорий
+380501231212

Client: +380953459607
                '''
                draft_int = '''
new:internal
Днепр
Конотоп

Козак Григорий
+380501231212

Client: +380953459607
                '''
                self.iface.bot.send_message(self.iface.chat_id, 'Copy, edit and send back')
                self.iface.bot.send_message(self.iface.chat_id, draft_int.strip())
                self.iface.bot.send_message(self.iface.chat_id, draft_ext.strip())
                # return CreateLoadState()
                return self
            elif message == 'Craft sms':
                self.iface.bot.send_message(self.iface.chat_id, 'Not implemented')
                return self
            elif message.startswith('new:'):
                try:
                    load = self.iface.create_new_load(message)
                    threading.Thread(target=self.enumerate_worker, args=([load])).start()
                except Exception as e:
                    self.iface.bot.send_message(self.iface.chat_id, 'Try again')
            return self

    class CreateLoadState(DialogState):

        def on_enter(self):
            pass

        def handle_event(self, update):
            pass

    class CraftsmsState(DialogState):

        def on_enter(self):
            pass

        def handle_event(self, update):
            pass

    class DialogContext:
        def __init__(self, state):
            self.state = state
            self.state.on_enter()

        def handle_event(self, update):
            new_state = self.state.handle_event(update)
            if new_state != self.state:
                self.state = new_state
                self.state.on_enter()

    def handle_cmd_start(self, update, context):

        self.dialog_context.state = self.StandbyState()
        self.dialog_context.handle_event(update)

        # keyboard = [
        #     ['Show active', 'Show deleted'],
        #     ['Create new', 'Clear'],
        #     ['Craft sms']
        # ]
        #
        # reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        # update.message.reply_text("Select option:", reply_markup=reply_markup)

    def handle_messages(self, update: Update, context):

        self.dialog_context.handle_event(update)

    def handle_inline_buttons(self, update, context):
        query = update.callback_query
        query.answer()
        data = query.data
        _cmd, _id = data.split(":", 1)
        load = Loads.instance.get_load_by_id(_id)

        if _cmd == 'set_start':
            load.change_stage('start')
            _message, reply_markup = self.craft_load(load)
            query.edit_message_text(text=_message, reply_markup=reply_markup, parse_mode='MARKDOWN')
        elif _cmd == 'set_engage':
            load.change_stage('engage')
            _message, reply_markup = self.craft_load(load)
            query.edit_message_text(text=_message, reply_markup=reply_markup, parse_mode='MARKDOWN')
        elif _cmd == 'set_drive':
            load.change_stage('drive')
            _message, reply_markup = self.craft_load(load)
            query.edit_message_text(text=_message, reply_markup=reply_markup, parse_mode='MARKDOWN')
        elif _cmd == 'set_clear':
            load.change_stage('clear')
            _message, reply_markup = self.craft_load(load)
            query.edit_message_text(text=_message, reply_markup=reply_markup, parse_mode='MARKDOWN')
        elif _cmd == 'set_finish':
            load.change_stage('finish')
            _message, reply_markup = self.craft_load(load)
            query.edit_message_text(text=_message, reply_markup=reply_markup, parse_mode='MARKDOWN')
        elif _cmd == 'delete':
            load.change_stage('history')
            query.edit_message_text(text=f"Deleted")
        else:
            pass

    def catch_webhook(self, _json):

        update = Update.de_json(_json, self.bot)
        self.dispatcher.process_update(update)


def base_input(cls):
    cls.loads_instance.add_load(Load(_type='internal',
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
    cls.loads_instance.add_load(Load(_type='external',
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


def storage_init(cls):
    _str = json.dumps(cls.loads_instance.to_loads_storage(), ensure_ascii=False)
    with open(file=LOADS_NOSQL_LOC, mode='w') as file:
        file.write(_str)


# --- Initialization ---
with open(file=LOADS_NOSQL_LOC, mode='r', encoding='utf8', ) as f:
    contents = f.read()
dct = json.loads(contents)
loads_instance = Loads().from_loads_storage(dct)  # entrypoint

# telegram_interface = TelegramInterface('https://ec5e-194-233-96-196.ngrok-free.app')
telegram_interface = TelegramInterface()
telegram_interface.dialog_context = TelegramInterface.DialogContext(TelegramInterface.StandbyState())
# --- Initialization ---
