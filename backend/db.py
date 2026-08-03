import pymysql
from backend.core.config import Config


def get_connection(use_database=True):
    """
    Get a MySQL connection.
    Set use_database=False when creating the database for the first time.
    """
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME if use_database else None,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )
