
import mysql.connector
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=settings.DB_HOST,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            port=settings.DB_PORT
        )
        return conn
    except mysql.connector.Error as err:
        logger.error(f"Database connection error: {err}")
        return None
