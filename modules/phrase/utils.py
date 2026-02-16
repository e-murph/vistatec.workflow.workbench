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

# utils.py
import logging
import pandas as pd


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def extract_language(file_str):
    """
    Extract the language code from the 'File' string.
    Assumes format like "path | en_us>lang_code".
    """
    try:
        lang_part = file_str.split('|')[-1].strip().split('>')[-1].strip('" ')
        return lang_part
    except IndexError:
        raise ValueError(f"Invalid file string format: {file_str}")


def save_excel(new_df, path, add_chart=False):
    """Save the DataFrame to XLSX with optional pie chart."""
    with pd.ExcelWriter(path, engine='xlsxwriter') as writer:
        new_df.to_excel(writer, index=False, sheet_name='Sheet1')
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']
        bold_format = workbook.add_format({'bold': True})
        last_row = len(new_df)
        worksheet.set_row(last_row, None, bold_format)

        # Auto-adjust column widths with +2 padding
        for col_num, col_name in enumerate(new_df.columns):
            series = new_df.iloc[:, col_num].astype(str)
            max_len = max(series.apply(len).max(), len(col_name))
            worksheet.set_column(col_num, col_num, max_len + 2)

        if add_chart:
            chart = workbook.add_chart({'type': 'pie'})
            
            # Categories: Columns 2 (ICE) to 9 (Repetitions)
            # 0=Filename, 1=Total, 2=ICE ... 9=Repetitions, 10=TotalChars
            chart.add_series({
                'name': 'Word Count Distribution',
                'categories': ['Sheet1', 0, 2, 0, 9],  
                'values': ['Sheet1', last_row, 2, last_row, 9],
            })
            
            chart.set_title({'name': 'Word Count by Category'})
            worksheet.insert_chart('L2', chart)