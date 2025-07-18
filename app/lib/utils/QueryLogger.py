import os
import hashlib
from datetime import datetime
from pathlib import Path
import app.lib.apis.telegramapi3 as tgapi3
import traceback
from typing import Optional, Tuple, Iterator
import sqlite3
from app import settings
from app.lib.utils.logger import logger
from app.lib.utils import compositor
from app.lib.utils.DTOs import RequestDTO, CalculationDTO
from app.lib.calc.place import Place
from app.lib.calc.loadables.vehicles import VEHICLES


SQL_PATH = Path.cwd()/Path('app/lib/utils/sql')
STRF_DATE = '%Y-%m-%d'
STRF_TIME = '%H-%M-%S'
STRF_DATETIME = '%Y-%m-%d %H-%M-%S'


class QueryLogger:

    """
    Database connection class for storing queries and responses
    from Calc for auditing or debugging purposes.

    Intended usage via context manager.
    """

    def __init__(self, db_loc: str = ':memory:'):
        self.DB_LOCATION = db_loc
        self.conn = None
        self.cursor = None

    def _ensure_queries_exists(self):
        with open(SQL_PATH/'queries_create_table.sql', encoding='utf8') as f:
            script = f.read()
        self.cursor.executescript(script)
        self.conn.commit()

    def _ensure_calculation_exists(self):
        with open(SQL_PATH/'calculation_create_table.sql', encoding='utf8') as f:
            script = f.read()
        self.cursor.executescript(script)
        self.conn.commit()

    def _ensure_tg_message_exists(self):
        with open(SQL_PATH/'tg_message_create_table.sql', encoding='utf8') as f:
            script = f.read()
        self.cursor.executescript(script)
        self.conn.commit()

    def _ensure_sample_exists(self):
        with open(SQL_PATH/'sample_create_table.sql', encoding='utf8') as f:
            script = f.read()
        self.cursor.executescript(script)
        self.conn.commit()

    def __enter__(self):
        self.conn = sqlite3.connect(self.DB_LOCATION)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._ensure_queries_exists()
        self._ensure_calculation_exists()
        self._ensure_tg_message_exists()
        self._ensure_sample_exists()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if self.conn:
            self.conn.close()
        self.conn = None
        self.cursor = None

    @staticmethod
    def _format_date(dt: datetime) -> str:
        return dt.strftime(STRF_DATE)

    @staticmethod
    def _format_time(dt: datetime) -> str:
        return dt.strftime(STRF_TIME)

    @staticmethod
    def _format_datetime(dt: datetime) -> str:
        return dt.strftime(STRF_DATETIME)

    INSERT_QUERY = """
        INSERT INTO queries( "date", "time", "number", "query", "response")
        VALUES (?, ?, ?, ?, ?)
    """

    def log_request_response(
        self, 
        query: str, 
        response: str, 
        phone_number: Optional[str]
    ) -> None:
        """
        Logs a query and response to the database
        Logs to old 'queries' table
        :param phone_number: (str) phone number formatted as '380501234567'
        :param query: (str) The input query to store
        :param response: (str) The system's response to the query
        :return: None
        """
        now = datetime.now()
        if not self.conn or not self.cursor:
            raise RuntimeError('QueryLogger must be used within a context manager')
        try:
            self.cursor.execute(self.INSERT_QUERY, (self._format_date(now),
                                self._format_time(now),
                                phone_number,
                                query,
                                response))
            self.conn.commit()
        except sqlite3.DatabaseError as e:
            logger.error(f'sqlite3.DatabaseError at QueryLogger\n{traceback.format_exc()}')
            tgapi3.tg_interface_manager.get_interface().send_developer('sqlite3.DatabaseError at QueryLogger', e)

    @staticmethod
    def _generate_random_digest() -> str:
        random_bytes = os.urandom(20)  # 20 random bytes = 160 bits (SHA-1 size)
        return hashlib.sha1(random_bytes).hexdigest()

    def log_calculation(self, request_dto: RequestDTO, calculation_dto: CalculationDTO) -> str:
        """
        Inserts data from the request_dto and calculation_dto to NEW table 'calculation'
        Returns a unique digest by which a record can be extracted from the database
        :param request_dto: RequestDTO instance
        :param calculation_dto: CalculationDTO instance
        :return: str 40 chars long
        """
        if not self.conn or not self.cursor:
            raise RuntimeError('QueryLogger must be used within a context manager')
        digest = self._generate_random_digest()
        try:
            with open(SQL_PATH/'calculation_insert_into.sql', encoding='utf-8') as f:
                script = f.read()

            values = {
                'calculation_id': digest,

                'created_at': self._format_datetime(datetime.now()),
                'edited_at': None,
                'tg_msg_id': None,

                # RequestDTO
                'request_intent': request_dto.intent,
                'request_vehicle': request_dto.vehicle.id,
                'request_phone_num': request_dto.phone_num,
                'request_locale': request_dto.locale,
                'request_url': request_dto.url,
                'request_ip': request_dto.ip,

                'request_orig_lat': request_dto.origin.lat,
                'request_orig_lng': request_dto.origin.lng,
                'request_orig_name': request_dto.origin.name,
                'request_orig_name_long': request_dto.origin.name_long,
                'request_orig_countrycode': request_dto.origin.countrycode,

                'request_dest_lat': request_dto.destination.lat,
                'request_dest_lng': request_dto.destination.lng,
                'request_dest_name': request_dto.destination.name,
                'request_dest_name_long': request_dto.destination.name_long,
                'request_dest_countrycode': request_dto.destination.countrycode,

                # CalculationDTO
                'calculation_place_a_name': calculation_dto.place_a_name,
                'calculation_place_a_name_long': calculation_dto.place_a_name_long,
                'calculation_place_b_name': calculation_dto.place_b_name,
                'calculation_place_b_name_long': calculation_dto.place_b_name_long,
                'calculation_map_link': calculation_dto.map_link,
                'calculation_place_chain': calculation_dto.place_chain,
                'calculation_chain_map_link': calculation_dto.chain_map_link,

                'calculation_distance': calculation_dto.distance_unstr,
                'calculation_transport_id': calculation_dto.transport_id,
                'calculation_transport_name': calculation_dto.transport_name,
                'calculation_transport_capacity': calculation_dto.transport_capacity,

                'calculation_price': calculation_dto.price_unstr,
                'calculation_price_per_ton': calculation_dto.price_per_ton_unstr,
                'calculation_price_per_km': calculation_dto.price_per_km_unstr,
                'calculation_is_price_per_ton': int(calculation_dto.is_price_per_ton),

                'calculation_currency': calculation_dto.currency,
                'calculation_currency_rate': calculation_dto.currency_rate,
                'calculation_pfactor_vehicle': calculation_dto.pfactor_vehicle,
                'calculation_pfactor_departure': calculation_dto.pfactor_departure,
                'calculation_pfactor_arrival': calculation_dto.pfactor_arrival,
                'calculation_pfactor_distance': calculation_dto.pfactor_distance,
                'calculation_locale': calculation_dto.locale,
                'calculation_real_price': calculation_dto.real_price,
                'calculation_starting_depot_id': calculation_dto.starting_depot_id,
                'calculation_ending_depot_id': calculation_dto.ending_depot_id
            }

            self.cursor.execute(script, values)
            self.conn.commit()
            return digest
        except sqlite3.DatabaseError as e:
            logger.error(f'sqlite3.DatabaseError at QueryLogger\n{traceback.format_exc()}')
            tgapi3.tg_interface_manager.get_interface().send_developer('sqlite3.DatabaseError at QueryLogger', e)
            raise RuntimeError('Cannot produce digest due to DB error') from e

    def get_request_dto(self, digest: str) -> Optional[RequestDTO]:
        """
        Constructs a new RequestDTO object from database using digest to lookup or return
        :param digest: 40 char string
        :return: RequestDTO instance or None
        """
        if not self.conn or not self.cursor:
            raise RuntimeError('QueryLogger must be used within a context manager')

        with open(SQL_PATH/'calculation_select_r_from.sql', encoding='utf-8') as f:
            script = f.read()
        self.cursor.execute(script, {'lookup_id': digest})
        row = self.cursor.fetchone()
        if row is None:
            return None
        origin = Place(
            lat=row['request_orig_lat'],
            lng=row['request_orig_lng'],
            name=row['request_orig_name'],
            name_long=row['request_orig_name_long'],
            countrycode=row['request_orig_countrycode'],
        )

        destination = Place(
            lat=row['request_dest_lat'],
            lng=row['request_dest_lng'],
            name=row['request_dest_name'],
            name_long=row['request_dest_name_long'],
            countrycode=row['request_dest_countrycode'],
        )

        return RequestDTO(
            intent=row['request_intent'],
            origin=origin,
            destination=destination,
            vehicle=VEHICLES.get_by_id(row['request_vehicle']),
            phone_num=row['request_phone_num'],
            locale=row['request_locale'],
            url=row['request_url'],
            ip=row['request_ip'],
        )

    def get_calculation_dto(self, digest: str) -> Optional[CalculationDTO]:
        """
        Constructs a new CalculationDTO object from database using digest to lookup or return None
        :param digest: 40 char string
        :return: RequestDTO instance or None
        """
        if not self.conn or not self.cursor:
            raise RuntimeError('QueryLogger must be used within a context manager')

        with open(SQL_PATH/'calculation_select_c_from.sql', encoding='utf-8') as f:
            script = f.read()
        self.cursor.execute(script, {'lookup_id': digest})
        row = self.cursor.fetchone()
        if row is None:
            return None

        return CalculationDTO(
            place_a_name=row["calculation_place_a_name"],
            place_a_name_long=row["calculation_place_a_name_long"],
            place_b_name=row["calculation_place_b_name"],
            place_b_name_long=row["calculation_place_b_name_long"],
            map_link=row["calculation_map_link"],
            place_chain=row["calculation_place_chain"],
            chain_map_link=row["calculation_chain_map_link"],
            distance=str(row["calculation_distance"]),
            distance_unstr=row["calculation_distance"],
            transport_id=row["calculation_transport_id"],
            transport_name=row["calculation_transport_name"],
            transport_capacity=int(row["calculation_transport_capacity"]),
            price=compositor.format_cost(row["calculation_price"]),
            price_unstr=row["calculation_price"],
            currency=row["calculation_currency"],
            currency_rate=row["calculation_currency_rate"],
            price_per_ton=compositor.format_cost(row["calculation_price_per_ton"]),
            price_per_ton_unstr=row["calculation_price_per_ton"],
            price_per_km=compositor.format_cost(row["calculation_price_per_km"]),
            price_per_km_unstr=row["calculation_price_per_km"],
            is_price_per_ton=bool(row["calculation_is_price_per_ton"]),
            pfactor_vehicle=row["calculation_pfactor_vehicle"],
            pfactor_departure=row["calculation_pfactor_departure"],
            pfactor_arrival=row["calculation_pfactor_arrival"],
            pfactor_distance=row["calculation_pfactor_distance"],
            locale=row["calculation_locale"],
            real_price=row["calculation_real_price"],
            starting_depot_id=row["calculation_starting_depot_id"],
            ending_depot_id=row["calculation_ending_depot_id"],
        )

    def log_tg_message(self,
                       chat_id: int,
                       message_id: int,
                       calculation_id: str,
                       msg_body: str) -> None:
        """
        Store a message to the database. Returns None if inserting OK.
        :param chat_id: int, Telegram chat ID.
        :param message_id: int, Telegram message ID.
        :param calculation_id: str, 40 char sha1 hex digest, foreign key
        :param msg_body: str, Message text
        :return: None if inserting OK
        :raises: RuntimeError if inserting failed
        """
        try:
            with open(SQL_PATH / 'tg_message_insert_into.sql', encoding='utf-8') as f:
                sql = f.read()
            self.cursor.execute(sql, {
                'chat_id': chat_id,
                'message_id' : message_id,
                'calculation_id' : calculation_id,
                'message_body': msg_body,
            })
            self.conn.commit()
            return None
        except sqlite3.DatabaseError as e:
            logger.error(f'sqlite3.DatabaseError at QueryLogger\n{traceback.format_exc()}')
            tgapi3.tg_interface_manager.get_interface().send_developer('sqlite3.DatabaseError at QueryLogger', e)
            raise RuntimeError('Cannot write to the database') from e

    def get_tg_message(self, chat_id: int, message_id: int) -> Optional[tuple[str, str]]:
        """
        Retrieve a message from the database by chat_id and message_id.
        :param chat_id: int, Telegram chat ID.
        :param message_id: int, Telegram message ID.
        :return: Tuple (calculation_id, message_body) if found, else None.
        :raises: RuntimeError if query fails
        """
        try:
            with open(SQL_PATH / 'tg_message_select_one.sql', encoding='utf-8') as f:
                sql = f.read()
            self.cursor.execute(sql, {
                'chat_id': chat_id,
                'message_id': message_id
            })
            result = self.cursor.fetchone()
            return result['calculation_id'], result['message_body'] if result else None
        except sqlite3.DatabaseError as e:
            logger.error(f'sqlite3.DatabaseError at QueryLogger\n{traceback.format_exc()}')
            tgapi3.tg_interface_manager.get_interface().send_developer('sqlite3.DatabaseError at QueryLogger', e)
            raise RuntimeError('Cannot read from the database') from e

    def sample_upsert(self, calculation_id: str, desired_value: float) -> None:
        """
        Inserts a sample to the database. Returns None if inserting OK.
        As calculation_id has UNIQUE constraint, method will update existing sample
        if it already exists.
        :param calculation_id: str, 40 char sha1 hex digest, foreign key
        :param desired_value: float, the model expected output value
        :return: returns None if inserting OK
        """
        with open(SQL_PATH/'sample_upsert.sql', encoding='utf-8') as f:
            script = f.read()
        self.cursor.execute(script, {
            'calculation_id': calculation_id,
            'desired_value': desired_value,
        })
        self.conn.commit()

    def select_samples(self) -> Iterator[Tuple[int, int, int, float]]:
        with open(SQL_PATH / 'sample_select_finetune_batch.sql', encoding='utf-8') as f:
            sql = f.read()
        self.cursor.execute(sql)

        for row in self.cursor.fetchall():
            yield int(row['calculation_starting_depot_id']), \
                  int(row['calculation_ending_depot_id']), \
                  int(row['calculation_transport_id']), \
                  float(row['desired_value'])


QUERY_LOGGER = QueryLogger(db_loc=settings.QUERYLOG_DB_LOC)
