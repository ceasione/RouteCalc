import os
import hashlib
from datetime import datetime
from pathlib import Path
import traceback
import sqlite3
from app import settings
import app.lib.apis.telegramapi2 as tgapi2
from app.lib.utils.logger import logger
from app.lib.utils.DTOs import RequestDTO, CalculationDTO


SQL_PATH = Path.cwd()/Path('app/lib/utils/sql')


class QueryLogger:

    """
    Database connection class for storing queries and responses
    from Calc for auditing or debugging purposes.

    Intended usage via context manager.

    Schema:
    CREATE TABLE "queries" (
        "date"      TEXT,
        "time"      TEXT,
        "number"    TEXT,
        "query"     TEXT,
        "response"	TEXT
    );
    """

    def __init__(self):
        self.DB_LOCATION = settings.QUERYLOG_DB_LOC
        self.conn = None
        self.cursor = None

    def _ensure_calculation_exists(self):
        with open(SQL_PATH/'create_table_calculation.sql', encoding='utf8') as f:
            script = f.read()
        self.cursor.executescript(script)
        self.conn.commit()

    def __enter__(self):
        self.conn = sqlite3.connect(self.DB_LOCATION)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._ensure_calculation_exists()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if self.conn:
            self.conn.close()
        self.conn = None
        self.cursor = None

    @staticmethod
    def _today() -> str:
        """
        We are agreed that under this database Date are stored as a text in form of this specific pattern
        :return: datetime.now().strftime('%Y-%m-%d')
        """
        return datetime.now().strftime('%Y-%m-%d')

    @staticmethod
    def _now() -> str:
        """
        The same as above
        :return: datetime.now().strftime('%H:%M:%S')
        """
        return datetime.now().strftime('%H:%M:%S')

    INSERT_QUERY = """
        INSERT INTO queries( "date", "time", "number", "query", "response")
        VALUES (?, ?, ?, ?, ?)
    """

    def log_request_response(self, phone_number: str, query: str, response: str) -> None:
        """
        Logs a query and response to the database
        Logs to old 'queries' table
        :param phone_number: (str) phone number formatted as '380501234567'
        :param query: (str) The input query to store
        :param response: (str) The system's response to the query
        :return: None
        """
        if not self.conn or not self.cursor:
            raise RuntimeError("QueryLogger must be used within a context manager")
        try:
            self.cursor.execute(self.INSERT_QUERY, (self._today(),
                                self._now(),
                                phone_number,
                                query,
                                response))
            self.conn.commit()
        except sqlite3.DatabaseError as e:
            logger.error(f'sqlite3.DatabaseError at QueryLogger\n{traceback.format_exc()}')
            tgapi2.send_developer('sqlite3.DatabaseError at QueryLogger', e)

    @staticmethod
    def _generate_random_digest() -> str:
        random_bytes = os.urandom(20)  # 20 random bytes = 160 bits (SHA-1 size)
        return hashlib.sha1(random_bytes).hexdigest()

    def log_calcultaion(self, request_dto: RequestDTO, calculation_dto: CalculationDTO) -> str:
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
            with open(SQL_PATH/'insert_into_calculation.sql', encoding='utf-8') as f:
                script = f.read()

            values = {
                'calculation_id': digest,

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
            }

            self.cursor.execute(script, values)
            self.conn.commit()
            return digest
        except sqlite3.DatabaseError as e:
            logger.error(f'sqlite3.DatabaseError at QueryLogger\n{traceback.format_exc()}')
            tgapi2.send_developer('sqlite3.DatabaseError at QueryLogger', e)
            raise RuntimeError('Cannot produce digest due to DB error') from e


QUERY_LOGGER = QueryLogger()
