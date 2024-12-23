import json
import os
from decimal import Decimal, InvalidOperation


from django.shortcuts import get_object_or_404
import pandas as pd
from celery import shared_task
from .models import *
from .fetch_data.scraper import PharmaScraper
from .fetch_data.insert_foia_drug_data_from_file import FetchFoiaFile
from .fetch_data.insert_dod_data import InsertDODDrugData
from django.utils import timezone
from celery.signals import task_prerun, task_success, task_failure
import logging
from celery import current_app
from datetime import datetime
from smart_search.task import populate_consolidated_table


scraping_logger = logging.getLogger('scraping')
logger = logging.getLogger(__name__)


def get_manufacturer(name):
    if pd.notna(name) and name.strip():
        manufacturer, created = Manufacturer.objects.update_or_create(name=name.strip())
        return manufacturer
    return None


def insert_main_data(df):
    inserted_rows = 0
    for idx, row in df.iterrows():

        vendor, _ = FSSVendor.objects.update_or_create(vendor_name=row["VendorName"])
        contract, _ = FSSContract.objects.update_or_create(
            contract_number=row["ContractNumber"],
            defaults={
                "contract_start_date": pd.to_datetime(row["ContractStartDate"]).date(),
                "contract_stop_date": pd.to_datetime(row["ContractStopDate"]).date(),
                "vendor": vendor,
            },
        )
        drug, _ = FSSDrug.objects.update_or_create(
            ndc_with_dashes=row["NDCWithDashes"],
            contract=contract,
            vendor=vendor,
            trade_name=row["TradeName"],
            generic_name=row["Generic"],
            dosage_form=row["DosageForm"],
            strength=row["Strength"],
            route=row["Route"],
            va_class=row["VAClass"],
            covered=row["Covered"] == "T",
            prime_vendor=row["PrimeVendor"] == "T",
            ingredient=row["Ingredient"],
            package_description=row["PackageDescription"],
        )

        FSSPricing.objects.update_or_create(
            drug=drug,
            price=row["Price"],
            price_start_date=pd.to_datetime(row["PriceStartDate"]).date(),
            price_stop_date=pd.to_datetime(row["PriceStopDate"]).date(),
            price_type=row["PriceType"],
            non_taa_compliance=row["Non-TAA"],
        )
        inserted_rows += 1
    return inserted_rows


def insert_daily_med_data(df):
    for idx, row in df.iterrows():
        # Fetch the drug object based on the NDC code
        drug = FSSDrug.objects.filter(ndc_with_dashes=row["NDC Code"]).first()

        # If the drug exists, update its fields
        if drug:
            drug.manufactured_by = get_manufacturer(row.get("Manufactured By"))
            drug.manufactured_for = get_manufacturer(row.get("Manufactured For"))
            drug.distributed_by = get_manufacturer(row.get("Distributed By"))

            # Handle image URLs
            image_urls = row.get("Image URLs")
            if image_urls:
                # If the image URLs are stored as a JSON string, load them
                try:
                    drug.image_urls = json.loads(image_urls)
                except json.JSONDecodeError:
                    # If the image URLs are stored as a comma-separated list, split them
                    drug.image_urls = [url.strip() for url in image_urls.split(",")]

            # Save the drug object with the updated data
            drug.save()


def insert_sam_gov_data(df):

    for idx, row in df.iterrows():
        awarded_value = float(row.get("Awarded Value", 0))
        estimated_annual_quantities = row.get(
            "Estimated Annual Quantities", ""
        ).replace(",", "")
        contract = get_object_or_404(FSSContract, contract_number=row["ContractNumber"])

        contract.awardee = row["Awardee"]
        contract.awarded_value = awarded_value
        contract.estimated_annual_quantities = estimated_annual_quantities
        contract.save()


def insert_orange_book_data(df):

    for index, row in df.iterrows():

        obj, created = PotentialLead.objects.update_or_create(
            active_ingredient=row["Ingredient"],
            applicant_holder=row["Applicant Holder"],
            application_number=row["Appl. No."],
            te_code=row.get("TE Code", ""),
            market_status=row["Mkt.Status"],
            dosage_form=row.get("Dosage Form", ""),
            route=row.get("Route", ""),
            strength=row.get(
                "Strength",
            ),
        )


def insert_drug_shortage_data(df_access, df_asph):
    # Insert drug shortage data from the Access data file
    for idx, row in df_access.iterrows():
        defaults = {
            "shortage_status": row["SHORTAGE STATUS"],
        }
        AccessDrugShortageData.objects.update_or_create(
            generic_name=row["GENERIC NAME"], defaults=defaults
        )

    # Insert drug shortage data from the ASPH data file
    for idx, row in df_asph.iterrows():
        defaults = {
            "revision_date": pd.to_datetime(row["REVISION DATE"], errors="coerce"),
            "created_date": pd.to_datetime(row["CREATED DATE"], errors="coerce"),
            "shortage_status": row["SHORTAGE STATUS"],
        }
        AsphDrugShortageData.objects.update_or_create(
            generic_name=row["GENERIC NAME"], defaults=defaults
        )


