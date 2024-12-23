import os
import re
import threading
import pandas as pd
import requests
from selenium import webdriver
from .fetch_from_orange_book import FetchOrangeBook
from .data_wrangling import DataWrangling
from .fetch_from_daily_med import FetchDailyMed
from .fetch_from_sam_gov import FetchSamGov

from .fetch_asph import AsphDrugShortageScraper
from .fetch_access_data import AccessDataShortageScraper
from queue import Queue

class PharmaScraper:
    def __init__(self, logger):
        self.logger = logger
        self.driver = None
        self.raw_file_name = "vaFssPharmPrices.xlsx"
        self.error_queue = Queue()

    def download_file(self, url):
        try:
            if os.path.exists(self.raw_file_name):
                os.remove(self.raw_file_name)
                self.logger.info(f"Existing file '{self.raw_file_name}' deleted.")

            self.logger.info("Downloading new File...")
            response = requests.get(url)
            if response.status_code == 200:
                with open(self.raw_file_name, 'wb') as f:
                    f.write(response.content)
                self.logger.info("File downloaded successfully.")
            else:
                raise Exception("Failed to download the file.")
        except Exception as e:
            self.logger.error(f"Error in download_file: {str(e)}")
            self.error_queue.put(str(e))

    def run(self):
        file_link = "https://www.va.gov/opal/docs/nac/fss/vaFssPharmPrices.xlsx"
        self.download_file(file_link)

        self.data_Wrangler = DataWrangling()
        try:
            self.data_Wrangler.prepare_data(self.raw_file_name)
        except Exception as e:
            self.logger.error(f"Error in prepare_data: {str(e)}")
            self.error_queue.put(str(e))

        
        self.orange_book_scraper = FetchOrangeBook(self.logger)
        self.daily_med_scraper = FetchDailyMed(self.logger)
        self.sam_gov_scraper = FetchSamGov(self.logger)

        self.asph_scraper = AsphDrugShortageScraper(self.logger)
        self.access_data_scraper = AccessDataShortageScraper(self.logger)

        threads = [
            threading.Thread(target=self.thread_wrapper, args=(self.orange_book_scraper.process_csv_file,)),
            threading.Thread(target=self.thread_wrapper, args=(self.daily_med_scraper.get_data_from_daily_mad,)),
            threading.Thread(target=self.thread_wrapper, args=(self.sam_gov_scraper.process_contract_numbers,)),
            threading.Thread(target=self.thread_wrapper, args=(self.asph_scraper.scrape_and_save,)),
            threading.Thread(target=self.thread_wrapper, args=(self.access_data_scraper.scrape_and_save,))
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        if not self.error_queue.empty():
            while not self.error_queue.empty():
                self.logger.error(f"Thread error: {self.error_queue.get()}")
            raise Exception("Errors occurred in some threads. Check the logs for details.")
        else:
            self.logger.info("All threads completed successfully, and all the data has been scraped! ")

    def thread_wrapper(self, target):
        try:
            target()
        except Exception as e:
            self.logger.error(f"Error in thread {threading.current_thread().name}: {str(e)}")
            self.error_queue.put(str(e))
        


        

# if __name__ == "__main__": 
    
#     scraper = PharmaScraper()
#     scraper.run()
    

