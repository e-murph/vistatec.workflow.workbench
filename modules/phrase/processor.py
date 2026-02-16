"""
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
"""

import logging
import os
import pandas as pd
from .utils import extract_language, save_excel


def map_csv_columns(csv_path):
    """
    Parses the raw CSV to map Categories (Row 0) and Headers (Row 1)
    to their specific column indices.
    """
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        if len(lines) < 2:
            return {}

        # Parse the raw lines (assuming ; delimiter)
        # Strip BOM if present
        categories = lines[0].strip().replace('\ufeff', '').split(';')
        headers = lines[1].strip().split(';')

        mapping = {}
        current_category = None

        # Loop through HEADERS (Row 1)
        for idx, header in enumerate(headers):
            
            # 1. Update Category if present in Row 0 at this index
            if idx < len(categories):
                cat_val = categories[idx].strip()
                if cat_val:
                    current_category = cat_val
            
            # 2. Map the header to the current category
            if current_category:
                header_name = header.strip()
                
                if current_category not in mapping:
                    mapping[current_category] = {}
                
                mapping[current_category][header_name] = idx
                
        return mapping

    except Exception as e:
        logging.error(f"Error mapping columns for {csv_path}: {e}")
        return {}


def process_csv(csv_path, output_dir):
    """Process a single CSV file and always convert it to 4 XLSX files."""

    # 1. Build the dynamic column map
    col_map = map_csv_columns(csv_path)
    if not col_map:
        logging.error(f"Could not map columns for {csv_path}")
        return

    # 2. Read the data
    df = pd.read_csv(csv_path, sep=';', header=1)
    if df.empty: return

    # Extract language
    first_file = df.iloc[0, 0]
    lang = extract_language(first_file)

    # 3. Helper to get data safely
    def get_data(category, header):
        try:
            col_idx = col_map[category][header]
            return df.iloc[:, col_idx]
        except KeyError:
            return pd.Series(0, index=df.index)

    # 4. Build Base Dictionary
    data_dict = {
        'Filename': df.iloc[:, 0],
        'Total': get_data('Total', 'Words'),
        'Total Characters': get_data('Total', 'Characters'), # Dynamically mapped
        'ICE': get_data('Context Match', 'Words'),
        '100%': get_data('100%', 'Words'),
        '95% - 99%': get_data('95% - 99%', 'Words'),
        '85% - 94%': get_data('85% - 94%', 'Words'),
        '75% - 84%': get_data('75% - 84%', 'Words'),
        '50% - 74%': get_data('50% - 74%', 'Words'),
        'No Match': get_data('No Match', 'Words'),
        'Repetitions': get_data('Repetitions', 'Words')
    }

    # Create DataFrame
    full_df = pd.DataFrame(data_dict)

    # --- DEFINE COLUMN ORDER ---
    # Breakdown columns first (Indices 2 to 9)
    cols = ['Filename', 'Total', 'ICE', '100%', '95% - 99%', '85% - 94%', '75% - 84%', '50% - 74%', 'No Match', 'Repetitions']
    
    # Append 'Total Characters' at the very END (Index 10)
    cols.append('Total Characters')
    
    # Reindex to enforce order
    full_df = full_df.reindex(columns=cols)

    # Numeric Processing
    numeric_cols = full_df.columns[1:]
    full_df[numeric_cols] = full_df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)

    # Add Totals Row
    totals = ['Total'] + [full_df[col].sum() for col in numeric_cols]
    full_df.loc[len(full_df)] = totals

    # 5. File Generation Logic (Always 4 Files)

    basename = os.path.basename(csv_path).rsplit('.', 1)[0]
    
    # Paths
    out_std = os.path.join(output_dir, f"{basename}_{lang}.xlsx")
    out_std_chart = os.path.join(output_dir, f"{basename}_{lang}_chart.xlsx")
    out_no_char = os.path.join(output_dir, f"{basename}_{lang}_no_chars.xlsx")
    out_no_char_chart = os.path.join(output_dir, f"{basename}_{lang}_no_chars_chart.xlsx")

    # --- SAVE STANDARD SET ---
    save_excel(full_df, out_std, add_chart=False)
    save_excel(full_df, out_std_chart, add_chart=True)

    # --- SAVE NO-CHARS SET ---
    no_chars_df = full_df.drop(columns=['Total Characters'])
    save_excel(no_chars_df, out_no_char, add_chart=False)
    save_excel(no_chars_df, out_no_char_chart, add_chart=True)