def insert_ndc_drug_data(df):
    for idx, row in df.iterrows():
        drug_data, created = FOIAUniqueNDCData.objects.update_or_create(
            ndc_code=row["NDC"],
            defaults={
                "description": row["Drug Description"],
                "total_quantity_purchased": row["Total Quantity Purchased"],
                "total_publishable_dollars_spent": row["Total Publishable Dollars Spent"],
            },
        )

# Define a function to convert date format
def convert_date_format(date_str):
        try:
            # Try converting the date string to a datetime object
            return pd.to_datetime(date_str, format='%d-%b-%y').strftime('%Y-%m-%d')
        except ValueError:
            # Return None or handle the error if conversion fails
            return None
# Define a function to clean and convert decimal values
def convert_decimal(value):
    """Convert a value to Decimal, returning 0.00 if the conversion fails or value is 'nan'."""
    try:
        # Remove commas and extra spaces, then convert to decimal
        cleaned_value = str(value).replace(',', '').strip()
        # Convert to decimal, return 0.00 if conversion fails
        return Decimal(cleaned_value) if cleaned_value not in ['nan', ''] else Decimal('0.00')
    except (ValueError, InvalidOperation):
        return Decimal('0.00')

def convert_to_integer(value):
    """Convert a value to integer, returning 0 if the conversion fails or value is 'nan'."""
    try:
        # Remove commas and extra spaces, then convert to float and then to integer
        cleaned_value = str(value).replace(',', '').strip()
        # Convert to integer, return 0 if conversion fails
        return int(float(cleaned_value)) if cleaned_value not in ['nan', ''] else 0
    except (ValueError, TypeError):
        return 0

def estimated_annual_spend_convert_decimal(value):
    """Convert a currency-formatted string to a Decimal, returning 0.00 if conversion fails."""
    try:
        if isinstance(value, str):
            # Remove currency symbols and commas
            cleaned_value = value.replace('$', '').replace(',', '').strip()
            return Decimal(cleaned_value) if cleaned_value not in ['nan', ''] else Decimal('0.00')
        elif isinstance(value, (int, float)):
            return Decimal(value)
    except (ValueError, InvalidOperation):
        return Decimal('0.00')
    return Decimal('0.00')
# def insert_data():

def update_fss_drug_model_with_ndc_data(df):
    """
    Process the DataFrame, update the FSSDrug model, and return the count of inserted rows and unmatched records.
    """
    unmatched_records = []
    output_dir = "scraper/fetch_data/records/daily_med"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    inserted_rows = 0  # To keep track of how many rows are successfully updated

    try:
        for _, row in df.iterrows():
            ndc_code = row.get('NDCWithDashes')
            estimated_annual_quantity = row.get('Estimated Annual Quantities')
            estimated_resolicitation_date = row.get('Estimated resolicitation Date')
            offers = row.get('Offers')
            estimated_annual_spend = row.get('Estimated Annual Spend')
             
            # Clean and convert values
            if isinstance(estimated_annual_quantity, (int, float, str)):
                estimated_annual_quantity = convert_decimal(estimated_annual_quantity)
            if isinstance(estimated_resolicitation_date, str):
                estimated_resolicitation_date = convert_date_format(estimated_resolicitation_date)
            
            offers = convert_to_integer(offers)
            estimated_annual_spend = estimated_annual_spend_convert_decimal(estimated_annual_spend)

            try:
                drugs = FSSDrug.objects.filter(ndc_with_dashes=ndc_code)
                if drugs.exists():
                    for drug in drugs:
                        drug.estimated_annual_quantity = estimated_annual_quantity
                        drug.estimated_resolicitation_date = estimated_resolicitation_date
                        drug.offers = offers
                        drug.estimated_annual_spend = estimated_annual_spend
                        drug.save()
                        inserted_rows += 1  # Increment the count for each successful update
                        logger.info(f"Updated drug with NDC {ndc_code}")
                else:
                    unmatched_records.append({
                        'NDC Code': ndc_code
                    })
                    logger.warning(f"Unmatched NDC Code: {ndc_code}")
            except Exception as e:
                logger.error(f"Failed to update drug with NDC {ndc_code}: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to process NDC data: {str(e)}")

    # Save unmatched records to a CSV file
    if unmatched_records:
        unmatched_df = pd.DataFrame(unmatched_records)
        file_path = os.path.join(output_dir, 'unmatched_records.csv')
        unmatched_df.to_csv(file_path, index=False)

    return inserted_rows, unmatched_records  # Return the number of inserted rows and unmatched records

