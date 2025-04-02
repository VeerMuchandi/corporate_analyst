import os
import unittest
from unittest.mock import patch
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import the modules you want to test
from sec10ktool import get_10k_report_link, download_sec_filing
from zoominfotool import enrich_company


class TestSec10kTool(unittest.TestCase):
    # No need for setUpClass to initialize the database pool here

    def test_get_10k_report_link(self):
        """Test the get_10k_report_link function."""
        # Test with a valid ticker
        ticker = "GOOG"
        url, date = get_10k_report_link(ticker)
        self.assertIsNotNone(url)
        self.assertIsNotNone(date)
        print(f"Test get_10k_report_link with {ticker}: URL: {url}, Date: {date}")

        # Test with an invalid ticker
        ticker = "INVALID_TICKER"
        url, date = get_10k_report_link(ticker)
        self.assertIsNone(url)
        self.assertIsNone(date)
        print(f"Test get_10k_report_link with {ticker}: URL: {url}, Date: {date}")

    def test_download_sec_filing(self):
        """Test the download_sec_filing function."""
        # Test with a valid URL (you might need to update this URL)
        ticker = "GOOG"
        url, _ = get_10k_report_link(ticker)
        if url:
            text = download_sec_filing(url, ticker)
            self.assertIsNotNone(text)
            self.assertIn("Google", text)
            print(f"Test download_sec_filing with {url}: Text length: {len(text)}")
        else:
            self.fail("Could not get a valid URL for testing download_sec_filing")

        # Turned this off as it is hitting API
        # Test with an invalid URL
        # invalid_url = "https://invalid.url"
        # text = download_sec_filing(invalid_url, ticker)
        # self.assertIsNone(text)
        # print(f"Test download_sec_filing with {invalid_url}: Text: {text}")


class TestZoomInfoTool(unittest.TestCase):
    # No need for setUpClass to initialize the database pool here

    def test_enrich_company(self):
        """Test the enrich_company function."""
        # Test with a valid company domain and ticker
        company_domain = "google.com"
        ticker = "GOOG"
        enriched_data = enrich_company(company_domain, ticker)
        self.assertIsNotNone(enriched_data)
        self.assertIn("Alphabet", enriched_data)
        print(f"Test enrich_company with {company_domain} and {ticker}: Data length: {len(enriched_data)}")

        # Turned this off as it is hitting API
        # Test with an invalid company domain
        # company_domain = "invalid.domain"
        # ticker = "INVALID"
        # enriched_data = enrich_company(company_domain, ticker)
        # self.assertIsNotNone(enriched_data)
        # print(f"Test enrich_company with {company_domain} and {ticker}: Data: {enriched_data}")


if __name__ == "__main__":
    unittest.main()
