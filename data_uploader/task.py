import os
from django.shortcuts import get_object_or_404
import pandas as pd
from celery import shared_task
from scraper.models import *
from .data_insertion.insert_dod_data import InsertDODDrugData
from .data_insertion.insert_foia_drug_data_from_file import FetchFoiaFile 
from celery.signals import task_prerun, task_success, task_failure
import logging

scraping_logger = logging.getLogger('scraping')
logger = logging.getLogger(__name__)


@shared_task
def insert_dod_drug_data_async(file_path):
    try:
        logger.info("Inserting DOD drug data started...")
        dod_file = InsertDODDrugData()
        dod_file.insert_dod_data(file_path)
        
        # Record the data insertion for DOD
        DataInsertionRecord.objects.create(drug_type='DOD')

        logger.info("DOD drug data successfully inserted.")
    except Exception as e:
        logger.error(f"Failed to process DOD data: {str(e)}")


@shared_task
def insert_foia_drug_data_async():
    try:
        logger.info("Inserting FOIA data started...")
        foia_file = FetchFoiaFile()
        foia_file.insert_foia_drug_data_from_file()
        
        # Record the data insertion for FOIA
        DataInsertionRecord.objects.create(drug_type='FOIA')
        logger.info("FOIA data successfully inserted.")
    except Exception as e:
        logger.error(f"Failed to process FOIA data: {str(e)}")


# tasks.py
from celery import shared_task
from .models import FOIAMonthlyStats
import csv
from decimal import Decimal, InvalidOperation
from django.db import IntegrityError, transaction

def safe_decimal_conversion(value, default_value=Decimal('0')):
    try:
        return Decimal(value.strip('$').replace(',', '')) if value else default_value
    except (InvalidOperation, ValueError):
        logger.error(f"Error converting value {value} to Decimal")
        return default_value
    
    
@shared_task
def insert_foia_monthly_status_async_task(file_data):
    logger.info("Inserting FOIA Monthly Status Data started...")

    try:
        ndc_data = {}
        decoded_file = file_data.decode('utf-8').splitlines()

        # Log the content to make sure it's correct
        logger.debug(f"CSV file content: {decoded_file}")

        reader = csv.DictReader(decoded_file)

        for row in reader:
            try:
                logger.debug(f"Processing row: {row}")  # Log each row

                # Get NDC and apply checks
                ndc = row['NDC'].strip()
                if len(ndc) < 11:  # Check if NDC length is less than 11
                    matched_pattern = row.get('Matched Pattern', '').replace('-', '').strip()
                    ndc = matched_pattern if matched_pattern else ndc  # Use "Matched Pattern" if available
                    logger.debug(f"Updated NDC from 'Matched Pattern': {ndc}")

                product_name = row['Product Name'].strip()
                strength = row.get('Strength', None)
                
                # Handle missing or invalid Month and Year values
                month = row.get('Month', '').strip() or None
                year_str = row.get('Year', '').strip() or None

                # Convert year to integer if available
                if year_str:
                    try:
                        year = int(float(year_str))  # Handle formats like '2024.0'
                    except ValueError:
                        logger.warning(f"Invalid year format in row: {row}")
                        year = None
                else:
                    year = None

                # Safely convert the financial data
                dollars_spent = safe_decimal_conversion(row['Dollars Spent'])
                ndc_units_purchased = safe_decimal_conversion(row['NDC Units Purchased'])
                purchase_price = safe_decimal_conversion(row.get('Purchase Price', None))

                # Update or initialize data for each NDC
                if ndc not in ndc_data:
                    ndc_data[ndc] = {
                        'product_name': product_name,
                        'strength': strength,
                        'total_dollar_spent': dollars_spent,
                        'total_units_purchased': ndc_units_purchased,
                        'min_purchase_price': purchase_price,
                        'max_purchase_price': purchase_price,
                        'month': month,
                        'year': year,
                    }
                else:
                    ndc_data[ndc]['total_dollar_spent'] += dollars_spent
                    ndc_data[ndc]['total_units_purchased'] += ndc_units_purchased
                    ndc_data[ndc]['min_purchase_price'] = min(ndc_data[ndc]['min_purchase_price'], purchase_price)
                    ndc_data[ndc]['max_purchase_price'] = max(ndc_data[ndc]['max_purchase_price'], purchase_price)

            except KeyError as e:
                logger.error(f"Missing key in CSV row: {e}")
            except ValueError as e:
                logger.error(f"Error processing row: {e}")
            except Exception as e:
                logger.error(f"Unexpected error while processing row: {str(e)}")

        # Insert the aggregated data into the database
        for ndc, data in ndc_data.items():
            try:
                with transaction.atomic():
                    FOIAMonthlyStats.objects.update_or_create(
                        ndc=ndc,
                        month=data['month'],
                        year=data['year'],
                        defaults={
                            'product_name': data['product_name'].strip(),
                            'strength': data['strength'],
                            'total_dollar_spent': data['total_dollar_spent'],
                            'total_units_purchased': data['total_units_purchased'],
                            'min_purchase_price': data['min_purchase_price'],
                            'max_purchase_price': data['max_purchase_price'],
                        }
                    )
            except IntegrityError as e:
                logger.error(f"Database error while inserting/updating NDC {ndc}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error while inserting/updating NDC {ndc}: {str(e)}")

        logger.info("FOIA Monthly Status Data successfully inserted.")

    except Exception as e:
        logger.error(f"Error processing CSV file: {str(e)}")
        raise