@shared_task
def insert_scraped_data_async():
    
    scraping_logger.info("Inserting data started...")
    file_paths = {
        "main": os.path.join(
            "scraper", "fetch_data", "cleaned_data", "cleaned_vaFssPharmPrices.csv"
        ),
         "national_contract_list": os.path.join(
            "scraper", "fetch_data", "raw_data", "National_Contract_List.csv"
        ),

        "daily_med": os.path.join(
            "scraper", "fetch_data", "records", "daily_med", "drug_data_daily_med.csv"
        ),
        "sam_gov": os.path.join(
            "scraper", "fetch_data", "records", "sam_gov", "sam_gov_records.csv"
        ),
        "orange_book": os.path.join(
            "scraper", "fetch_data", "records", "orange_book", "orange_book_records.csv"
        ),
        "access_data_drug_shortage": os.path.join(
            "scraper",
            "fetch_data",
            "records",
            "drug_shortage",
            "access_data_drug_shortage.csv",
        ),
        "asph_drug_shortage": os.path.join(
            "scraper",
            "fetch_data",
            "records",
            "drug_shortage",
            "asph_drug_shortage.csv",
        ),
    }

    try:
        # Load all data first if files exist
        dfs = {}
        for key, path in file_paths.items():
            full_path = os.path.abspath(path)
            if not os.path.exists(full_path):
                scraping_logger.error(f"File not found: {path}")
                continue
            dfs[key] = pd.read_csv(full_path)

        # Process the data
        if "main" in dfs:
            scraping_logger.info("Inserting main data...")
            #inserted_rows =22
            inserted_rows = insert_main_data(dfs["main"])
            scraping_logger.info(f"{inserted_rows} rows inserted from main data.")
            
            inserted_rows, unmatched_records = update_fss_drug_model_with_ndc_data(dfs["national_contract_list"])
            scraping_logger.info(f"{inserted_rows} rows inserted for national_contract_list data.")
            if unmatched_records:
                scraping_logger.warning(f"Unmatched records: {unmatched_records}")
                # print(f"Unmatched records: {unmatched_records}") 
              
            #insert_daily_med_data(dfs["daily_med"])
            scraping_logger.info(f"{inserted_rows} rows inserted for daily_med data.")
            insert_sam_gov_data(dfs["sam_gov"])
            scraping_logger.info(f"{inserted_rows} rows inserted for sam_govd data.")
            insert_orange_book_data(dfs["orange_book"])
            scraping_logger.info(f"{inserted_rows} rows inserted for orange_book data.")
            insert_drug_shortage_data(
                 dfs["access_data_drug_shortage"], dfs["asph_drug_shortage"]
             )
            scraping_logger.info(f"{inserted_rows} rows inserted for drug_shortage data.")
            
            DataInsertionRecord.objects.create(drug_type='FSS')

        scraping_logger.info("Data successfully uploaded and processed.")
    except Exception as e:
        scraping_logger.error(f"Failed to process data: {str(e)}")


# Scraping Async Task
@shared_task(bind=True)
def run_pharma_scraper_async(self):
    try:
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        scraping_logger.info(f"Scraping started at {start_time}...")
        scraper = PharmaScraper(scraping_logger)
        scraper.run()
        scraping_logger.info("Started inserting scraped data...")
        insert_scraped_data_async()
        scraping_logger.info("Started inserting data into consolidated table...")
        populate_consolidated_table()
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        scraping_logger.info(f"Scraping and Inserting Process Completed at {end_time}!")
    except Exception as e:
        scraping_logger.error(f"Failed to process data: {str(e)}")
        raise e

@task_prerun.connect(sender=run_pharma_scraper_async)
def task_prerun_handler(sender=None, task_id=None, task=None, **kwargs):
    ScrapingStatus.objects.create(start_time=timezone.now(), status='running', task_id=task_id)
    scraping_logger.info(f"Scraping task {task_id} started at {timezone.now()}")

@task_success.connect(sender=run_pharma_scraper_async)
def task_success_handler(sender=None, result=None, task_id=None, **kwargs):
    scraping_status = ScrapingStatus.objects.get(task_id=task_id)
    scraping_status.status = 'completed'
    scraping_status.end_time = timezone.now()
    scraping_status.save()
    scraping_logger.info(f"Scraping task {task_id} completed at {scraping_status.end_time}")


@task_failure.connect(sender=run_pharma_scraper_async)
def task_failure_handler(sender=None, exception=None, task_id=None, **kwargs):
    scraping_status = ScrapingStatus.objects.get(task_id=task_id)
    scraping_status.status = 'failed'
    scraping_status.end_time = timezone.now()
    scraping_status.save()
    scraping_logger.error(f"Scraping task {task_id} failed at {scraping_status.end_time} with exception: {exception}")
    
    

