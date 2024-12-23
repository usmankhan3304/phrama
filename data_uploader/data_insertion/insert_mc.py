import pandas as pd
import os

# Load the Excel file
df = pd.read_excel('raw_files/01.01.2023 – 01.31.2024 all drugs through McKesson (1).xlsx')  # Replace with your file path

# Rename columns
column_renames = {
    'units': 'NDC Units Purchased',
    'Product Description': 'Product Name'
}
df.rename(columns=column_renames, inplace=True)

# Create output directories if they do not exist
os.makedirs("output/monthly_files", exist_ok=True)
os.makedirs("output/invalid_ndc", exist_ok=True)

# Separate records based on the length of NDC
valid_ndc_df = df[df['NDC'].astype(str).str.len() == 11].copy()
invalid_ndc_df = df[df['NDC'].astype(str).str.len() != 11]

# Save the invalid NDC records into a separate file
invalid_ndc_df.to_csv("output/invalid_ndc/invalid_ndc_records.csv", index=False)

# Split 'Month Aggregation Field' into 'Year' and 'Month' columns
valid_ndc_df.loc[:, 'Year'] = valid_ndc_df['Month Aggregation Field'].astype(str).str[:4]
valid_ndc_df.loc[:, 'Month'] = valid_ndc_df['Month Aggregation Field'].astype(str).str[4:].astype(int)

# Convert numeric month to string month name
valid_ndc_df.loc[:, 'Month'] = valid_ndc_df['Month'].apply(lambda x: pd.to_datetime(f'2023-{x:02d}-01').strftime('%B'))

# Get the unique year-month combinations
unique_months = valid_ndc_df[['Year', 'Month']].drop_duplicates()

# Split the data by year and month and save each combination into a separate file
for _, row in unique_months.iterrows():
    year, month = row['Year'], row['Month']
    month_df = valid_ndc_df[(valid_ndc_df['Year'] == year) & (valid_ndc_df['Month'] == month)]
    output_path = f"output/monthly_files/{year}_{month}.csv"
    month_df.to_csv(output_path, index=False)
    print(f"Saved records for {year}-{month} to {output_path}")

print("Processing complete. Files are saved in the 'output' directory.")