def insert_foia_monthly_status_task(file_data):
    logger.info("Inserting FOIA Monthly Status Data started...")

    try:
        ndc_data = {}
        decoded_file = file_data.decode('utf-8').splitlines()

        # Log the content to make sure it's correct
        logger.debug(f"CSV file content: {decoded_file}")

        reader = csv.DictReader(decoded_file)

        for row in reader:
            try:
                logger.debug(f"Processing row: {row}")  # Log each row

                # Get NDC and apply checks
                ndc = row['NDC'].strip()
                if len(ndc) < 11:  # Check if NDC length is less than 11
                    matched_pattern = row.get('Matched Pattern', '').replace('-', '').strip()
                    ndc = matched_pattern if matched_pattern else ndc  # Use "Matched Pattern" if available
                    logger.debug(f"Updated NDC from 'Matched Pattern': {ndc}")

                product_name = row['Product Name'].strip()
                strength = row.get('Strength', None)
                
                # Handle missing or invalid Month and Year values
                month = row.get('Month', '').strip() or None
                year_str = row.get('Year', '').strip() or None

                # Convert year to integer if available
                if year_str:
                    try:
                        year = int(float(year_str))  # Handle formats like '2024.0'
                    except ValueError:
                        logger.warning(f"Invalid year format in row: {row}")
                        year = None
                else:
                    year = None

                # Safely convert the financial data
                dollars_spent = safe_decimal_conversion(row['Dollars Spent'])
                ndc_units_purchased = safe_decimal_conversion(row['NDC Units Purchased'])
                purchase_price = safe_decimal_conversion(row.get('Purchase Price', None))

                # Update or initialize data for each NDC
                if ndc not in ndc_data:
                    ndc_data[ndc] = {
                        'product_name': product_name,
                        'strength': strength,
                        'total_dollar_spent': dollars_spent,
                        'total_units_purchased': ndc_units_purchased,
                        'min_purchase_price': purchase_price,
                        'max_purchase_price': purchase_price,
                        'month': month,
                        'year': year,
                    }
                else:
                    ndc_data[ndc]['total_dollar_spent'] += dollars_spent
                    ndc_data[ndc]['total_units_purchased'] += ndc_units_purchased
                    ndc_data[ndc]['min_purchase_price'] = min(ndc_data[ndc]['min_purchase_price'], purchase_price)
                    ndc_data[ndc]['max_purchase_price'] = max(ndc_data[ndc]['max_purchase_price'], purchase_price)

            except KeyError as e:
                logger.error(f"Missing key in CSV row: {e}")
            except ValueError as e:
                logger.error(f"Error processing row: {e}")
            except Exception as e:
                logger.error(f"Unexpected error while processing row: {str(e)}")

        # Insert the aggregated data into the database
        for ndc, data in ndc_data.items():
            try:
                with transaction.atomic():
                    FOIAMonthlyStats.objects.update_or_create(
                        ndc=ndc,
                        month=data['month'],
                        year=data['year'],
                        defaults={
                            'product_name': data['product_name'].strip(),
                            'strength': data['strength'],
                            'total_dollar_spent': data['total_dollar_spent'],
                            'total_units_purchased': data['total_units_purchased'],
                            'min_purchase_price': data['min_purchase_price'],
                            'max_purchase_price': data['max_purchase_price'],
                        }
                    )
            except IntegrityError as e:
                logger.error(f"Database error while inserting/updating NDC {ndc}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error while inserting/updating NDC {ndc}: {str(e)}")

        logger.info("FOIA Monthly Status Data successfully inserted.")

    except Exception as e:
        logger.error(f"Error processing CSV file: {str(e)}")
        raise