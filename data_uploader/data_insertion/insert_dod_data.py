import logging
import os
import pandas as pd
from django.db import transaction
from scraper.models import DODDrugData

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InsertDODDrugData:
    def __init__(self):
        pass
    
    def insert_dod_data(self, input_file):
        # Use pandas to read the Excel file
        data = pd.read_excel(input_file, dtype={'NDC': str})
        
        data = data[data['NDC'].apply(len) == 11]
        
        with transaction.atomic():
            for index, row in data.iterrows():
                _, created = DODDrugData.objects.update_or_create(
                    ndc_code=row['NDC'],  # Make sure these column names match your Excel columns
                    defaults={
                        'description': row['Description'],
                        'price': float(row['Dollar Value']) if pd.notna(row['Dollar Value']) else 0.0,
                        'quantity': int(row['Quantity']) if pd.notna(row['Quantity']) else 0
                    }
                )
                if created:
                    logger.info(f'Successfully added dod drug data for NDC: {row["NDC"]}')
