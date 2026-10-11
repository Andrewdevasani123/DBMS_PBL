import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "blood_bank_db")
LOW_STOCK_THRESHOLD = int(os.getenv("LOW_STOCK_THRESHOLD", 5))

def get_connection():
    """Establish and return a connection to the MySQL database."""
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            autocommit=False
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        raise e

def query_db(query, params=(), one=False):
    """
    Execute a parameterized SELECT query and return results as dictionaries.
    Parameterized queries protect against SQL injection vulnerabilities.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return (rows[0] if rows else None) if one else rows
    finally:
        cursor.close()
        conn.close()

def execute_db(query, params=(), commit=True):
    """
    Execute an INSERT, UPDATE, or DELETE parameterized query.
    Returns the lastrowid or affected rowcount.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if commit:
            conn.commit()
        last_id = cursor.lastrowid
        row_count = cursor.rowcount
        return last_id if last_id else row_count
    except Error as e:
        if commit:
            conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()
