import csv
from decimal import Decimal, InvalidOperation  
from data_uploader.models import FOIAMonthlyStats

def safe_decimal_conversion(value, default_value=Decimal('0')):
    """
    Safely convert a string to a Decimal, removing unwanted characters like $ and commas.
    If the conversion fails or the value is empty, return the default value (Decimal 0).
    """
    try:
        # If the value exists, strip it of unwanted characters and try to convert it to a Decimal
        return Decimal(value.strip('$').replace(',', '')) if value else default_value
    except (InvalidOperation, ValueError):
        # Return default value if conversion fails
        return default_value

def process_foia_monthly_stats_data(input_file_path, output_file_path):
    # Dictionary to store aggregated data for each NDC
    ndc_data = {}

    # Open the input CSV file
    with open(input_file_path, 'r') as input_file:
        reader = csv.DictReader(input_file)
        
        for row in reader:
            ndc = row['NDC']
            product_name = row['Product Name']
            strength = row['Strength']
            month = row['Month']  # Assuming the month column is named 'Month'
            year = int(float(row['Year']))  # Assuming the year column is named 'Year'
            
            # Safely convert fields using the helper function
            dollars_spent = safe_decimal_conversion(row['Dollars Spent'])
            ndc_units_purchased = safe_decimal_conversion(row['NDC Units Purchased'])
            purchase_price = safe_decimal_conversion(row['Purchase Price'])
            
            # Aggregate data for each NDC
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

    # Open the output CSV file to write the results
    with open(output_file_path, 'w', newline='') as output_file:
        fieldnames = ['NDC', 'Product Name', 'Strength', 'Total Dollar Spent', 'Total Units Purchased', 'Min Purchase Price', 'Max Purchase Price', 'Month', 'Year']
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)

        writer.writeheader()

        # Write aggregated data to the new CSV file
        for ndc, data in ndc_data.items():
            writer.writerow({
                'NDC': ndc,
                'Product Name': data['product_name'],
                'Strength': data['strength'],
                'Total Dollar Spent': f"${data['total_dollar_spent']:.2f}",
                'Total Units Purchased': f"{data['total_units_purchased']:.2f}",
                'Min Purchase Price': f"${data['min_purchase_price']:.2f}",
                'Max Purchase Price': f"${data['max_purchase_price']:.2f}",
                'Month': data['month'],
                'Year': data['year'],
            })

    print(f"Aggregated data written to {output_file_path}")

def insert_foia_monthly_stats_data_into_db(input_file_path):
    # Dictionary to store aggregated data for each NDC
    ndc_data = {}

    # Open the input CSV file
    with open(input_file_path, 'r') as input_file:
        reader = csv.DictReader(input_file)
        
        for row in reader:
            ndc = row['NDC']
            product_name = row['Product Name']
            strength = row['Strength']
            month = row['Month']  # Assuming the month column is named 'Month'
            year = int(float(row['Year']))  # Assuming the year column is named 'Year'
            
            # Safely convert fields using the helper function
            dollars_spent = safe_decimal_conversion(row['Dollars Spent'])
            ndc_units_purchased = safe_decimal_conversion(row['NDC Units Purchased'])
            purchase_price = safe_decimal_conversion(row['Purchase Price'])
            
            # Aggregate data for each NDC
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

    # Insert the aggregated data into the database
    for ndc, data in ndc_data.items():
        FOIAMonthlyStats.objects.update_or_create(
            ndc=ndc,
            month=data['month'],
            year=data['year'],
            defaults={
                'product_name': data['product_name'],
                'strength': data['strength'],
                'total_dollar_spent': data['total_dollar_spent'],
                'total_units_purchased': data['total_units_purchased'],
                'min_purchase_price': data['min_purchase_price'],
                'max_purchase_price': data['max_purchase_price'],
            }
        )

    print("Data inserted into the database successfully.")

# Define the input file path
input_file_path = 'raw_files/All Pharm PPV Jan-Feb 24/January-All Pharm PPV Jan-Feb 24-January_data.csv' 
output_file_path = 'FOIA_Monthly_Stats.csv'  


# Call the function to insert data into the database
#insert_foia_monthly_stats_data_into_db(input_file_path)

# Call the function to process the data and write the results to a new CSV file
process_foia_monthly_stats_data(input_file_path, output_file_path)