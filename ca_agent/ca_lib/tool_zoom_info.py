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

"""Tool that pulls corporate information from ZoomInfo."""

import datetime
import http
import json
import os
import ssl
from typing import Optional
import logging

import certifi
import requests
import sqlalchemy
from google.cloud.sql.connector import Connector
import pg8000.dbapi
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add a StreamHandler to send log messages to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)  # Set the level for the console handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Initialize global variables
zoom_token_update_time = datetime.datetime.min
zoom_token = None

# Initialize database connection pool globally
db_pool = None


def init_db_pool():
    """Initializes the database connection pool using Cloud SQL Python Connector."""
    global db_pool
    if db_pool is None:
        db_user = os.environ["DB_USER"]
        db_pass = os.environ["DB_PASS"]
        db_name = os.environ["DB_NAME"]
        db_connection_name = os.environ["DB_CONNECTION_NAME"]  # e.g., project:region:instance

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
        logger.info("Database connection pool initialized using Cloud SQL Connector.")


def get_db_pool():
    """Returns the database connection pool."""
    global db_pool
    if db_pool is None:
        init_db_pool()
    return db_pool


def get_token():
    """Retrieves an access token from ZoomInfo using username and password."""
    global zoom_token_update_time
    global zoom_token
    username = os.environ.get("ZOOMINFO_USERNAME")
    password = os.environ.get("ZOOMINFO_PASSWORD")

    context = ssl.create_default_context(cafile=certifi.where())

    minutes = (
        datetime.datetime.now() - zoom_token_update_time
    ).total_seconds() / 60
    conn = http.client.HTTPSConnection("api.zoominfo.com", context=context)

    if zoom_token is None or zoom_token == "" or minutes > 55:
        logger.info("Refreshing zoominfo jwt token.")
        payload = json.dumps({"username": username, "password": password})
        headers = {"Content-Type": "application/json"}
        conn.request("POST", "/authenticate", payload, headers)
        res = conn.getresponse()
        auth = res.read()
        # set the token and update time
        try:
            zoom_token = json.loads(auth)["jwt"]
            zoom_token_update_time = datetime.datetime.now()
            logger.info("Token update was a success. Resetting token and time.")
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error decoding JSON or missing key: {e}")
            logger.error(f"Response content: {auth}")
            zoom_token = None  # Reset to none if there's an error
            return None

    return zoom_token


def search_companies(access_token, company_name):
    """Searches for companies by name."""
    endpoint = "/search/company"
    base_url = "https://api.zoominfo.com"  # Or your region specific base url
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    params = {"name": company_name}  # Parameters to pass to the api

    try:
        response = requests.get(
            f"{base_url}{endpoint}", headers=headers, params=params
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"Error during API call: {e}")
        return None


