import os
import requests
from bs4 import BeautifulSoup
import pandas as pd

class AccessDataShortageScraper:
    def __init__(self,scraping_logger):
        self.logger = scraping_logger
        self.url = "https://www.accessdata.fda.gov/scripts/drugshortages/default.cfm"
        self.output_dir = "scraper/fetch_data/records/drug_shortage"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def scrape_data(self):
        try:
            response = requests.post(self.url)
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.content
        except requests.exceptions.RequestException as e:
            print("An error occurred while making the request:", str(e))
            return None
    
    def parse_html(self, content):
        if content:
            try:
                soup = BeautifulSoup(content, 'html.parser')
                table = soup.find('table', class_='display')
                generic_names = []
                shortage_status = []
                if table:
                    tbody = table.find('tbody')
                    if tbody:
                        rows = tbody.find_all('tr')
                        for row in rows:
                            columns = row.find_all('td')
                            if len(columns) >= 2:
                                generic_names.append(columns[0].get_text(strip=True))
                                shortage_status.append(columns[1].get_text(strip=True))
                return {'GENERIC NAME': generic_names, 'SHORTAGE STATUS': shortage_status}
            except AttributeError as e:
                print("An error occurred while parsing HTML:", str(e))
                return None
        else:
            return None
    
    def save_to_csv(self, data, filename='access_data_drug_shortage.csv'):
        if data:
            try:
                df = pd.DataFrame(data)
                file_path = os.path.join(self.output_dir, filename)
                df.to_csv(file_path , index=False)
                print("Data has been successfully scraped and saved to '{}'.".format(file_path))
            except Exception as e:
                print("An error occurred while saving to CSV:", str(e))
        else:
            print("No data to save.")

    def scrape_and_save(self):
        self.logger.info("Start fecthing data from access...")
        content = self.scrape_data()
        if content:
            data = self.parse_html(content)
            if data:
                self.save_to_csv(data)
            else:
                print("No data to save due to parsing errors.")
        else:
            print("No content retrieved, cannot proceed.")

# Example usage

