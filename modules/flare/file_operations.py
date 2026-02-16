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

# file_operations.py

import json
import os
import sys


# Helper function to get the base path for bundled files
def get_resource_path(relative_path):
    """
    Get the absolute path to a resource, whether running from source or PyInstaller bundle.
    """
    # PyInstaller creates a temporary folder and sets _MEIPASS for one-file mode
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running in a PyInstaller bundle
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        # Running from source
        # Assumes the 'settings' folder is relative to the script's directory
        return os.path.join(os.path.dirname(__file__), relative_path)


# Load replacement patterns from a given file, interpreting \n as actual newlines
def load_replacements(filename):
    replacements = {}
    # Construct the correct absolute path to the file
    full_path = get_resource_path(filename)
    try:
        with open(full_path, 'r', encoding='utf-8') as file:
            replacements = json.load(file)
    except FileNotFoundError:
        # Raise an error that can be caught by the GUI
        raise FileNotFoundError(f"File not found: {full_path}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Error parsing JSON file: {full_path} - {e}", "", 0)
    return replacements


# Load language-specific replacements from a JSON file
def load_language_replacements(filename):
    # Construct the correct absolute path to the file
    full_path = get_resource_path(filename)
    try:
        with open(full_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        # Raise an error that can be caught by the GUI
        raise FileNotFoundError(f"Language replacements file not found: {full_path}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Error decoding JSON in file: {full_path} - {e}", "", 0)
