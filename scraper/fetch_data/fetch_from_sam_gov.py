import csv
import time
from urllib.parse import unquote
import os
import re
import shutil
import tempfile
import uuid
from docx import Document
import requests
from bs4 import BeautifulSoup
import pandas as pd
import fitz
from .data_wrangling import DataWrangling


class FetchSamGov:
    def __init__(self,scraping_logger):
        self.logger = scraping_logger
        self.headers = {"content-type": "application/x-www-form-urlencoded"}
        self.cached_dataframes = {}
        self.url = "https://sam.gov/api/prod/sgs/v1/search/?random=1711435940961&index=_all&page=0&mode=search&sort=-modifiedDate&size=25&mfe=true&q={}&qMode=ALL"
        self.cleaned_data_dir = "scraper/fetch_data/cleaned_data/cleaned_vaFssPharmPrices.csv"
        self.payload = {}
        self.headers = {}

        self.fetched_data = None
        self.data_wrangler = DataWrangling()
        
        self.fetched_data_cache= {}
        self.output_dir = "scraper/fetch_data/records/sam_gov"

    def get_data_from_file_doc(self, file_name):
        self.logger.info(f"Extracting data from DOCX file: {file_name}")
        try:
            doc = Document(file_name)
            data = []

            for table in doc.tables:
                if "ESTIMATED ANNUAL REQUIREMENTS BY AGENCY" in table.cell(0, 0).text:
                    is_header_row = True
                    for row in table.rows:
                        if is_header_row:
                            is_header_row = False
                            continue  # Skip the header row

                        row_data = []
                        for cell in row.cells:
                            row_data.append(cell.text)
                        data.append(row_data)

            # Create DataFrame without header
            df = pd.DataFrame(data)

            if not df.empty:
                self.logger.info(f"Data extracted successfully from DOCX: {file_name}")
                # Set the first row as the header
                new_header = df.iloc[0]
                df = df[1:]
                df.columns = new_header

                # Dynamically identify column name containing "TOTAL EST. ANNUAL USAGE"
                total_usage_col = None
                for col in df.columns:
                    if "TOTAL EST. ANNUAL USAGE" in col:
                        total_usage_col = col
                        break

                if total_usage_col:
                    df["DosageForm"], df["Strength"], df["Route"], df["Ingredient"] = zip(
                        *df["DESCRIPTION"].apply(
                            self.data_wrangler.extract_values_from_generic_column
                        )
                    )

                    # Keep only the columns of interest, ensuring dynamic handling of the total usage column
                    df = df[
                        [
                            total_usage_col,
                            "DosageForm",
                            "Strength",
                            "Route",
                            "Ingredient",
                        ]
                    ]

                    # Rename the dynamically identified 'TOTAL EST. ANNUAL USAGE' column
                    result_df = df.rename(
                        columns={total_usage_col: "Estimated Annual Quantities"}
                    )
                else:
                    result_df = pd.DataFrame()
            else:
                self.logger.warning(f"No data extracted from DOCX: {file_name}")
                result_df = pd.DataFrame()

        except Exception as e:
            self.logger.error(f"Error extracting data from DOCX {file_name}: {str(e)}")
            result_df = pd.DataFrame()

        return result_df


    def get_data_from_pdf(self, file_name):
        self.logger.info(f"Extracting data from PDF file: {file_name}")
        try:
            doc = fitz.open(file_name)
            data = []
            start_extracting = False

            for page in doc:
                text_instances = page.search_for("ESTIMATED ANNUAL REQUIREMENTS BY AGENCY")
                if text_instances:
                    start_extracting = True
                    rect = text_instances[0]
                    bottom_left = fitz.Point(rect.bl.x, rect.bl.y + 1)

                    for text_instance in page.get_text("blocks"):
                        block_rect = fitz.Rect(text_instance[:4])

                        if block_rect.tl.y > bottom_left.y:
                            row_data = text_instance[4].split("\n")
                            if row_data:
                                data.append(row_data)

                if start_extracting:
                    break

            df = pd.DataFrame(data)

            if not df.empty:
                self.logger.info(f"Data extracted successfully from PDF: {file_name}")
                # Process and return the DataFrame as before...
            else:
                self.logger.warning(f"No data extracted from PDF: {file_name}")
                return pd.DataFrame()

        except Exception as e:
            self.logger.error(f"Error extracting data from PDF {file_name}: {str(e)}")
            return pd.DataFrame()

    
    def get_data_from_file_excel(self, file_name):
        self.logger.info(f"Extracting data from Excel file: {file_name}")
        try:
            # Read the Excel file. Assuming the data is in the first sheet, else specify sheet_name
            df = pd.read_excel(file_name, sheet_name=0)

            if not df.empty:
                self.logger.info(f"Data extracted successfully from Excel: {file_name}")
                # Dynamically identify column name containing "TOTAL Estimated ANNUAL"
                total_usage_col = None
                for col in df.columns:
                    if "total estimated annual" in col.lower():
                        total_usage_col = col
                        break

                if total_usage_col:
                    # Assuming 'DESCRIPTION' exists and can be used to extract the following details
                    if 'DESCRIPTION' in df.columns:
                        df["DosageForm"], df["Strength"], df["Route"], df["Ingredient"] = zip(
                            *df["DESCRIPTION"].apply(
                                self.data_wrangler.extract_values_from_generic_column
                            )
                        )

                        # Keep only the columns of interest, ensuring dynamic handling of the total usage column
                        df = df[
                            [
                                total_usage_col,
                                "DosageForm",
                                "Strength",
                                "Route",
                                "Ingredient",
                            ]
                        ]

                        # Rename the dynamically identified 'TOTAL Estimated ANNUAL' column
                        result_df = df.rename(
                            columns={total_usage_col: "Estimated Annual Quantities"}
                        )
                    else:
                        self.logger.warning(f"'DESCRIPTION' column not found in Excel: {file_name}")
                        result_df = pd.DataFrame()
                else:
                    self.logger.warning(f"'TOTAL Estimated ANNUAL' column not found in Excel: {file_name}")
                    result_df = pd.DataFrame()
            else:
                self.logger.warning(f"No data extracted from Excel: {file_name}")
                result_df = pd.DataFrame()

        except Exception as e:
            self.logger.error(f"Error extracting data from Excel {file_name}: {str(e)}")
            result_df = pd.DataFrame()

        return result_df


    def process_file(self, file_path):
        self.logger.info(f"Processing file: {file_path}")
        
        result_df = pd.DataFrame()  # Default to an empty DataFrame
        
        try:
            if file_path.endswith(".pdf"):
                result_df = self.get_data_from_pdf(file_path)
            elif file_path.endswith(".docx"):
                result_df = self.get_data_from_file_doc(file_path)
            elif file_path.endswith((".xlsx", ".xls")):
                result_df = self.get_data_from_file_excel(file_path)
            else:
                self.logger.error(f"Unsupported file type for {file_path}")
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {str(e)}")

        if result_df is None:
            self.logger.warning(f"Resulting DataFrame is None for file {file_path}")
            return pd.DataFrame()

        if result_df.empty:
            self.logger.warning(f"Resulting DataFrame is empty for file {file_path}")
            return pd.DataFrame()

        self.logger.info(f"Successfully processed file: {file_path}")
        return result_df

    def extract_filename(self, content_disposition):
        if not content_disposition:
            return None
        parts = content_disposition.split(";")
        for part in parts:
            if part.strip().startswith("filename="):
                filename = part.split("=")[1]
                filename = filename.strip("\"'")
                return unquote(filename)  # URL-decode the filename
        return None

    def sam_gov_1st_api(self, q):
        max_retries = 20
        attempts = 0
        while attempts < max_retries:
            try:
                url = self.url.format(q)
                response = requests.get(url, headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    if "_embedded" in data and "results" in data["_embedded"]:
                        results = data["_embedded"]["results"]
                        if len(results) > 0 and "_id" in results[0]:
                            id = results[0]["_id"]
                            print("ID:", id)
                            return id
                    else:
                        print("No ID results found.")
                        return None
                else:
                    print("Failed to fetch data from 1st API. Status code:", response.status_code)
                    attempts += 1
                    if attempts < max_retries:
                        print("Retrying in 5 seconds...")
                        time.sleep(10)
                    else:
                        print("Maximum retries reached. Aborting.")
                        return None
            except requests.RequestException as e:
                print("An error occurred:", e)
                attempts += 1
                if attempts < max_retries:
                    print("Retrying in 5 seconds...")
                    time.sleep(10)
                else:
                    print("Maximum retries reached after error. Aborting.")
                    return None

    def sam_gov_2nd_api(self, id):
        max_retries = 20
        attempts = 0
        while attempts < max_retries:
            try:
                url = f"https://sam.gov/api/prod/opps/v2/opportunities/{id}/history"
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if "history" in data and len(data["history"]) > 0:
                        for entry in data["history"]:
                            if entry.get("procurementType") == "o":
                                opportunity_id = entry.get("opportunityId")
                                if opportunity_id:
                                    print("Opportunity ID:", opportunity_id)
                                    return opportunity_id
                        else:
                            print("No opportunity found with procurementType 'o'.")
                            return None
                    else:
                        print("No history found.")
                        return None
                else:
                    print("Failed to fetch data from 2nd API. Status code:", response.status_code)
                    attempts += 1
                    if attempts < max_retries:
                        print("Retrying in 5 seconds...")
                        time.sleep(10)
                    else:
                        print("Maximum retries reached. Aborting.")
                        return None
            except requests.RequestException as e:
                print("An error occurred:", e)
                attempts += 1
                if attempts < max_retries:
                    print("Retrying in 5 seconds...")
                    time.sleep(10)
                else:
                    print("Maximum retries reached after error. Aborting.")
                    return None

    def sam_gov_3rd_api(self, opportunity_id):
        self.logger.info("Inside sam_gov_3rd_api (sam gov)")
        max_retries = 20  # Set maximum number of retries
        if opportunity_id:  # Ensure there is an opportunity_id
            # Construct the API URL
            url = f"https://sam.gov/api/prod/opps/v3/opportunities/{opportunity_id}/resources"
            attempts = 0  # Initialize attempt counter
            while attempts < max_retries:
                try:
                    response = requests.get(url)
                    if response.status_code == 200:
                        data = response.json()
                        self.logger.info("response status code 200 (sam gov)")
                        if "_embedded" in data and "opportunityAttachmentList" in data["_embedded"]:
                            opportunity_attachment_list = data["_embedded"]["opportunityAttachmentList"]
                            self.logger.info("Making opportunity attachment list (sam gov)")
                            if opportunity_attachment_list:
                                temp_dir_name = f"temp_{uuid.uuid4()}"
                                os.makedirs(temp_dir_name, exist_ok=True)

                                for attachment_info in opportunity_attachment_list:
                                    self.logger.info("Itrating over opportunity attachment list  (sam gov)")
                                    attachments = attachment_info.get("attachments", [])
                                    for attachment in attachments:
                                        self.logger.info("Itrating over attachments (sam gov)")
                                        download_url = attachment.get("uri") or \
                                            f"https://sam.gov/api/prod/opps/v3/opportunities/resources/files/{attachment['resourceId']}/download?&status=archived"
                                        
                                        # Retry logic for file download
                                        download_attempts = 0
                                        while download_attempts < max_retries:
                                            self.logger.info("Inside download attempt (sam gov)")
                                            download_response = requests.get(download_url)
                                            if download_response.status_code == 200:
                                                content_disposition = download_response.headers.get("Content-Disposition")
                                                filename = self.extract_filename(content_disposition)
                                                if filename:
                                                    file_path = os.path.join(temp_dir_name, filename)
                                                    with open(file_path, "wb") as file:
                                                        file.write(download_response.content)
                                                    print(f"File saved as {file_path} in the original format.")
                                                    break  # Break the loop if file is successfully downloaded
                                                else:
                                                    print("Filename could not be extracted from the headers.")
                                            else:
                                                print(f"Failed to download the file. Status code: {download_response.status_code}")
                                                download_attempts += 1
                                                if download_attempts < max_retries:
                                                    print("Retrying file download in 5 seconds...")
                                                    time.sleep(5)
                                                else:
                                                    print("Maximum file download retries reached. Moving to the next file.")
                               
                                self.logger.info("Out of download attempt (sam gov)")
                                # Process the downloaded files 
                                for filename in os.listdir(temp_dir_name):
                                    self.logger.info("Inside file processing (sam gov)")
                                    file_path = os.path.join(temp_dir_name, filename)
                                    result_df = self.process_file(file_path)
                                    if not result_df.empty:
                                        break
                                    print(f"Processing file: {file_path}")
                                    
                                self.logger.info("After processing, delete the temporary directory and its contents")
                                # After processing, delete the temporary directory and its contents
                                shutil.rmtree(temp_dir_name)
                                print(f"Temporary directory {temp_dir_name} has been deleted.")
                                return result_df
                            else:
                                print("No opportunity attachment list found.")
                                return pd.DataFrame()
                        else:
                            print("No embedded data or opportunity attachment list found.")
                            return pd.DataFrame()
                    else:
                        print(f"Failed to fetch data. Status code: {response.status_code}")
                        attempts += 1
                        if attempts < max_retries:
                            print("Retrying in 5 seconds...")
                            time.sleep(10)
                        else:
                            print("Maximum retries reached. Aborting.")
                            return pd.DataFrame()
                except requests.RequestException as e:
                    print(f"An error occurred: {e}")
                    attempts += 1
                    if attempts < max_retries:
                        print("Retrying in 5 seconds...")
                        time.sleep(10)
                    else:
                        print("Maximum retries reached after error. Aborting.")
                        return pd.DataFrame()
        else:
            print("Opportunity ID is not defined.")
    
    def fetch_award_name_and_amount(self,id):
        url = f"https://sam.gov/api/prod/opps/v2/opportunities/{id}?random=1712052820349"
        payload = {}
        headers = {}
        response = requests.request("GET", url, headers=headers, data=payload)
        if response.status_code == 200:
            data = response.json()
            if "data2" in data:
                award_data = data["data2"]["award"]
                if "amount" in award_data and "awardee" in award_data:
                    amount = award_data["amount"]
                    name = award_data["awardee"]["name"]
                    return name, amount
                else:
                    print("Amount or name field not found in the data.")
            else:
                print("No data found.")
        else:
            print("Failed to fetch data. Status code:", response.status_code)
        return '', ''

    def fetch_filtered_data_without_v_as_dataframe(self):
        filtered_data = []
        with open(self.cleaned_data_dir, "r", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["PriceType"] == "FSS":
                    continue  # Skip this row if PriceType is 'FSS'
                if not row["ContractNumber"].startswith(
                    "V"
                ):  # Check if ContractNumber does not start with 'V'
                    # Append the entire row to the list
                    filtered_data.append(row)

        # Convert the list of dictionaries to a pandas DataFrame
        df = pd.DataFrame(filtered_data)
        columns_to_check = ['Strength', 'DosageForm', 'Route', 'Ingredient','ContractNumber']
        df_clean = df.drop_duplicates(subset=columns_to_check, keep='first')
        # df.drop_duplicates(subset=['ContractNumber'],inplace=True)
        return df_clean 

    
    def process_contract_numbers(self):
        self.logger.info("Start fetching data from sam gov...")
        
        df = self.fetch_filtered_data_without_v_as_dataframe()
        
        self.logger.info("Keep only the rows that do not have a price type of 'FSS' and whose contract numbers do not start with 'V (sam gov)")
        
        # Path to the output CSV file
        os.makedirs(self.output_dir, exist_ok=True)
        output_path = os.path.join(self.output_dir, "sam_gov_records.csv")
        
        self.logger.info("Creating directory to store scraped data (sam gov)")
        
        # Remove the existing file if it exists
        if os.path.exists(output_path):
            self.logger.info(f"File {output_path} already exists. Removing it.")
            os.remove(output_path)
        
        # Open the CSV file in write mode to create a new file
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ["ContractNumber", "Ingredient", "Strength", "Awardee", "Awarded Value", "Estimated Annual Quantities"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write the header
            writer.writeheader()
            
            self.logger.info("Open file to insert the data at runtime (sam gov)")
            
            for _, row in df.iterrows():
                self.logger.info("Start iterating over filtered data (sam gov)")
                contract_number = row["ContractNumber"]
                print("Contract Number: ", contract_number)
                if contract_number in self.fetched_data_cache:
                    result_df = self.fetched_data_cache[contract_number]
                else:
                    self.fetched_data_cache[contract_number] = pd.DataFrame()
                    self.logger.info("Getting data from the first API (sam gov)")
                    id = self.sam_gov_1st_api(contract_number)
                    if id:
                        self.logger.info("Getting data from the 2nd API (sam gov)")
                        opportunity_id = self.sam_gov_2nd_api(id)
                        if opportunity_id:
                            self.logger.info("Getting data from the 3rd API (sam gov)")
                            result_df = self.sam_gov_3rd_api(opportunity_id)
                            self.logger.info(f"Outside the 3rd API : {result_df} (sam gov)")
                            self.fetched_data_cache[contract_number] = result_df
                    else:
                        continue

                result_df = self.fetched_data_cache[contract_number]

                if result_df is not None and not result_df.empty:
                    self.logger.info("Desired data found (sam gov)")
                    print("Data found: ")
                    print(result_df)
                    self.logger.info("Fetch award name and amount (sam gov)")
                    awardee, awarded_value = self.fetch_award_name_and_amount(id)
                    self.logger.info("Start iterating over result data (sam gov)")
                    for _, result_row in result_df.iterrows():
                        if result_row["Strength"] is not None and result_row["Ingredient"] is not None:
                            if row["Strength"] in result_row["Strength"] and row['Ingredient'] in result_row['Ingredient']:
                                matched_row_info = {
                                    "ContractNumber": contract_number,
                                    "Ingredient": result_row["Ingredient"],
                                    "Strength": result_row["Strength"],
                                    "Awardee": awardee,
                                    "Awarded Value": awarded_value,
                                    "Estimated Annual Quantities": result_row["Estimated Annual Quantities"]
                                }
                                # Write the matched row immediately to the CSV file
                                self.logger.info("Insert the matched data in the csv file (sam gov)")
                                writer.writerow(matched_row_info)
                                break

 
                    
            
        


# Example usage:
# fetcher = FetchSamGov("logeer")
# fetcher.process_contract_numbers()
