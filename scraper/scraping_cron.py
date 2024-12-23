#!/bin/bash

import requests
import logging
import os
from dotenv import load_dotenv


scraping_logger = logging.getLogger('scraping')
logger = logging.getLogger(__name__)

dotenv_path = '/home/Davincigovdata/pharma_scrape/.env'
load_dotenv(dotenv_path)

logger.info(dotenv_path)

LOGIN_URL = "https://portal.davincigovdata.com/api/auth/login/email/"
API_URL = "https://portal.davincigovdata.com/api/scraper/start/scraping/"
USERNAME = os.environ.get("USER_EMAIL")
PASSWORD = os.environ.get("USER_PASSWORD")

def get_jwt_token():
    """
    Authenticate and obtain a JWT token using login credentials.
    """
    login_data = {
        "email": USERNAME,
        "password": PASSWORD
    }
    
    logger.info(dotenv_path)

    try:
        logging.info(f"Username: {USERNAME}")
        logging.info(f"Password: {PASSWORD}")
        response = requests.post(LOGIN_URL, json=login_data)
        logging.info(f"Login response status code: {response.status_code}")
        logging.info(f"Login response content: {response.text}")
        response.raise_for_status()

        # Parse the JSON response
        json_response = response.json()

        # Check if the login was successful and a token was returned
        if json_response.get("success") and "data" in json_response and "token" in json_response["data"]:
            token = json_response["data"]["token"]
            logging.info("Login successful, JWT token obtained.")
            return token
        else:
            logging.error("Login failed or token not found in response.")
            return None

    except requests.RequestException as e:
        logging.error(f"Error obtaining JWT token: {e}")
        return None

def call_pharma_scraper_api(token):
    headers = {
        "Authorization": f"token {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(API_URL, headers=headers)
        response.raise_for_status()
        logging.info("Pharma scraper API call successful.")
        logging.info(f"Response: {response.json()}")
    except requests.RequestException as e:
        logging.error(f"Error calling Pharma scraper API: {e}")
        logging.error(f"Response content: {response.text}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    token = get_jwt_token()
    if token:
        call_pharma_scraper_api(token)
        logging.error("Successfully obtained JWT token, proceeding with scraping...")
    else:
        logging.error("Failed to obtain JWT token, cannot proceed with API call.")
