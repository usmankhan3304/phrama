from collections import defaultdict
import csv
import json
import logging
import time
from bs4 import BeautifulSoup
from django.db import transaction
from django.db.models import F
import os
import pandas as pd
import openai
import requests
from scraper.models import FOIAUniqueNDCData, FOIADrugsData, Manufacturer, FOIAStationData
logger = logging.getLogger(__name__)

class FetchFoiaFile:
    def __init__(self):
        self.foia_file_path = os.path.join('scraper', 'fetch_data', 'raw_data', 'FOIA-24-02336-F Response (1).txt')
        self.station_file_path = os.path.join('scraper', 'fetch_data', 'raw_data', 'VA Station ID List.xlsx')
        self.base_url = "https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query={}&pagesize=20&page=1"
        #self.ndc_details = set()
        self.ndc_details = set(FOIAUniqueNDCData.objects.values_list('ndc_code', flat=True))  # Cache existing NDC codes

    
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
            logger.info('div element with id "drug-information" not found')
    
    def extract_from_response_and_save(self, response, ndc_code):
        # Find the start and end index of the JSON object
        start_index = response.find("{")
        end_index = response.rfind("}") + 1

        json_string = response[start_index:end_index]
        json_dict = json.loads(json_string)

        data = {
            "NDC Code": ndc_code,
            "Ingredient": "",
            "Strength": "",
            "Dosage Form": "",
            "Manufactured By": "",
            "Manufactured For": "",
            "Distributed By": "",
        }

        for key in data.keys():
            if key in json_dict:
                data[key] = json_dict[key]

        return data
    
    def get_ndc_drug_data(self, soup, ndc_code, description):
        
        logger.info(f"Searching for NDC code: {ndc_code}")
        desire_element = self.get_desire_element(soup)
        if desire_element is not None:
            text = self.extract_information_from_li(desire_element)
            logger.info(text)
            prompt = f'''
                I have extracted the following text:\n{text}\n\n
                Now, from this text find the complete details of "Manufactured By", "Manufactured for", and "Distributed by". If one is not found, then place an empty string against it.
                Additionally, based on the provided description: \n{description}\n\n, extract the "Medicine"(must goes into the Ingredient) or "Ingredient", "Dosage Form", and "Strength".
                Provide all the information in a single JSON format:

                {{"Ingredient": "", "Dosage Form": "", "Strength": "","Manufactured By": "", "Manufactured For": "", "Distributed By": ""}}
                '''
            response = self.get_with_gpt(prompt)
            logger.info(response)
            data = self.extract_from_response_and_save(response, ndc_code)
            
            return data
            #self.write_to_csv(data,'foia_drug_data.csv')
        else:
            logger.info(f"No desire element found for NDC code: {ndc_code} \n Just Finding the Ingredient, Dosage Form and Strength.")
            prompt = f'''
                I have extracted the following text:\n{'empty'}\n\n
                Now, from this text find the complete details of "Manufactured By", "Manufactured for", and "Distributed by". If one is not found, then place an empty string against it.
                Additionally, based on the provided description: \n{description}\n\n, extract the "Medicine"(must goes into the Ingredient) or "Ingredient", "Dosage Form", and "Strength".
                Provide all the information in a single JSON format:

                {{"Ingredient": "", "Dosage Form": "", "Strength": "","Manufactured By": "", "Manufactured For": "", "Distributed By": ""}}
                '''
            response = self.get_with_gpt(prompt)
            logger.info(response)
            data = self.extract_from_response_and_save(response, ndc_code)
            return data

    
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
                    logger.info(f"Failed to fetch data from the URL: {url}. Status Code: {response.status_code}")
                    attempts += 1
                    if attempts < max_retries:
                        logger.info(f"Attempt {attempts} failed, retrying in 5 seconds...")
                        time.sleep(10)  # Wait for 5 seconds before retrying
                    else:
                        logger.info("Maximum retries reached. Aborting.")
                        return None
            except requests.exceptions.RequestException as e:
                logger.info(f"An error occurred during the request: {e}")
                attempts += 1
                if attempts < max_retries:
                    logger.info(f"Attempt {attempts} failed due to a request exception, retrying in 5 seconds...")
                    time.sleep(10)  # Wait for 5 seconds before retrying
                else:
                    logger.info("Maximum retries reached after request exception. Aborting.")
                    return None
    
    def get_with_gpt(self, prompt):
        api_key = os.getenv('API_KEY')
        client = openai.Client(api_key=api_key)
        max_attempts = 5
        base_sleep_seconds = 2  # Base sleep time which will increase exponentially

        for attempt in range(max_attempts):
            try:
                response = client.chat.completions.create(
                    messages=[
                        {"role": "user", "content": prompt},
                    ],
                    model="gpt-3.5-turbo-1106",
                    response_format={"type": "json_object"},
                )
                # Assuming the response from the model is correctly formatted JSON
                return response.choices[0].message.content
            except openai.RateLimitError as e:
                sleep_time = base_sleep_seconds * (2 ** attempt)
                logger.info(f"Rate limit exceeded. Retrying in {sleep_time} seconds.\n {e}")
                time.sleep(sleep_time)
            except openai.OpenAIError as e:
                logger.info(f"An OpenAI API error occurred: {e}")
                break
            except json.JSONDecodeError as e:
                logger.info(f"Failed to decode JSON from GPT response: {e}")
                break
        logger.info("Failed to get response after multiple retries.")
        return None
    
    def get_or_create_manufacturer(self, name):
        if name:
            manufacturer, _ = Manufacturer.objects.update_or_create(name=name)
            return manufacturer
        return None
    
    def load_and_save_station_data(self):
        print("Getting station file..")
        # Load the Excel file into a DataFrame
        station_df = pd.read_excel(self.station_file_path)
        
        # Clean column names by stripping any leading/trailing whitespace
        station_df.columns = station_df.columns.str.strip()
        
        # Iterate through the DataFrame and save each record in the StationData table
        for _, row in station_df.iterrows():
            station_id = str(row['Station ID']).strip()
            facility_name = str(row['Facility']).strip() if not pd.isna(row['Facility']) else ''
            address = str(row['Address']).strip() if not pd.isna(row['Address']) else ''
            state = str(row['State']).strip() if not pd.isna(row['State']) else ''
            phone = str(row['Phone']).strip() if not pd.isna(row['Phone']) else ''
            
            # Save or update the station data in the database
            FOIAStationData.objects.update_or_create(
                station_id=station_id,
                defaults={
                    'facility_name': facility_name,
                    'address': address,
                    'state': state,
                    'phone': phone
                }
            )

    def insert_foia_drug_data_from_file(self, batch_size=1000):
        fioa_drugs_data_list = []
        update_ndc_drug_data = defaultdict(lambda: {'total_quantity': 0, 'total_spent': 0})
    
        with open(self.foia_file_path, 'r') as infile:
            logger.info("Reading file...")
            for line in infile:
                if line.startswith("Quarterly Risk Share Data"):
                    break
                if line.startswith("McKesson Station Number"):
                    continue

                row = line.strip().split('\t')
                try:
                    mckesson_station_number = row[0].strip()
                    ndc_code = row[1].strip()
                    description = row[2].strip()
                    quantity_purchased = int(row[3].strip())
                    dollars_spent = float(row[4].strip())

                    if not ndc_code:
                        logger.info("Skipping line due to empty NDC code...")
                        continue

                except (IndexError, ValueError) as e:
                    logger.error(f"Skipping line due to error: {e}, Line content: {row[:10]}")
                    continue

                # Update batches for existing NDC data
                update_ndc_drug_data[ndc_code]['total_quantity'] += quantity_purchased
                update_ndc_drug_data[ndc_code]['total_spent'] += dollars_spent
                
                
                # Fetch and create NDC data if it does not already exist
                if ndc_code not in self.ndc_details:
                    url = self.base_url.format(ndc_code)
                    soup = self.fetch_daily_med(url)
                    data = self.get_ndc_drug_data(soup, ndc_code, description)

                    manufacturer_by = self.get_or_create_manufacturer(data["Manufactured By"])
                    manufacturer_for = self.get_or_create_manufacturer(data["Manufactured For"])
                    distributor = self.get_or_create_manufacturer(data["Distributed By"])

                    FOIAUniqueNDCData.objects.update_or_create(
                    ndc_code=ndc_code,
                    defaults={
                        "description": description,
                        "ingredient": data.get("Ingredient"),
                        "dosage_form": data.get("Dosage Form"),
                        "strength": data.get("Strength"),
                        "manufactured_by": manufacturer_by,
                        "manufactured_for": manufacturer_for,
                        "distributed_by": distributor,
                    }
                )
                self.ndc_details.add(ndc_code)  # Update the cache

                # Prepare FOIADrugsData for batch insert
                fioa_drugs_data_list.append(FOIADrugsData(
                    mckesson_station_number=mckesson_station_number,
                    ndc_code=FOIAUniqueNDCData.objects.get(ndc_code=ndc_code),
                    quantity_purchased=quantity_purchased,
                    publishable_dollars_spent=dollars_spent
                ))

                if len(fioa_drugs_data_list) >= batch_size:
                    with transaction.atomic():
                        FOIADrugsData.objects.bulk_create(fioa_drugs_data_list)
                        fioa_drugs_data_list = []
                        self.update_ndc_drug_batches(update_ndc_drug_data)
                        update_ndc_drug_data.clear()

            # Process remaining data in batches
            if fioa_drugs_data_list or update_ndc_drug_data:
                with transaction.atomic():
                    FOIADrugsData.objects.bulk_create(fioa_drugs_data_list)
                    self.update_ndc_drug_batches(update_ndc_drug_data)

    def update_ndc_drug_batches(self, update_data):
        for ndc_code, data in update_data.items():
            FOIAUniqueNDCData.objects.filter(ndc_code=ndc_code).update(
                total_quantity_purchased=F('total_quantity_purchased') + data['total_quantity'],
                total_publishable_dollars_spent=F('total_publishable_dollars_spent') + data['total_spent']
            )

    def run(self):
        """
        Entry method to start the NDC data processing.
        """
        self.load_and_save_station_data()
        self.insert_foia_drug_data_from_file()