def enrich_company(company_domain: str, ticker: str) -> Optional[str]:
    """Enriches company data from ZoomInfo.

    Args:
        company_domain: Domain name of the company such as google.com
        ticker: The ticker symbol of the company

    Returns:
        Enriched information about the company from ZoomInfo in JSON format as a string or None if an error occurs
    """
    # Check if ZoomInfo API calls are enabled
    if os.environ.get("ENABLE_ZOOMINFO_API_CALLS", "True").lower() != "true":
        logger.info("ZoomInfo API calls are disabled. Using only database data.")

    logger.debug(f"enrich_company called with company_domain: {company_domain}, ticker: {ticker}")
    db_pool = get_db_pool()
    with db_pool.connect() as db_conn:
        # Check if the report already exists in the database
        result = db_conn.execute(
            sqlalchemy.text(
                "SELECT company_enrichment_data, last_update_date FROM zoominfo_enrichments WHERE ticker = :ticker"
            ),
            {"ticker": ticker},
        ).fetchone()

        if result:
            company_enrichment_data, last_update_date = result
            if (
                last_update_date
                and datetime.date.today() - last_update_date
                < datetime.timedelta(days=30)
            ):
                logger.info(
                    f"Enrichment data for company ticker '{ticker}' found in the database and is recent."
                )
                return company_enrichment_data  # Return the company_enrichment_data from the database
            elif os.environ.get("ENABLE_ZOOMINFO_API_CALLS", "True").lower() != "true":
                logger.info(
                    f"Enrichment data for company ticker '{ticker}' found in the database but ZoomInfo API calls are disabled."
                )
                return company_enrichment_data
            else:
                logger.info(
                    f"Enrichment data for company ticker '{ticker}' found in the database but is older than 30 days. Refreshing..."
                )
                # Delete the old record
                db_conn.execute(
                    sqlalchemy.text(
                        "DELETE FROM zoominfo_enrichments WHERE ticker = :ticker"
                    ),
                    {"ticker": ticker},
                )
                db_conn.commit()

        # If not in the database or the report is too old, download and process the report
        access_token = get_token()

        # Check if ZoomInfo API calls are enabled
        if os.environ.get("ENABLE_ZOOMINFO_API_CALLS", "True").lower() != "true":
            return None

        if access_token is None:
            logger.error("Could not get access token")
            return None
        context = ssl.create_default_context(cafile=certifi.where())
        conn = http.client.HTTPSConnection("api.zoominfo.com", context=context)
        if company_domain and len(company_domain) > 3:
            company_filter = {"companyWebsite": f"http://www.{company_domain}"}
        else:
            logger.error("Must provide either company_domain")
            return None

        payload = json.dumps({
            "matchCompanyInput": [company_filter],
            "outputFields": [
                "id",
                "ticker",
                "name",
                "website",
                "logo",
                "parentId",
                "parentName",
                "SocialMediaUrls",
                "revenue",
                "employeeCount",
                "phone",
                "street",
                "city",
                "state",
                "zipCode",
                "country",
                "metroArea",
                "companyStatus",
                "companyStatusDate",
                "descriptionList",
                "sicCodes",
                "naicsCodes",
                "competitors",
                "ultimateParentId",
                "ultimateParentName",
                "ultimateParentRevenue",
                "ultimateParentEmployees",
                "subUnitCodes",
                "subUnitType",
                "subUnitIndustries",
                "primaryIndustry",
                "industries",
                "alexaRank",
                "metroArea",
                "revenueRange",
                "employeeRange",
                "companyFunding",
                "recentFundingAmount",
                "recentFundingDate",
                "totalFundingAmount",
                "businessModel",
                "departmentBudgets",
                "employeeCountByDepartment",
            ],
        })
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }
        conn.request("POST", "/enrich/company", payload, headers)
        res = conn.getresponse()
        data = res.read()
        try:
            company_enrichment_data = json.loads(data.decode("utf-8"))
            # Log the response for debugging
            logger.debug(f"ZoomInfo API Response: {company_enrichment_data}")

            # Safely extract ticker
            api_ticker = None
            if company_enrichment_data and "data" in company_enrichment_data and isinstance(company_enrichment_data["data"], list):
                if len(company_enrichment_data["data"]) > 0:
                    first_data_item = company_enrichment_data["data"][0]
                    if isinstance(first_data_item, dict) and "ticker" in first_data_item:
                        api_ticker = first_data_item["ticker"]
                else:
                    logger.warning("Warning: 'data' list is empty in ZoomInfo response.")
            elif company_enrichment_data and "data" in company_enrichment_data and not isinstance(company_enrichment_data["data"], list):
                logger.warning("Warning: 'data' is not a list in ZoomInfo response.")
            elif company_enrichment_data and "data" not in company_enrichment_data:
                logger.warning("Warning: 'data' key is missing in ZoomInfo response.")
            else:
                logger.warning("Warning: Unexpected ZoomInfo response format.")
            
            # Use the ticker passed as parameter if the api_ticker is not available
            if not api_ticker:
                api_ticker = ticker

            last_update_date = datetime.date.today()
            db_conn.execute(
                sqlalchemy.text(
                    "INSERT INTO zoominfo_enrichments (ticker, company_domain, company_enrichment_data, last_update_date) VALUES (:ticker, :company_domain, :company_enrichment_data, :last_update_date) ON CONFLICT (ticker) DO UPDATE SET company_enrichment_data = :company_enrichment_data, company_domain = :company_domain, last_update_date = :last_update_date"
                ),
                {
                    "ticker": api_ticker,
                    "company_domain": company_domain,
                    "company_enrichment_data": json.dumps(company_enrichment_data),
                    "last_update_date": last_update_date,
                },
            )
            db_conn.commit()
            logger.info(
                f"Enrichment data for company ticker '{api_ticker}' saved to the database."
            )
            return json.dumps(company_enrichment_data)
        except json.JSONDecodeError:
            logger.error("Error: could not convert json from ZoomInfo")
            return "Error: could not convert json from ZoomInfo"
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return f"An unexpected error occurred: {e}"
