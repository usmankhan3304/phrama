import csv
import os
import re
import pandas as pd
from selenium import webdriver


class DataWrangling:
    def __init__(self):

        # Chorme_Driver Setting
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless')
        # self.driver = webdriver.Chrome(options= options)

        self.driver = None
        self.link = ""

        self.output_dir_clean = "scraper/fetch_data/cleaned_data"
        self.output_dir_missing = "scraper/fetch_data/missing_data"

        self.route_keywords = [
            "ORAL",
            "SYRINGE",
            "SYRINGE KET",
            "SOLN",
            "SA",
            "CHEW",
            "OPTH",
            "CONC",
            "RTL",
            "EC-ORAL",
            "CHEWG GUM",
            "CHEWABLE",
            "CLICKEASY",
            "INTRATHECAL",
            "IMPLANT",
            "SUSP",
            "VAG",
            "INTRAVITREAL",
            "OPH",
            "TOP",
            "EMULSION",
            "BAG",
            "HUMALOG",
            "KWIKPEN",
            "LYUMJEV",
            "CARTRIDGE",
            "PEN",
            "PWDR",
            "UD",
            "INJ",
        ]
        self.dosage_form_keywords = [
            "TAB",
            "CAP",
            "INJ",
            "SOLN",
            "CREAM",
            "OINT",
            "LIQUID",
            "PACK",
            "GEL",
            "PAD",
            "SUPP",
            "INHL",
            "INSULIN",
            "VACCINE",
            "SPRAY",
            "LOTION",
            "FILM",
            "OIL",
            "AEROSOL",
            "CAPLET",
            "WASH",
            "SHAMPOO",
            "FOAM",
            "SOLUTION",
            "TABS",
            "SYRUP",
            "DROPS",
            "JELLY",
            "ENEMA",
            "NEEDLE",
            "TAPE",
            "GRNL",
            "INHALER",
            "SUPPLEMENT",
            "SUPS",
            "SUSP",
            "PWDR",
            "POWDER",
            "APPLICATOR" "SDV",
            "IMPLANT",
            "CONC",
            "INSERT",
            "RING",
            "SKIN",
            "PELLET",
            "EMULSION",
            "PASTE",
            "SWABSTICK",
            "APPLICATOR",
        ]
        self.strength_keywords = [
            "MG",
            "ML",
            "MCG",
            "%",
            "UNT",
            "VIL",
            "GM",
            "MEQ",
            "mg",
        ]

        self.dosage_form_mapping = {
            "SUSP": "SUSPENSION",
            "TAB": "TABLET",
            "CAP": "CAPSULE",
            "INJ": "INJECTABLE",
            "SOLN": "SOLUTION",
            "CREAM": "CREAM",
            "OINT": "OINTMENT",
            "LIQUID": "LIQUID",
            "PACK": "PACK",
            "SYRINGE": "SYRINGE",
            "GEL": "GEL",
            "TOOTHPASTE": "TOOTHPASTE",
            "PAD": "PAD",
            "SUPP": "SUPPOSITORY",
            "INJECTOR": "INJECTOR",
            "INHL": "INHALER",
            "INSULIN": "INSULIN",
            "PWDR": "POWDER",
            "VACCINE/PF": "VACCINE/PREFILLED",
            "VACCINE": "VACCINE",
            "TABLET": "TABLET",
            "IMPLANT": "IMPLANT",
            "(1500MG)TAB": "TABLET (1500MG)",
            "SPRAY": "SPRAY",
            "LOTION": "LOTION",
            "FILM": "FILM",
            "OIL": "OIL",
            "AEROSOL": "AEROSOL",
            "CAPLET": "CAPLET",
            "SYRUP": "SYRUP",
            "WASH": "WASH",
            "SHAMPOO": "SHAMPOO",
            "FOAM": "FOAM",
            "SOLUTION": "SOLUTION",
            "120MGCAP": "CAPSULE (120MG)",
            "TABS": "TABLETS",
            "EMULSION": "EMULSION",
            "INSERT": "INSERT",
            "180MCG/INHL": "INHALER (180MCG)",
            "90MCG/INHL": "INHALER (90MCG)",
            "LIQUID(360ML)": "LIQUID (360ML)",
            "CAPTAB": "CAPSULE/TABLET",
            "DROPS": "DROPS",
            "SOFTGEL": "SOFTGEL",
            "CAP/TAB": "CAPSULE/TABLET",
            "ENEMA": "ENEMA",
            "SOFTGELS": "SOFTGELS",
            "(HBP)TAB": "TABLET (HBP)",
            "CAPS": "CAPSULES",
            "SGEL": "GEL (SOFT)",
            "CAPSULE": "CAPSULE",
            "CAPSAICIN": "CAPSAICIN",
            "W/APPLICATOR": "WITH APPLICATOR",
            "RING": "RING",
            "AUTOINJECTOR": "AUTOINJECTOR",
            "TAPE": "TAPE",
            "GRNL": "GRANULES",
            "CONC": "CONCENTRATE",
            "100MGTAB": "TABLET (100MG)",
            "150MGTAB": "TABLET (150MG)",
            "INJCT": "INJECT",
            "INHALER": "INHALER",
            "40/AMLODIPINE5/HYDROCHLOROTHIAZIDE12.5MGTAB": "TABLET (40/5/12.5MG)",
            "MEDOXOMIL40/AMLODIPINE10/HYDROCHLOROTHIAZIDE12.5MGTAB": "TABLET (40/10/12.5MG)",
            "25MGTAB": "TABLET (25MG)",
            "OIL)": "OIL",
            "INJECTION": "INJECTION",
            "GEL/PF": "GEL/PREFILLED",
            "INJINJ": "INJECTION",
            "PASTE": "PASTE",
            "PELLET": "PELLET",
            "APPLICATOR": "APPLICATOR",
            "INJ)": "INJECTION",
            "1GM/INJ": "INJECTION (1GM)",
            "2GM/INJ": "INJECTION (2GM)",
            "4GM/INJ": "INJECTION (4GM)",
            "JELLY": "JELLY",
            "UNT/INJ": "UNIT/INJECTION",
            "CAP)": "CAPSULE",
            "AQ": "AQUEOUS",
            "CREAM.TOP": "CREAM (TOPICAL)",
            "OINTMENT": "OINTMENT",
            "SOL": "SOLUTION",
            "0.5%SOLN": "SOLUTION (0.5%)",
            "40MGX2": "TABLET (40MG X 2)",
            "w/NEEDLE": "WITH NEEDLE",
            "SWABSTICK": "SWABSTICK",
            "VACCINE/0.5ML": "VACCINE (0.5ML)",
            "W/SYRINGE": "WITH SYRINGE",
            "5MGTAB": "TABLET (5MG)",
            "10MGTAB": "TABLET (10MG)",
            "20MGTAB": "TABLET (20MG)",
            "PEDIATRIC": "PEDIATRIC",
            "ADULT": "ADULT",
            "INJ/BAG": "INJECTION/BAG",
        }

        self.route_mapping = {
            "ORAL": "ORAL",
            "SYRINGE": "SYRINGE",
            "EMULSION": "EMULSION",
            "SOLN": "SOLUTION",
            "EMULSION VIL": "EMULSION VIAL",
            "INJ": "INJECTION",
            "SA": "SUBLINGUAL ADMINISTRATION",
            "PEN 1.56ML": "PEN 1.56ML",
            "TOP": "TOPICAL",
            "CLICKEASY": "CLICKEASY",
            "PWDR": "POWDER",
            "BAG": "BAG",
            "UD": "UNKNOWN DOSAGE",
            "SUSP": "SUSPENSION",
            "CHEWABLE": "CHEWABLE",
            "CHEWG": "CHEWING GUM",
            "NASAL 9.9ML": "NASAL (9.9ML)",
            "NASAL 15.8ML": "NASAL (15.8ML)",
            "RTL": "RETROBULBAR",
            "SYRINGE 10ML": "SYRINGE (10ML)",
            "SYRINGE 17ML": "SYRINGE (17ML)",
            "PEN 1ML": "PEN 1ML",
            "SYRINGE 1ML": "SYRINGE (1ML)",
            "NASAL": "NASAL",
            "HUMALOG": "HUMALOG",
            "CARTRIDGE 3ML": "CARTRIDGE (3ML)",
            "KWIKPEN 3ML": "KWIKPEN (3ML)",
            "KWIKPEN": "KWIKPEN",
            "LYUMJEV": "LYUMJEV",
            "PEN": "PEN",
            "PEN 2.4ML": "PEN 2.4ML",
            "SOLN 40ML": "SOLUTION (40ML)",
            "SOLN 4ML": "SOLUTION (4ML)",
            "RENST-ORAL": "RENST-ORAL",
            "ORAL 2ML": "ORAL (2ML)",
            "SYRINGE 0.5ML": "SYRINGE (0.5ML)",
            "SOLN 12ML": "SOLUTION (12ML)",
            "SOLN 24ML": "SOLUTION (24ML)",
            "IMPLANT": "IMPLANT",
            "SOLN VIL": "SOLUTION VIAL",
            "INTRATHECAL": "INTRATHECAL",
            "TOP 8.1ML": "TOPICAL (8.1ML)",
            "OPH": "OPHTHALMIC",
            "VAG": "VAGINAL",
            "TOP 63GM": "TOPICAL (63GM)",
            "OINT": "OINTMENT",
            "SOLN 15ML": "SOLUTION (15ML)",
            "SOLN 0.4ML": "SOLUTION (0.4ML)",
            "OPH 0.4ML": "OPHTHALMIC (0.4ML)",
            "CAP": "CAPSULE",
            "TAB": "TABLET",
            "180MCG/INHL": "INHALER (180MCG)",
            "90MCG/INHL": "INHALER (90MCG)",
            "CHEW": "CHEW",
            "NASAL 8.43GM": "NASAL (8.43GM)",
            "ORAL(360ML)": "ORAL (360ML)",
            "CONC": "CONCENTRATE",
            "ORAL 1ML": "ORAL (1ML)",
            "SYRINGE 2ML": "SYRINGE (2ML)",
            "SYRINGE 6ML": "SYRINGE (6ML)",
            "SYRINGE 0.6ML": "SYRINGE (0.6ML)",
            "PENFILL 3ML": "PENFILL (3ML)",
            "100U/ML": "100U/ML",
            "FLEXPEN 3ML": "FLEXPEN (3ML)",
            "PEN 0.5ML": "PEN (0.5ML)",
            "LYOPHILIZED": "LYOPHILIZED",
            "SOLN 26ML": "SOLUTION (26ML)",
            "SOLN 0.5ML": "SOLUTION (0.5ML)",
            "SOLN 3ML": "SOLUTION (3ML)",
            "SOLN 1.7ML": "SOLUTION (1.7ML)",
            "ORAL 25ML": "ORAL (25ML)",
            "EC-ORAL": "ENTERIC COATED - ORAL",
            "INJ VIL": "INJECTION VIAL",
            "RCNST-ORAL": "RECONSTITUTED - ORAL",
            "AUTOINJECTOR": "AUTOINJECTOR",
            "ORAL 5ML": "ORAL (5ML)",
            "BAG 100ML": "BAG (100ML)",
            "BAG 200ML": "BAG (200ML)",
            "BAG 300ML": "BAG (300ML)",
            "BAG 400ML": "BAG (400ML)",
            "BAG 150ML": "BAG (150ML)",
            "BAG 250ML": "BAG (250ML)",
            "BAG 350ML": "BAG (350ML)",
            "ORAL 10.2GM": "ORAL (10.2GM)",
            "4.5MCG": "4.5MCG",
            "SYRINGE 5ML": "SYRINGE (5ML)",
            "ORAL 10.7GM": "ORAL (10.7GM)",
            "ORAL 5.9GM": "ORAL (5.9GM)",
            "2.5MG": "2.5MG",
            "5MG": "5MG",
            "SOLN 16ML": "SOLUTION (16ML)",
            "SYRINGE 0.1ML": "SYRINGE (0.1ML)",
            "SYRINGE 0.2ML": "SYRINGE (0.2ML)",
            "SYRINGE 0.67ML": "SYRINGE (0.67ML)",
            "ORALLY": "ORALLY",
            "SOLN 5ML": "SOLUTION (5ML)",
            "ORAL 6.7GM": "ORAL (6.7GM)",
            "10X10UD": "10X10UD",
            "SYRINGE 125ML": "SYRINGE (125ML)",
            "SYRINGE 15ML": "SYRINGE (15ML)",
            "SYRINGE 20ML": "SYRINGE (20ML)",
            "SOLN 2.5ML": "SOLUTION (2.5ML)",
            "SOLN 10ML": "SOLUTION (10ML)",
            "SUSP 1ML": "SUSPENSION (1ML)",
            "SYRINGE 1.91ML": "SYRINGE (1.91ML)",
            "SYRINGE 0.8ML": "SYRINGE (0.8ML)",
            "SOLN 1ML": "SOLUTION (1ML)",
            "CARTRIDGE": "CARTRIDGE",
            "BAG 50ML": "BAG (50ML)",
            "NASAL 1.3ML": "NASAL (1.3ML)",
            "SOLN 2ML": "SOLUTION (2ML)",
            "ORAL 18GM": "ORAL (18GM)",
            "AEROSOL": "AEROSOL",
            "ORAL 12GM": "ORAL (12GM)",
            "1GM/INJ": "INJECTION (1GM)",
            "2GM/INJ": "INJECTION (2GM)",
            "4GM/INJ": "INJECTION (4GM)",
            "SYRINGE 50ML": "SYRINGE (50ML)",
            "SOLN 10ML(PFS)": "SOLUTION (10ML, PREFILLED SYRINGE)",
            "SOLN 20ML(PFS)": "SOLUTION (20ML, PREFILLED SYRINGE)",
            "ORAL 10ML": "ORAL (10ML)",
            "ORAL 13GM": "ORAL (13GM)",
            "ORAL 8.8GM": "ORAL (8.8GM)",
            "SYRINGE 0.17ML": "SYRINGE (0.17ML)",
            "SOLN 20ML": "SOLUTION (20ML)",
            "SOLN 50ML": "SOLUTION (50ML)",
            "ORAL 15GM": "ORAL (15GM)",
            "ORAL 8.5GM": "ORAL (8.5GM)",
            "VACCINE": "VACCINE",
            "42MCG/ACTUATION": "42MCG/ACTUATION",
            "ORAL 8GM": "ORAL (8GM)",
            "ORAL 1.5ML": "ORAL (1.5ML)",
            "SUSP 0.5ML": "SUSPENSION (0.5ML)",
            "SUSP 20ML": "SUSPENSION (20ML)",
            "OPTH": "OPTH",
            "SYRINGE 4ML": "SYRINGE (4ML)",
            "60MG/1.5ML": "60MG/1.5ML",
            "PEN 2ML": "PEN (2ML)",
            "PEN 1.14ML": "PEN (1.14ML)",
            "SYRINGE 0.4ML": "SYRINGE (0.4ML)",
            "SYRINGE 0.3ML": "SYRINGE (0.3ML)",
            "SYRINGE 1.0ML": "SYRINGE (1.0ML)",
            "NASAL 16ML": "NASAL (16ML)",
            "ORAL 30ML": "ORAL (30ML)",
            "ORAL 15ML": "ORAL (15ML)",
            "ORAL 10.3GM": "ORAL (10.3GM)",
            "CREAM": "CREAM",
            "SOLUTION": "SOLUTION",
            "100000UNT/GM": "100000UNT/GM",
            "NASAL 17GM": "NASAL (17GM)",
            "NASAL 30ML": "NASAL (30ML)",
            "AQ": "AQUEOUS",
            "SYRINGE 3ML": "SYRINGE (3ML)",
            "TOP 0.65ML": "TOPICAL (0.65ML)",
            "INHL": "INHALER",
            "SYRINGE 2.5ML": "SYRINGE (2.5ML)",
            "BAG 500ML": "BAG (500ML)",
            "BAG 1000ML": "BAG (1000ML)",
            "0.5%SOLN": "SOLUTION (0.5%)",
            "80MGX1": "80MGX1",
            "10000UNT/GM": "10000UNT/GM",
            "SOLN 0.9ML": "SOLUTION (0.9ML)",
            "SOLN 30ML": "SOLUTION (30ML)",
            "SYRINGE 0.9ML": "SYRINGE (0.9ML)",
            "AUTOINJECTOR 0.5ML": "AUTOINJECTOR (0.5ML)",
            "AUTOINJECTOR 1ML": "AUTOINJECTOR (1ML)",
            "AUTOINJECTOR 2ML": "AUTOINJECTOR (2ML)",
            "SOLN 0.7ML": "SOLUTION (0.7ML)",
            "55MCG/ACTUATION": "55MCG/ACTUATION",
            "ORAL 32ML": "ORAL (32ML)",
            "ORAL 60ML": "ORAL (60ML)",
            "INTRATHECAL 1ML": "INTRATHECAL (1ML)",
            "INTRATHECAL 5ML": "INTRATHECAL (5ML)",
            "INTRATHECAL 20ML": "INTRATHECAL (20ML)",
            "SYRINGE 1.6ML": "SYRINGE (1.6ML)",
            "SUSP 3ML": "SUSPENSION (3ML)",
            "0.5MMOL/ML": "0.5MMOL/ML",
            "ORAL 0.5ML": "ORAL (0.5ML)",
            "ORAL 2.5ML": "ORAL (2.5ML)",
            "PEN 2.48ML": "PEN (2.48ML)",
            "NASAL 12.5GM": "NASAL (12.5GM)",
            "ORAL 6.1GM": "ORAL (6.1GM)",
            "NASAL 6.1GM": "NASAL (6.1GM)",
            "12MCG/ACTUAT": "12MCG/ACTUATION",
            "2.5MG/SYSTEM": "2.5MG/SYSTEM",
            "10MG/SYSTEM": "10MG/SYSTEM",
            "20MG/SYSTEM": "20MG/SYSTEM",
            "TOP 7.5GM": "TOPICAL (7.5GM)",
            "SYRINGE 1.5ML": "SYRINGE (1.5ML)",
            "POWDER": "POWDER",
            "ORAL 10.6GM": "ORAL (10.6GM)",
            "NASAL 6.8GM": "NASAL (6.8GM)",
            "NASAL 10.6GM": "NASAL (10.6GM)",
            "750MG/150ML": "750MG/150ML",
            "BAG 20ML": "BAG (20ML)",
            "ORAL 45ML": "ORAL (45ML)",
        }

    def extract_values_from_generic_column(self, generic_str):
        
        
        # if generic_str == 'AMLODIPINE BESYLATE 2.5MG TAB':
        #     print(generic_str)

        numeric_pattern = re.compile(r"\d")
        numeric_index = None
        for index, char in enumerate(generic_str):
            if numeric_pattern.match(char):
                numeric_index = index
                break

        if numeric_index is not None:
            ingredient = generic_str[:numeric_index].strip()
        else:
            ingredient = generic_str.strip()

        ingredient = ingredient.rstrip("-#")
        if "," in ingredient:
            ingredient = ingredient.split(",")[0].strip()

        parts = generic_str.split(" ")
        dosage_form = None
        strength = None
        route = None

        for part in parts:
            for keyword in self.dosage_form_keywords:
                if keyword in part:
                    if "," in part:
                        if keyword in part.split(",")[0]:
                            dosage_form = part.split(",")[0]
                        else:
                            dosage_form = part.split(",")[1]
                    else:
                        dosage_form = part
                    break

        for part in parts:
            for keyword in self.route_keywords:
                if keyword in part:
                    if "," in part:
                        if keyword in part.split(",")[1]:
                            if len(part.split(",")) >= 3 and any(
                                unit in part.split(",")[2]
                                for unit in self.strength_keywords
                            ):
                                route = f'{part.split(",")[1]} {part.split(",")[2]}'
                            else:
                                route = part.split(",")[1]
                        else:
                            if "," in part.split(",")[0]:
                                route = part.split(",")[0].replace(",", " ")
                            else:
                                route = part.split(",")[0]
                    else:
                        if keyword == part:
                            route = part
                        else:
                            route = ""
                    break

        for i, part in enumerate(parts):
            if any(unit in part for unit in self.strength_keywords):
                strength = part
                # Check if the part is not already in the ingredient to avoid overlap
                if strength in ingredient:
                    continue
                # Ensure the strength contains a digit
                if not any(char.isdigit() for char in strength):
                    if i > 0:
                        strength = parts[i - 1] + " " + strength
                break

        # ingredient = parts[0]

        return dosage_form, strength, route, ingredient

    def drop_rows_with_missing_values(self, df, columns_to_check, output_filename):

        missing_values_df = df[df[columns_to_check].isnull().any(axis=1)]
        df = df.dropna(subset=columns_to_check)
        missing_values_df.to_csv(output_filename, index=False)

        return df

    def clean_and_save_data(self, df):

        print("Perfroming data cleaning and saving data...")

        # Drop duplicates and save to a separate file
        df_deduplicated = df.drop_duplicates(subset="NDCWithDashes")
        os.makedirs(self.output_dir_missing, exist_ok=True)
        output_path = os.path.join(self.output_dir_missing, "NDC_duplicated_data.csv")
        df_deduplicated.to_csv(output_path, index=False)

        # Extract values from the "Generic" column and perform other operations
        df["DosageForm"], df["Strength"], df["Route"], df["Ingredient"] = zip(
            *df["Generic"].apply(self.extract_values_from_generic_column)
        )

        df["VendorName"] = df["VendorName"].str.replace(",", "")

        # Drop rows with missing values
        os.makedirs(self.output_dir_missing, exist_ok=True)
        output_path_missing_values = os.path.join(
            self.output_dir_missing, "missing_values(strength and DosageForm).csv"
        )
        df_cleaned = self.drop_rows_with_missing_values(
            df, ["Strength", "DosageForm"], output_path_missing_values
        )
        df_cleaned['DosageForm'] = df['DosageForm'].map(self.dosage_form_mapping)
        df_cleaned['Route'] = df_cleaned['Route'].map(self.route_mapping)
    
        # Save the cleaned data to a file
        os.makedirs(self.output_dir_clean, exist_ok=True)
        output_path_cleaned_data = os.path.join(
            self.output_dir_clean, "cleaned_vaFssPharmPrices.csv"
        )
        df_cleaned.to_csv(output_path_cleaned_data, index=False)

    def read_excel_file(self, file_path):
        print("Reading Excel File ...")
        df = pd.read_excel(file_path)
        return df

    def prepare_data(self, file_path):

        df = self.read_excel_file(file_path)

        # Reformating the data
        self.clean_and_save_data(df)


# if __name__ == "__main__":
#     scraper = DataWrangling()
#     scraper.prepare_data("vaFssPharmPrices.xlsx")
