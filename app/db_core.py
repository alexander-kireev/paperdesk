import psycopg2
import os
from dotenv import load_dotenv

# load database
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

class DBCore:
    """ Class for connecting to the database. """
    
    @staticmethod
    def get_connection():
        """ Returns a psycopg2 database connection. """

        if DATABASE_URL:
            database_url = DATABASE_URL.replace(
                "postgres://", "postgresql://", 1
            )
            return psycopg2.connect(database_url)
        
        return psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
