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

# content_cleaning.py

import re


def reformat_xref_variations(content):
    pattern = r'(></MadCap:xref>)(\s*\w+)'
    return re.sub(pattern, lambda match: f"{match.group(1)} {match.group(2).strip()}", content)


def clean_header_tags(content):
    content = re.sub(r'<(h[1-5])>\s+', r'<\1>', content)
    content = re.sub(r'\s+</(h[1-5])>', r'</\1>', content)
    return content


def clean_li_tags(content):
    # Clean <li> tags with direct text content, removing extra spaces but preserving structure
    def clean_direct_content(match):
        # Match direct content only, without nested tags
        return f"<li>{match.group(1).strip()}</li>"

    content = re.sub(r"<li>\s*(\S.*?)\s*</li>", clean_direct_content, content)

    # Preserve structure for <li> with nested tags like <p>, ensuring line breaks remain
    def preserve_nested_structure(match):
        opening_li = match.group(1)
        nested_content = match.group(2)
        closing_li = match.group(3)
        return f"{opening_li}{nested_content}{closing_li}"

    content = re.sub(
        r"(<li>\s*\n)(.*?\n)(\s*</li>)",
        preserve_nested_structure,
        content,
        flags=re.DOTALL,
    )

    return content


def clean_td_tags(content):
    # Clean <td> tags with direct text content, removing extra spaces but preserving structure
    def clean_direct_content(match):
        # Match direct content only, without nested tags
        return f"<td>{match.group(1).strip()}</td>"

    content = re.sub(r"<td>\s*(\S.*?)\s*</td>", clean_direct_content, content)

    # Preserve structure for <td> with nested tags like <p>, ensuring line breaks remain
    def preserve_nested_structure(match):
        opening_td = match.group(1)
        nested_content = match.group(2)
        closing_td = match.group(3)
        return f"{opening_td}{nested_content}{closing_td}"

    content = re.sub(
        r"(<td>\s*\n)(.*?\n)(\s*</td>)",
        preserve_nested_structure,
        content,
        flags=re.DOTALL,
    )

    return content
