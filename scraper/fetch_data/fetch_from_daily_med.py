import csv
import json
import os
import re
import time
import requests
from bs4 import BeautifulSoup
import pandas as pd
import openai
from openai import Client, Completion
from dotenv import load_dotenv

class FetchDailyMed:
    def __init__(self,scraping_logger):
        self.logger = scraping_logger
        
        self.cleaned_data_dir = "scraper/fetch_data/cleaned_data/cleaned_vaFssPharmPrices.csv"
        self.df = pd.read_csv(self.cleaned_data_dir)
        self.particular_column_values = self.df["NDCWithDashes"]
        self.generic_names = self.df["Generic"]
        
        self.base_url = "https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query={}&pagesize=20&page=1"
        self.output_dir = "scraper/fetch_data/records/daily_med"
        os.makedirs(self.output_dir, exist_ok=True)  # Ensure the output directory is created here
        self.init_csv_files()
        load_dotenv()

    def init_csv_files(self):
        # Initialize CSV files and write headers if not already present
        self.packager_file_path = os.path.join(self.output_dir, "packager_data_daily_med.csv")
        self.drug_file_path = os.path.join(self.output_dir, "drug_data_daily_med.csv")

        # Make sure the directory exists before creating files
        os.makedirs(self.output_dir, exist_ok=True)
    
        if os.path.exists(self.packager_file_path):
            os.remove(self.packager_file_path)
            with open(self.packager_file_path, 'w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=["Generic", "NDC Code", "Packager"])
                writer.writeheader()
        else:
            with open(self.packager_file_path, 'w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=["Generic", "NDC Code", "Packager"])
                writer.writeheader()
            
        if os.path.exists(self.drug_file_path):
            os.remove(self.drug_file_path)
            with open(self.drug_file_path, 'w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=["NDC Code", "Manufactured By", "Manufactured For", "Distributed By","Image URLs"])
                writer.writeheader()
        else:
            with open(self.drug_file_path, 'w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=["NDC Code", "Manufactured By", "Manufactured For", "Distributed By","Image URLs"])
                writer.writeheader()
            

    def write_to_csv(self, data, filename):
        path = os.path.join(self.output_dir, filename)
        with open(path, 'a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=data.keys())
            writer.writerow(data)

    def fetch_daily_med(self, url):
        max_retries = 20  
        attempts = 0  
        while attempts < max_retries:
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    return soup
                else:
                    print(f"Failed to fetch data from the URL: {url}. Status Code: {response.status_code}")
                    attempts += 1
                    if attempts < max_retries:
                        print(f"Attempt {attempts} failed, retrying in 5 seconds...")
                        time.sleep(10)  # Wait for 5 seconds before retrying
                    else:
                        print("Maximum retries reached. Aborting.")
                        return None
            except requests.exceptions.RequestException as e:
                print("An error occurred during the request:", e)
                attempts += 1
                if attempts < max_retries:
                    print(f"Attempt {attempts} failed due to a request exception, retrying in 5 seconds...")
                    time.sleep(10)  # Wait for 5 seconds before retrying
                else:
                    print("Maximum retries reached after request exception. Aborting.")
                    return None

    def get_desire_element(self, soup):

        texts = [
            "manufactured by",
            "manufactured for",
            "distributed by",
            "distributed and marketed by",
        ]

        div_element = soup.find("div", id="drug-information")
        if div_element is not None:

            li_elements = div_element.find_all("li")
            for li in li_elements:
                if any(text in str(li.text).lower() for text in texts):
                    return li
        else:
            print('div element with id "drug-information" not found')

    def get_with_gpt(self, prompt):
        api_key = os.getenv('API_KEY')
        print(api_key)
        client = openai.Client(api_key=api_key)
        max_attempts = 5
        base_sleep_seconds = 2  # Base sleep time which will increase exponentially

        for attempt in range(max_attempts):
            try:
                response = client.chat.completions.create(
                    messages=[
                        {"role": "user", "content": prompt},
                    ],
                    model="gpt-3.5-turbo-0125",
                    response_format={"type": "json_object"},
                )
                return response.choices[0].message.content
            except openai.RateLimitError as e:
                sleep_time = base_sleep_seconds * (2 ** attempt)
                print(f"Rate limit exceeded. Retrying in {sleep_time} seconds.\n", e)
                time.sleep(sleep_time)
            except openai.OpenAIError as e:
                print(f"An OpenAI API error occurred: {e}")
                break
        print("Failed to get response after multiple retries.")
        return None

    def extract_information_from_li(self, li_element):
        relevant_keywords = [
            "manufactured by",
            "manufactured for",
            "distributed by",
            "distributed and marketed by",
        ]

        # Find all paragraph elements
        relevant_paragraphs = li_element.find_all("p")

        for i, paragraph in enumerate(relevant_paragraphs):
            text = paragraph.get_text().strip()

            if any(keyword in text.lower() for keyword in relevant_keywords):

                text_fragments = [text]
                for subsequent_paragraph in relevant_paragraphs[i + 1 :]:
                    text_fragments.append(subsequent_paragraph.get_text().strip())

                return " ".join(text_fragments)

        return ""

    def extract_from_response_and_save(self, response, ndc_code):
        # Find the start and end index of the JSON object
        start_index = response.find("{")
        end_index = response.rfind("}") + 1

        json_string = response[start_index:end_index]
        json_dict = json.loads(json_string)

        data = {
            "NDC Code": ndc_code,
            "Manufactured By": "",
            "Manufactured For": "",
            "Distributed By": "",
        }

        for key in data.keys():
            if key in json_dict:
                data[key] = json_dict[key]

        return data
    
    
    def get_images_url(self, soup):
        
        base_url = "https://dailymed.nlm.nih.gov" 
        # Find all <li> elements with class 'img package-photo'
        li_elements = soup.find_all('li', class_='img package-photo')

        # Extract href from <a> tags within those <li> elements
        hrefs = []
        for li in li_elements:
            a_tag = li.find('a', href=True)
            if a_tag:
                # Append base URL to the href to make it a full URL
                full_url = base_url + a_tag['href']
                hrefs.append(full_url)
        return hrefs
        

    def get_and_save_packager_data(self, soup, ndc_code, generic_name):
        packager_tag = soup.select_one('li:-soup-contains("Packager:")')
        if packager_tag:
            manufacturer_info = packager_tag.get_text(separator="\n", strip=True)
            manufacturer_name = manufacturer_info.replace("Packager:", "").strip()
        else:
            manufacturer_name = ""

        data = {
            "Generic": generic_name,
            "NDC Code": ndc_code,
            "Packager": manufacturer_name,
        }
        self.write_to_csv(data,'packager_data_daily_med.csv')
        #self.packager_data_list.append(data)

    def get_and_save_drug_data(self, soup, ndc_code):
        
        print("Searching for NDC code: ", ndc_code)
        
        # Getting images url of the drug
        hrefs = self.get_images_url(soup)
        
        # Convert the list of image URLs to a comma-separated string
        images_list = ", ".join(hrefs)
        
        data = {
        "NDC Code": ndc_code,
        "Manufactured By": "",
        "Manufactured For": "",
        "Distributed By": "",
        "Image URLs": images_list  # Store image URLs as a comma-separated string
        }
        
        
        desire_element = self.get_desire_element(soup)
        if desire_element is not None:
            text = self.extract_information_from_li(desire_element)
            print(text)
            prompt = f'I have extracted the following text:\n{text}\n\nNow, From this text find the complete details of Manufactured By, Manufactured for, and Distributed by if one is not found then place an empty string against this. Just provide one JSON like \n\n\n( "Manufactured By": " ", "Manufactured For": " ","Distributed By": " ")'
            response = self.get_with_gpt(prompt)
            print(response)
            extracted_data  = self.extract_from_response_and_save(response, ndc_code)
            data.update(extracted_data)
            self.write_to_csv(data,'drug_data_daily_med.csv')

    def save_packager_data(self):

        os.makedirs(self.output_dir, exist_ok=True)
        output_path = os.path.join(self.output_dir, "packager_data_daily_med.csv")
        packager_df = pd.DataFrame(self.packager_data_list)
        packager_df.to_csv(output_path, index=False)

    def save_drug_data(self):

        os.makedirs(self.output_dir, exist_ok=True)
        output_path = os.path.join(self.output_dir, "drug_data_daily_med.csv")
        packager_df = pd.DataFrame(self.drug_data_list)
        packager_df.to_csv(output_path, index=False)

    def get_data_from_daily_mad(self):

        self.logger.info("Start fecthing data from daily mad...")
        for value, generic_name in zip(
            self.particular_column_values, self.generic_names
        ):
            url = self.base_url.format(value)
            soup = self.fetch_daily_med(url)

            
            #Saving packager info
            self.get_and_save_packager_data(soup, value, generic_name)

            # save drug info
            self.get_and_save_drug_data(soup, value)
            
            

        # self.save_packager_data()
        # self.save_drug_data()


#Example usage:
# fetcher = FetchDailyMed()
# fetcher.get_data_from_daily_mad()
