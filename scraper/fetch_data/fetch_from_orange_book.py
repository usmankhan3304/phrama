import csv
import os
import re
import time
import requests
from bs4 import BeautifulSoup
import pandas as pd


class FetchOrangeBook:
    def __init__(self,scraping_logger):
        self.logger = scraping_logger
        self.headers = {"content-type": "application/x-www-form-urlencoded"}
        self.cleaned_data_dir = "scraper/fetch_data/cleaned_data/cleaned_vaFssPharmPrices.csv"
        self.url = "https://www.accessdata.fda.gov/scripts/cder/ob/search_product.cfm"
        self.output_dir = "scraper/fetch_data/records/orange_book"
        self.output_file = os.path.join(self.output_dir, "orange_book_records.csv")
        self.selected_columns = [
            "Ingredient",
            "Active Ingredient",
            "Appl. No.",
            "Dosage Form",
            "Route",
            "Strength",
            "Applicant Holder",
            "TE Code",
            "Mkt.Status"
        ]
        self.cached_dataframes = {}
        self.existing_records = set()
        os.makedirs(self.output_dir, exist_ok=True)
        self.initialize_csv_file()

    def initialize_csv_file(self):
        
        if not os.path.exists(self.output_file):
            with open(self.output_file, 'w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=self.selected_columns)
                writer.writeheader()
        else:
            os.remove(self.output_file)
            with open(self.output_file, 'w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=self.selected_columns)
                writer.writeheader()

    def fetch_data_from_orange_book(self, ingredient):
        max_retries = 20  
        attempts = 0  
        
        while attempts < max_retries:
            try:
                ingredients = ingredient.split()  # Splitting the ingredient by whitespace
                
                # Use the first element of the ingredient for initial search
                first_term_payload = f"drugname={ingredients[0]}&discontinued=RX%2COTC%2CDISCN"
                first_term_response = requests.post(url=self.url, data=first_term_payload, headers=self.headers)
                first_term_response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
                first_term_soup = BeautifulSoup(first_term_response.content, "html.parser")
                first_term_table = first_term_soup.find("table")
                
                if first_term_table:
                    # If data found for the first term, create DataFrame and return
                    return self.parse_table_to_dataframe(first_term_table)
                elif len(ingredients) > 1:
                    # If no data found for the first term and there are more terms, try with a combined search of the first and second terms
                    combined_term_payload = f"drugname={'+'.join(ingredients[:2])}&discontinued=RX%2COTC%2CDISCN"
                    combined_term_response = requests.post(url=self.url, data=combined_term_payload, headers=self.headers)
                    combined_term_response.raise_for_status()
                    combined_term_soup = BeautifulSoup(combined_term_response.content, "html.parser")
                    combined_term_table = combined_term_soup.find("table")
                    
                    if combined_term_table:
                        # If data found for the combined term, create DataFrame and return
                        return self.parse_table_to_dataframe(combined_term_table)
                    else:
                        print("No data found for any search term.")
                        return pd.DataFrame()
                else:
                    print("No data found for any search term.")
                    return pd.DataFrame()
            
            except requests.RequestException as e:
                print("Error fetching data from orange book:", e)
                attempts += 1  # Increment the attempt counter
                if attempts < max_retries:
                    print(f"Attempt {attempts} failed, retrying in 5 seconds...")
                    time.sleep(10)  # Wait for 5 seconds before retrying
                else:
                    print("Maximum retries reached. Aborting.")
                    return pd.DataFrame()  # Return an empty DataFrame after exceeding retry limit
    
    def parse_table_to_dataframe(self, table):
        table_data = []
        rows = table.find_all("tr")
        for row in rows:
            row_data = [
                cell.get_text(strip=True) for cell in row.find_all(["th", "td"])
            ]
            # Remove the part containing **...**
            row_data[7] = re.sub(r'\*\*.*$', '', row_data[7]).strip()
            table_data.append(row_data)
        return pd.DataFrame(table_data[1:], columns=table_data[0])

    def process_csv_file(self):
        self.logger.info("Start fetching data from orange book...")
        unmatched_records = []  # List to store records where no match is found
        # Initialize existing_records if not already done
        if not hasattr(self, 'existing_records'):
            self.existing_records = set()
        try:
            df = pd.read_csv(self.cleaned_data_dir)
            if all(col in df.columns for col in ['Ingredient', 'VendorName', 'Route', 'Strength', 'DosageForm']):
                grouped = df.groupby('Ingredient')
                for ingredient, group in grouped:
                    self.logger.info(f"Processing ingredient: {ingredient}")
                    print(f"Processing ingredient: {ingredient}")
                    num_rows = len(group)
                    print(f"Ingredient: {ingredient} has {num_rows} rows.")
                    # Fetch data from the Orange Book for the current ingredient
                    df_results = self.fetch_data_from_orange_book(ingredient)
                    if df_results.empty:
                        self.logger.info(f"No data fetched for ingredient: {ingredient}")
                        print(f"No data fetched for ingredient: {ingredient}")
                        continue
                    # Clean and process the scraped data
                    df_results = df_results[df_results['Active Ingredient'].apply(lambda x: x.split()[0] == ingredient.split()[0])]
                    df_results = df_results.assign(Ingredient=ingredient)
                    # Convert group DataFrame to a list of dictionaries for easier handling
                    group_records = group.to_dict(orient='records')
                    for record in group_records:
                        vendor_name = str(record['VendorName']) if pd.notna(record['VendorName']) else ''
                        route = str(record['Route']) if pd.notna(record['Route']) else ''
                        strength = str(record['Strength']) if pd.notna(record['Strength']) else ''
                        dosage_form = str(record['DosageForm']) if pd.notna(record['DosageForm']) else ''
                        # Initialize a list to collect unmatched rows for the current record
                        unmatched_rows = []
                        # Iterate through each row in df_results
                        for _, row in df_results.iterrows():
                            applicant_holder = row['Applicant Holder'].upper().replace(',', '')
                            # Compare the standardized 'Applicant Holder' with the standardized 'VendorName'
                            if applicant_holder != vendor_name.upper().replace(',', ''):
                                # Add the row to the unmatched_rows list if there's no match
                                unmatched_rows.append(row)
                         # Convert the list of unmatched rows for the current record to a DataFrame
                        unmatched_rows_df = pd.DataFrame(unmatched_rows, columns=df_results.columns)
                        # Print the first record in the 'Applicant Holder' column from the unmatched rows
                        if not unmatched_rows_df.empty:
                            # print("Unmatched Applicant Holder:", unmatched_rows_df['Applicant Holder'].iloc[1])
                            # Save unmatched rows to a CSV file for testing purposes
                            self.append_to_csv(unmatched_rows_df)
                        else:
                            print("No unmatched rows found for vendor:", vendor_name)
                        if not unmatched_rows_df.empty:
                            # Add unmatched record if there is a mismatch
                            unmatched_records.append(record)
                        else:
                            # Filter matching rows if the applicant and vendor name match
                            matching_rows = df_results[
                                (df_results['Applicant Holder'].str.contains(vendor_name.upper().replace(',', ''), case=False, na=False, regex=False)) &
                                (df_results['Dosage Form'].str.contains(dosage_form, case=False, na=False, regex=False)) &
                                (df_results['Strength'].str.upper() == strength.upper())
                            ]
                            if not matching_rows.empty:
                                combined_results = pd.concat([matching_rows]).drop_duplicates(subset=self.selected_columns)
                                unique_new_rows = combined_results[~combined_results[self.selected_columns].apply(tuple, axis=1).isin(self.existing_records)]
                                if not unique_new_rows.empty:
                                    self.append_to_csv(unique_new_rows[self.selected_columns])
                                    new_records_tuples = set(unique_new_rows[self.selected_columns].apply(tuple, axis=1))
                                    self.existing_records.update(new_records_tuples)
                    self.logger.info(f"No matching data found for ingredient: {ingredient}")
                    print(f"No matching data found for ingredient: {ingredient}")
            else:
                self.logger.error("Required columns missing in the CSV file.")
                print("Required columns missing in the CSV file.")
        except Exception as e:
            self.logger.error(f"Error processing CSV file: {e}")
            print(f"Error processing CSV file: {e}")
    def append_to_csv(self, df_results):
        # Ensure self.existing_records is a set for efficient lookups
        if not hasattr(self, 'existing_records'):
            self.existing_records = set()
        # Drop duplicates based on selected columns
        df_results = df_results.drop_duplicates(subset=self.selected_columns)
        # Convert df_results to a list of tuples for checking against existing records
        new_rows = df_results[~df_results[self.selected_columns].apply(tuple, axis=1).isin(self.existing_records)]
        if not new_rows.empty:
            # Append new rows to CSV
            # new_rows.to_csv(self.output_file, mode='a', header=False, index=False)
            new_rows.to_csv(self.output_file, mode='a', header=False, index=False, columns=self.selected_columns)
            # Update existing records with the new rows
            new_records_tuples = set(new_rows[self.selected_columns].apply(tuple, axis=1))
            self.existing_records.update(new_records_tuples)


# if __name__ == "__main__": 
#     scraper = FetchOrangeBook()
#     scraper.process_csv_file()



