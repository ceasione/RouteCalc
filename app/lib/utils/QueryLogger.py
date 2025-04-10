from app.impsettings import settings
import sqlite3
from datetime import datetime
import app.lib.apis.telegramapi2 as tgapi2


"""
CREATE TABLE "queries" (
    "date"      TEXT,
    "time"      TEXT,
    "number"    TEXT,
    "query"     TEXT,
    "response"	TEXT
);"""


def _today():
    now = datetime.now()
    return now.strftime('%Y-%m-%d')


def _now():
    now = datetime.now()
    return now.strftime('%H:%M:%S')


class QueryLogger:

    def __init__(self):

        self.DB_LOCATION = settings.LOG_DB_LOCATION
        self.conn = sqlite3.connect(self.DB_LOCATION, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.c = self.conn.cursor()

    def __del__(self):

        self.conn.close()

    def put_request_safe(self, phone_number, query, response):
        try:
            self.c.execute("""
                        INSERT INTO queries(
                            "date",
                            "time",
                            "number",
                            "query",
                            "response")
                        VALUES (?, ?, ?, ?, ?) 
                        """, (_today(),
                              _now(),
                              phone_number,
                              query,
                              response))
            self.conn.commit()
        except sqlite3.OperationalError as e:
            tgapi2.send_developer('sqlite3.OperationalError at QueryLogger', e)

    def put_request(self, phone_number, query, response):
        self.put_request_safe(phone_number, query, response)

    def get_today_requests_count(self, phone_number):

        self.c.execute("""
            SELECT date, number 
            FROM queries
            WHERE date = ? and number = ?
            """, (_today(), phone_number))
        rows = self.c.fetchall()
        return len(rows)


singleton = QueryLogger()


def query_logger_factory():
    return singleton
