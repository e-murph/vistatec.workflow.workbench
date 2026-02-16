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

# file_processing.py - ADAPTED FOR PYQT6 & LOGIC FIXES

import os


from .content_cleaning import (
    reformat_xref_variations,
    clean_header_tags,
    clean_li_tags,
    clean_td_tags,
)
from .file_operations import load_replacements
from .format_madcap_dropdown import format_madcap_tags
from .regex import clean_specific_patterns


def apply_replacements(content, replacements):
    # Sort replacements by key length in descending order to handle longer strings first
    sorted_replacements = sorted(replacements.items(), key=lambda x: len(x[0]), reverse=True)

    # Apply replacements in order
    for find_text, replace_text in sorted_replacements:
        content = content.replace(find_text, replace_text)

    return content


def apply_language_specific_replacements(content, language, file_extension, language_replacements):
    # Correctly access language-specific and then file-extension specific replacements
    replacements_for_file_type = language_replacements.get(language, {}).get(file_extension, {})
    content = apply_replacements(content, replacements_for_file_type)

    # Imported from content_cleaning and regex
    content = reformat_xref_variations(content)
    content = clean_header_tags(content)
    content = clean_specific_patterns(content)
    content = clean_li_tags(content)
    content = clean_td_tags(content)
    # content = format_madcap_tags(content) # Uncomment if you want to use this function
    return content


# Changed signature to accept global replacements
def process_files(folder_path, language, progress_callback, status_callback,
                  language_replacements, xtm_replacements, madcap_replacements):
    if not os.path.exists(folder_path):
        # This will be caught by the Worker's try-except and emitted as an error
        raise FileNotFoundError(f"Selected folder does not exist: {folder_path}")

    files_to_process = []
    for root, _, files in os.walk(folder_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            file_extension = os.path.splitext(file_name)[1].lower()

            if file_extension in ['.html', '.xhtml', '.htm', '.fltoc', '.fltar', '.flsnp', '.flmsp', '.flvar',
                                  '.flprj']:
                files_to_process.append(file_path)

    total_files = len(files_to_process)
    if total_files == 0:
        status_callback("No relevant files found to process.")
        progress_callback(100) # Indicate completion
        return

    for idx, file_path in enumerate(files_to_process):
        try:
            status_callback(f"Processing: {os.path.basename(file_path)}")
            # time.sleep(0.01) # Keep a small delay if you want to visibly see progress for very fast operations

            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            # Apply global replacements
            content = apply_replacements(content, xtm_replacements)
            content = apply_replacements(content, madcap_replacements)

            # Apply language-specific replacements
            content = apply_language_specific_replacements(content, language, os.path.splitext(file_path)[1].lower(),
                                                           language_replacements)

            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)

            progress_percentage = int(((idx + 1) / total_files) * 100)
            progress_callback(progress_percentage)
            status_callback(f"Processed: {os.path.basename(file_path)} ({idx + 1}/{total_files})")

        except Exception as e:
            # Emit error but continue processing other files if possible
            status_callback(f"Error processing {os.path.basename(file_path)}: {e}")
            continue

    status_callback("All files processed.")
