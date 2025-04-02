# Copyright 2025 Google, LLC
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     https://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tool that downloads 10k report for a corporation."""

import os
import PyPDF2
import requests
import sqlalchemy
from typing import Optional
from datetime import date, timedelta
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
        db_user = os.environ["DB_USER"]
        db_pass = os.environ["DB_PASS"]
        db_name = os.environ["DB_NAME"]
        db_connection_name = os.environ[
            "DB_CONNECTION_NAME"
        ]  # e.g., project:region:instance

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


def get_10k_report_link(ticker: str) -> Optional[str]:
    """Downloads a 10-K report from the SEC API or retrieves it from the database.

    Args:
        ticker: The company's ticker symbol

    Returns:
        The URL for the 10-K report (or None if not found).
    """
    # Check if SEC API calls are enabled
    if os.environ.get("ENABLE_SEC_API_CALLS", "True").lower() != "true":
        print("SEC API calls are disabled. Using only database data.")

    db_pool = get_db_pool()
    with db_pool.connect() as db_conn:
        # Check if the report already exists in the database
        result = db_conn.execute(
            sqlalchemy.text(
                "SELECT url, date_of_report FROM sec_filings WHERE ticker = :ticker ORDER BY date_of_report DESC"
            ),
            {"ticker": ticker},
        ).fetchone()

        if result:
            url, date_of_report = result
            if date_of_report and date.today() - date_of_report < timedelta(days=90):
                print(
                    f"Report for ticker '{ticker}' found in the database and is recent."
                )
                return url
            elif os.environ.get("ENABLE_SEC_API_CALLS", "True").lower() != "true":
                print(
                    f"Report for ticker '{ticker}' found in the database but SEC API calls are disabled."
                )
                return url
        else:
            print(f"No report found for ticker '{ticker}' in the database.")

        # If not in the database or the report is too old, download and process the report
        # Check if SEC API calls are enabled
        if os.environ.get("ENABLE_SEC_API_CALLS", "True").lower() != "true":
            return None

        api_key = os.environ.get("SEC_API_KEY")
        url = f"https://api.sec-api.io?token={api_key}"

        payload = {
            "query": f'ticker:({ticker}) AND formType:"10-K"',
            "from": "0",
            "size": "1",
            "sort": [{"filedAt": {"order": "desc"}}],
        }

        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            link_to_filing_details, date_of_report = extract_link_to_filing_details(
                response.json()
            )
            return link_to_filing_details

        except requests.exceptions.RequestException as e:
            print(f"Error during API call: {e}")
            return None
        except AttributeError:
            print("No response received from the API.")
            return None


def extract_link_to_filing_details(report_data):
    """Extracts the link to the filing details from the 10-K report data.

    Args:
        report_data: The data returned from the SEC API for the 10-K report.

    Returns:
        A tuple containing:
            - The link to the filing details (or None if not found).
            - The date of the report (or None if not found).
    """
    if report_data and report_data.get("total"):
        filings = report_data.get("filings", [])
        if filings:
            filing_details_link = filings[0].get("linkToFilingDetails")
            if filing_details_link and filings[0].get("filedAt"):
                date_of_report = date.fromisoformat(filings[0].get("filedAt")[:10])
                return filing_details_link, date_of_report
            elif filing_details_link:
                return filing_details_link, None
            else:
                print("linkToFilingDetails not found in the response.")
        else:
            print("No filings found in the response.")
    else:
        print("No 10-K reports found within the specified criteria.")
    return None, None


def download_sec_filing(url: str, ticker: str) -> Optional[str]:
    """Downloads a SEC filing from the provided URL or retrieves it from the database.

    Args:
        url: The URL of the SEC filing.
        ticker: The company's ticker symbol.

    Returns:
        The extracted text from the downloaded SEC filing (or from the database),
        or None if there's an error.
    """
    # Check if SEC API calls are enabled
    if os.environ.get("ENABLE_SEC_API_CALLS", "True").lower() != "true":
        print("SEC API calls are disabled. Using only database data.")

    db_pool = get_db_pool()
    with db_pool.connect() as db_conn:
        # Check if the report already exists in the database
        result = db_conn.execute(
            sqlalchemy.text("SELECT text_report FROM sec_filings WHERE url = :url"),
            {"url": url},
        ).fetchone()

        if result:
            print(f"Report for URL '{url}' found in the database.")
            return result[0]  # Return the text_report from the database

        # Check if SEC API calls are enabled
        if os.environ.get("ENABLE_SEC_API_CALLS", "True").lower() != "true":
            return None

        # If not in the database, download and process the report
        api_key = os.environ.get("SEC_API_KEY")
        download_url = (
            f"https://api.sec-api.io/filing-reader?token={api_key}&url={url}"
        )

        try:
            response = requests.get(download_url, stream=True)
            response.raise_for_status()  # Raise an exception for bad status codes

            if response.headers["Content-Type"] == "application/pdf":
                filename = f"{ticker}_10k.pdf"
                with open(filename, "wb") as pdf_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        pdf_file.write(chunk)
                print(f"File '{filename}' downloaded successfully.")
                text_report = extract_text_from_pdf(filename)
                os.remove(filename)

                # Save the report to the database
                date_of_download = date.today()
                link_to_filing_details, date_of_report = get_10k_report_link(ticker)
                if not link_to_filing_details:
                    link_to_filing_details = url
                db_conn.execute(
                    sqlalchemy.text(
                        "INSERT INTO sec_filings (url, text_report, ticker, date_of_report, date_of_download) VALUES (:url, :text_report, :ticker, :date_of_report, :date_of_download) ON CONFLICT (url) DO UPDATE SET text_report = :text_report, ticker = :ticker, date_of_report = :date_of_report, date_of_download = :date_of_download"
                    ),
                    {
                        "url": link_to_filing_details,
                        "text_report": text_report,
                        "ticker": ticker,
                        "date_of_report": date_of_report,
                        "date_of_download": date_of_download,
                    },
                )
                db_conn.commit()
                print(f"Report for URL '{url}' saved to the database.")
                return text_report
            else:
                print(
                    "The file at the given URL is not a PDF. Content-Type:"
                    f" {response.headers['Content-Type']}"
                )
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error downloading file: {e}")
            return None
        except Exception as e:
            print(f"Error saving or retrieving report from database: {e}")
            return None


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts text from a PDF file.

    Args:
        pdf_path: The path to the PDF file.

    Returns:
        The extracted text from the PDF file or None if there's an error.
    """
    try:
        with open(pdf_path, "rb") as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
            return text
    except FileNotFoundError:
        print(f"Error: PDF file not found at '{pdf_path}'")
        return None
    except PyPDF2.errors.PdfReadError:
        print(f"Error: Could not read PDF file at '{pdf_path}'")
        return None
