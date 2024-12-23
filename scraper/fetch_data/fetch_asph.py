import os
import requests
from bs4 import BeautifulSoup
import pandas as pd

class AsphDrugShortageScraper:
    def __init__(self,scraping_logger):
        self.logger = scraping_logger
        self.url = "https://www.ashp.org/drug-shortages/current-shortages/drug-shortages-list?page=All"
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        }
        self.output_dir = "scraper/fetch_data/records/drug_shortage"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def scrape_data(self):
        try:
            response = requests.get(self.url, headers=self.headers)
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.content
        except requests.exceptions.RequestException as e:
            print("An error occurred while making the request:", str(e))
            return None
    
    def parse_html(self, content):
        if content:
            try:
                soup = BeautifulSoup(content, 'html.parser')
                table = soup.find('table', class_='table-striped')
                rows = table.find_all('tr')
                data = {
                    'GENERIC NAME': [],
                    'SHORTAGE STATUS': [],
                    'REVISION DATE': [],
                    'CREATED DATE': []
                }
                for row in rows:
                    cells = row.find_all('td')
                    row_data = [cell.get_text(strip=True) for cell in cells]
                    if len(row_data) >= 3:
                        data['GENERIC NAME'].append(row_data[0])
                        data['SHORTAGE STATUS'].append(row_data[1])
                        data['REVISION DATE'].append(row_data[2])
                        data['CREATED DATE'].append(row_data[3])
                return data
            except AttributeError as e:
                print("An error occurred while parsing HTML:", str(e))
                return None
        else:
            return None
    
    def save_to_csv(self, data, filename='asph_drug_shortage.csv'):
        if data:
            try:
                df = pd.DataFrame(data)
                file_path = os.path.join(self.output_dir, filename)
                df.to_csv(file_path, index=False)
                print("Data has been successfully scraped and saved here'{}'.".format(file_path))
            except Exception as e:
                print("An error occurred while saving to CSV:", str(e))
        else:
            print("No data to save.")

    def scrape_and_save(self):
        self.logger.info("Start fecthing data from asph...")
        content = self.scrape_data()
        if content:
            data = self.parse_html(content)
            if data:
                self.save_to_csv(data)
            else:
                print("No data to save due to parsing errors.")
        else:
            print("No content retrieved, cannot proceed.")



