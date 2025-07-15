from app import settings
import sqlite3
from datetime import datetime
import app.lib.apis.telegramapi3 as tgapi3
import traceback
from app.lib.utils.logger import logger


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

    def __enter__(self):
        self.conn = sqlite3.connect(self.DB_LOCATION)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
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

    def log_calculation(self, phone_number: str, query: str, response: str) -> None:
        """
        Logs a query and response to the database
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
            tgapi3.tg_interface_manager.get_interface().send_developer('sqlite3.DatabaseError at QueryLogger', e)


QUERY_LOGGER = QueryLogger()
