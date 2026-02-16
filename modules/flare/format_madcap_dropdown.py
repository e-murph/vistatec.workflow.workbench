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

# format_madcap_dropdown.py

import re
from bs4 import BeautifulSoup


def format_madcap_tags(content):
    """
    Format only MadCap:dropDown tags in the given XHTML content.

    Args:
        content (str): The XHTML content as a string.

    Returns:
        str: Content with correctly formatted MadCap:dropDown tags.
    """
    try:
        # Regex to isolate <MadCap:dropDown> blocks
        dropdown_pattern = re.compile(r"<MadCap:dropDown.*?</MadCap:dropDown>", re.DOTALL | re.IGNORECASE)

        def reformat_dropdown(match):
            dropdown_html = match.group(0)
            dropdown_soup = BeautifulSoup(dropdown_html, "html.parser")

            # Format dropDownHead
            head = dropdown_soup.find("MadCap:dropDownHead")
            if head:
                if head.string:
                    head.string = head.string.strip()
                head.insert(0, "\n    ")
                head.append("\n    ")

                hotspot = head.find("MadCap:dropDownHotspot")
                if hotspot:
                    if hotspot.string:
                        hotspot.string = hotspot.string.strip()
                    hotspot.insert(0, "\n        ")
                    hotspot.append("\n    ")

            # Format dropDownBody
            body = dropdown_soup.find("MadCap:dropDownBody")
            if body:
                body.insert(0, "\n    ")
                body.append("\n")

                # Format child elements within dropDownBody
                for child in body.contents:
                    if child.name and child.name in ["li", "ol", "ul", "p"]:
                        if child.string:
                            child.string = child.string.strip()
                        child.insert(0, "\n        ")
                        child.append("\n    ")

            return dropdown_soup.prettify()

        # Apply the reformatting only to <MadCap:dropDown> tags
        formatted_content = dropdown_pattern.sub(reformat_dropdown, content)
        return formatted_content

    except Exception as e:
        print(f"Error formatting MadCap:dropDown tags: {e}")
        return content