@shared_task
def insert_foia_drug_data_async():
    try:
        logger.info("Inserting FOIA data started...")
        foia_file = FetchFoiaFile()
        foia_file.run()
        
        # Record the data insertion for FOIA
        DataInsertionRecord.objects.create(drug_type='FOIA')
        logger.info("FOIA data successfully inserted.")
    except Exception as e:
        logger.error(f"Failed to process FOIA data: {str(e)}")


@shared_task
def insert_dod_drug_data_async():
    try:
        logger.info("Inserting DOD drug data started...")
        dod_file = InsertDODDrugData()
        dod_file.insert_dod_data()
        
        # Record the data insertion for DOD
        DataInsertionRecord.objects.create(drug_type='DOD')

        logger.info("DOD drug data successfully inserted.")
    except Exception as e:
        logger.error(f"Failed to process DOD data: {str(e)}")


def insert_scraped_data():
    file_paths = {
        # "main": os.path.join(
        #    "scraper", "fetch_data", "cleaned_data", "cleaned_vaFssPharmPrices.csv"
        # ),
        # "national_contract_list": os.path.join(
        #     "scraper", "fetch_data", "raw_data", "National_Contract_List.csv"
        # ),
        # "daily_med": os.path.join(
        #     "scraper", "fetch_data", "records", "daily_med", "drug_data_daily_med.csv"
        # ),
        # "sam_gov": os.path.join(
        #     "scraper", "fetch_data", "records", "sam_gov", "sam_gov_records.csv"
        # ),
        "orange_book": os.path.join(
            "scraper", "fetch_data", "records", "orange_book", "orange_book_records.csv"
        ),
        # "access_data_drug_shortage": os.path.join(
            
        #     "scraper",
        #     "fetch_data",
        #     "records",
        #     "drug_shortage",
        #     "access_data_drug_shortage.csv",
        # ),
        # "asph_drug_shortage": os.path.join(
            
        #     "scraper",
        #     "fetch_data",
        #     "records",
        #     "drug_shortage",
        #     "asph_drug_shortage.csv",
        # ),
         
        # "ndc_drug_data": os.path.join(
        #     "scraper", "fetch_data", "records", "ndc_drug_data", "ndc_drug_data.csv"
        # ),
    }

    try:
        # Load all data first if files exist
        dfs = {}
        for key, path in file_paths.items():
            full_path = os.path.abspath(path)
            if not os.path.exists(full_path):
                logger.error(f"File not found: {path}")
                continue
            dfs[key] = pd.read_csv(full_path)
        # print(dfs["national_contract_list"])
        # Process the data
        insert_orange_book_data(dfs["orange_book"])
        if "main" in dfs:
            print("Inserting data started...")
            inserted_rows =22
            # inserted_rows = insert_main_data(dfs["main"])
              # Process NDC data
            # inserted_rows, unmatched_records = update_fss_drug_model_with_ndc_data(dfs["national_contract_list"])
            # scraping_logger.info(f"{inserted_rows} rows inserted for national_contract_list data.")
            # if unmatched_records:
            #     scraping_logger.warning(f"Unmatched records: {unmatched_records}")
            #     # print(f"Unmatched records: {unmatched_records}")  
            print(f"{inserted_rows} rows inserted from main data.")
            #insert_daily_med_data(dfs["daily_med"])
            print(f"{inserted_rows} rows inserted for daily_med data.")
            #insert_sam_gov_data(dfs["sam_gov"])
            print(f"{inserted_rows} rows inserted for sam_govd data.")
            insert_orange_book_data(dfs["orange_book"])
            print(f"{inserted_rows} rows inserted for orange_book data.")
            #insert_drug_shortage_data(
            #     dfs["access_data_drug_shortage"], dfs["asph_drug_shortage"]
            # )
            print(f"{inserted_rows} rows inserted for drug_shortage data.")
            #insert_ndc_drug_data(dfs["ndc_drug_data"])
            print(f"{inserted_rows} rows inserted for NDC drug data.")
           

        print("Data successfully uploaded and processed.")
    except Exception as e:
        logger.error(f"Failed to process data: {str(e)}")



def run_pharma_scraper():
    try:
        logger.info("Scraping started...")
        scraper = PharmaScraper(logger)
        scraper.run()
        logger.info("Scraping Process Completed!")
    except Exception as e:
        logger.error(f"Failed to process data: {str(e)}")
        raise e 


def stop_task(task_id):
    try:
        # Revoke (stop) the task using its task ID
        current_app.control.revoke(task_id, terminate=True)
        logger.info(f"Task {task_id} has been successfully stopped.")
        return f"Task {task_id} has been successfully stopped."
    except Exception as e:
        logger.error(f"Failed to stop task {task_id}: {str(e)}")
        return f"Failed to stop task {task_id}: {str(e)}"