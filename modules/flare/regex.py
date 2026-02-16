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

# regex.py

import re


# Clean specific patterns
def clean_specific_patterns(content):
    # Remove blank spaces in "></a>"
    content = re.sub(r'>\s+</a>', r'></a>', content)

    # Ensure proper spacing for .</a>
    content = re.sub(r'\s*\.</a>\s*(\w)', r'</a>. \1', content)
    content = re.sub(r'\.</a>(\w)', r'</a>. \1', content)
    content = re.sub(r'</a>\.\s*(\w)', r'</a>. \1', content)

    # Remove blank spaces around "listtext"><a"
    content = re.sub(r'"listtext">\s+<a', r'"listtext"><a', content)

    # Remove spaces before <a> inside <li class="SubStep"> tags
    content = re.sub(r'(<li class="SubStep"[^>]*?>)\s+<a', r'\1<a', content)

    # Remove spaces before <a> inside <caption MadCap:autonum=" tags
    content = re.sub(r'(<caption MadCap:autonum="[^>]*?>)\s+<a', r'\1<a', content)

    # Remove spaces before <MadCap inside <caption MadCap:autonum=" tags
    content = re.sub(r'(<caption MadCap:autonum="[^>]*?>)\s+<MadCap', r'\1<MadCap', content)

    # Remove blank spaces around "listtext"><b"
    content = re.sub(r'"listtext">\s+<b>', r'"listtext"><b>', content)

    # Remove blank spaces around "listtext"><MadCap:xref"
    content = re.sub(r'"listtext">\s+<MadCap:xref', r'"listtext"><MadCap:xref', content)

    # Remove blank spaces around <li><MadCap:xref"
    content = re.sub(r'<li>\s+<MadCap:xref', r'<li><MadCap:xref', content)

    # Remove blank spaces around </MadCap:xref></li>
    content = re.sub(r'</MadCap:xref>\s+</li>', r'</MadCap:xref></li>', content)

    # Ensure proper formatting for <b> and <i> tags
    content = re.sub(r'(\w)<(b|i)>', r'\1 <\2>', content)
    content = re.sub(r'<(b|i)>(\s){1,}', r'<\1>', content)
    content = re.sub(r'</(b|i)>(\w)', r'</\1> \2', content)
    content = re.sub(r'\s+</(b|i)>(\w)', r'</\1> \2', content)

    # Remove spacing between </a> and <MadCap:keyword>
    content = re.sub(r'</a>\s+<MadCap:keyword', r'</a><MadCap:keyword', content)

    # Fix spacing after <MadCap:keyword term="..." />
    content = re.sub(r'(<MadCap:keyword term="[^"]+" />)\s+<MadCap:', r'\1<MadCap:', content)

    # Remove spaces in <h1 class="heading1">
    content = re.sub(r'<h1 class="heading1">\s+(\w)', r'<h1 class="heading1">\1', content)

    # Remove spaces before <a> inside <h1 MadCap:autonum=" tags
    content = re.sub(r'(<h1 MadCap:autonum="[^>]*?>)\s+<a', r'\1<a', content)

    # Fix spaces before closing </p>
    # content = re.sub(r'\.\s+</p>', r'.</p>', content)

    # Fix spaces before closing </p>
    content = re.sub(r'\s+</p>', r'</p>', content)

    # Remove spaces after paragraph tags <p>
    content = re.sub(r'<p>\s+', r'<p>', content)

    # Remove spaces after <p MadCap:conditions=" tags
    content = re.sub(r'(<p MadCap:conditions="[^>]*?>)\s+', r'\1', content)

    # Replace spaces between a number and a unit with &#160;
    content = re.sub(r'(\d+)\s+(cm|kg|in|lb)', r'\1&#160;\2', content)
    content = re.sub(r'(\d+)\s+(W|VA|VAC|Hz|°C|%|ft|m)', r'\1&#160;\2', content)

    # Remove spaces inside <p class=" tags
    content = re.sub(r'(<p class="[^>]*?>)[ \t]+(?!\n)', r'\1', content)

    # Remove spaces inside <li class=" tags
    content = re.sub(r'(<li class="[^>]*?>)\s+', r'\1', content)

    return content
