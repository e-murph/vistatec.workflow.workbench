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

# test_logic.py
# test file.


import pytest
from modules.docx.docx_logic import clean_text

def test_clean_text_removes_null_bytes():
    # Test that invisible control characters are removed
    dirty_text = "Hello\x00World"
    cleaned = clean_text(dirty_text)
    assert cleaned == "HelloWorld"

def test_clean_text_leaves_normal_text():
    # Test that normal text is untouched
    normal_text = "Valid String"
    cleaned = clean_text(normal_text)
    assert cleaned == "Valid String"

def test_clean_text_handles_empty():
    # Test empty input
    assert clean_text(None) == ""
    assert clean_text("") == ""