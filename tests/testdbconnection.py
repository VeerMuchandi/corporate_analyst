import os
import sqlalchemy
from google.cloud.sql.connector import Connector, IPTypes
import pg8000.dbapi
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize database connection pool globally
db_pool = None


def init_db_pool():
    """Initializes the database connection pool using Cloud SQL Python Connector."""
    global db_pool
    if db_pool is None:
        db_user = os.environ.get("DB_USER")
        db_pass = os.environ.get("DB_PASS")
        db_name = os.environ.get("DB_NAME")
        db_connection_name = os.environ.get("DB_CONNECTION_NAME")  # e.g., project:region:instance

        if not all([db_user, db_pass, db_name, db_connection_name]):
            print(
                "Error: One or more database environment variables are not set (DB_USER, DB_PASS, DB_NAME, DB_CONNECTION_NAME)."
            )
            exit(1)

        def getconn():
            """Creates a connection to the database using the Cloud SQL Python Connector."""
            connector = Connector()
            conn = connector.connect(
                db_connection_name,
                "pg8000",
                user=db_user,
                password=db_pass,
                db=db_name,
            )
            return conn

        pool = sqlalchemy.create_engine(
            "postgresql+pg8000://",  # Use pg8000 in the connection string
            creator=getconn,
            pool_size=5,
            max_overflow=2,
            pool_timeout=30,
            pool_recycle=1800,
        )
        db_pool = pool
        print("Database connection pool initialized using Cloud SQL Connector.")


def get_db_pool():
    """Returns the database connection pool."""
    global db_pool
    if db_pool is None:
        init_db_pool()
    return db_pool


def test_db_connection_and_data_retrieval():
    """Tests the database connection and retrieves data from a table."""
    try:
        db_pool = get_db_pool()
        with db_pool.connect() as db_conn:
            print("Successfully connected to the database.")

            # Test retrieving data from the 'sec_filings' table
            print("\nTesting retrieval from 'sec_filings' table:")
            try:
                result = db_conn.execute(
                    sqlalchemy.text("SELECT * FROM sec_filings LIMIT 1")
                ).fetchone()
                if result:
                    print("Successfully retrieved data from 'sec_filings' table.")
                    print("Sample data:", result)
                else:
                    print("No data found in 'sec_filings' table.")
            except Exception as e:
                print(f"Error retrieving data from 'sec_filings' table: {e}")

            # Test retrieving data from the 'zoominfo_enrichments' table
            print("\nTesting retrieval from 'zoominfo_enrichments' table:")
            try:
                result = db_conn.execute(
                    sqlalchemy.text("SELECT * FROM zoominfo_enrichments LIMIT 1")
                ).fetchone()
                if result:
                    print(
                        "Successfully retrieved data from 'zoominfo_enrichments' table."
                    )
                    print("Sample data:", result)
                else:
                    print("No data found in 'zoominfo_enrichments' table.")
            except Exception as e:
                print(
                    f"Error retrieving data from 'zoominfo_enrichments' table: {e}"
                )

    except Exception as e:
        print(f"Error connecting to the database: {e}")


if __name__ == "__main__":
    # No need to check environment variables individually, load_dotenv() handles it.
    test_db_connection_and_data_retrieval()
