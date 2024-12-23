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
        # Adjust path as needed to point directly to your Excel file
        self.input_file = os.path.join('scraper', 'fetch_data', 'raw_data', 'DOD - PPVG GEN IV 2023 SALES BY NDC 2023 (1).xlsx')

    def insert_dod_data(self):
        # Use pandas to read the Excel file
        data = pd.read_excel(self.input_file, dtype={'NDC': str})
        
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

# # Example usage:
# if __name__ == '__main__':
#     inserter = InsertDODDrugData()
#     inserter.insert_data()
