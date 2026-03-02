import pandas as pd
import os

def process_xlsx_to_csv(input_path, output_path):
    """
    Reads an XLSX file using pandas and saves it as a CSV.
    """
    try:
        # Read the Excel file
        df = pd.read_excel(input_path)
        
        # Save as CSV without the index column
        df.to_csv(output_path, index=False)
        return True, ""
    except Exception as e:
        return False, str(e)