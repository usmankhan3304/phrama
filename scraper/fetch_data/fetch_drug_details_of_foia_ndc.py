from collections import defaultdict
import csv
import json
import logging
import time
from django.db import transaction
from django.db.models import F
import os
from bs4 import BeautifulSoup
import openai
import requests
#from scraper.models import FOIAUniqueNDCData
logger = logging.getLogger(__name__)

class FetchFoiaFile:
    
    def __init__(self):
        self.input_file = os.path.join('scraper', 'fetch_data', 'raw_data', 'FOIA-24-02336-F Response (1).txt')
        self.base_url = "https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query={}&pagesize=20&page=1"
        self.output_dir = "scraper/fetch_data/records/Foia_drugs"
        os.makedirs(self.output_dir, exist_ok=True)
        #self.input_file = os.path.join('scraper', 'fetch_data', 'raw_data', 'FOIA-24-02336-F Response (1).txt')
        self.ndc_details = set()
    
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
            print('div element with id "drug-information" not found')
    
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
    
    def get_and_save_drug_data(self, soup, ndc_code,description):
        print("Searching for NDC code: ", ndc_code)
        desire_element = self.get_desire_element(soup)
        if desire_element is not None:
            text = self.extract_information_from_li(desire_element)
            print(text)
            prompt = f'''
                I have extracted the following text:\n{text}\n\n
                Now, from this text find the complete details of "Manufactured By", "Manufactured for", and "Distributed by". If one is not found, then place an empty string against it.
                Additionally, based on the provided description: \n{description}\n\n, extract the "Ingredient", "Dosage Form", and "Strength".
                Provide all the information in a single JSON format:

                {{"Ingredient": "", "Dosage Form": "", "Strength": "","Manufactured By": "", "Manufactured For": "", "Distributed By": ""}}
                '''
            response = self.get_with_gpt(prompt)
            print(response)
            data = self.extract_from_response_and_save(response, ndc_code)
            
            return data
            #self.write_to_csv(data,'foia_drug_data.csv')
        else:
            print("No desire element found for NDC code: ", ndc_code)
    
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
                    model="gpt-4o",
                    response_format={"type": "json_object"},
                )
                # Assuming the response from the model is correctly formatted JSON
                return response.choices[0].message.content
            except openai.RateLimitError as e:
                sleep_time = base_sleep_seconds * (2 ** attempt)
                print(f"Rate limit exceeded. Retrying in {sleep_time} seconds.\n", e)
                time.sleep(sleep_time)
            except openai.OpenAIError as e:
                print(f"An OpenAI API error occurred: {e}")
                break
            except json.JSONDecodeError as e:
                print(f"Failed to decode JSON from GPT response: {e}")
                break
        print("Failed to get response after multiple retries.")
        return None


    def fetch_foia_drug_data(self):
        with open(self.input_file, 'r') as infile:
            for line in infile:
                if line.startswith("Quarterly Risk Share Data"):
                    break
                if line.startswith("McKesson Station Number"):
                    continue
                row = line.strip().split('\t')
                try:
                    ndc_code = row[1].strip()
                    description = row[2].strip()
                    if ndc_code and ndc_code not in self.ndc_details:
                        self.ndc_details.add(ndc_code)
                        url = self.base_url.format(ndc_code)
                        soup = self.fetch_daily_med(url)
                        data = self.get_and_save_drug_data(soup,ndc_code,description)
                        return data
                    else:
                        logger.info(f"Skipping line due to empty or duplicate NDC code {ndc_code}.")
                except (IndexError, ValueError) as e:
                    logger.error(f"Skipping line due to error: {e}, Line content: {row[:10]}")
                    continue
    
    

    def run(self):
        """
        Entry method to start the NDC data processing.
        """
        self.fetch_foia_drug_data()

# Usage
if __name__ == '__main__':
    processor = FetchFoiaFile()
    processor.run()

