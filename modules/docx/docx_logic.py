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

# docx_logic.py
# Handles XML parsing, text cleaning, sentence segmentation, and HTML generation.

import zipfile
import re
import hashlib  # <--- NEW: Needed for ID generation
import html as html_lib
from datetime import datetime  # <--- NEW: Needed for timestamp
from lxml import etree
from .html_templates import get_html_template

# XML Namespace for Word Documents
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


class DiffSegment:
    """Helper class to store a piece of text and its tracked-change status."""

    def __init__(self, text, type="normal"):
        self.text = text
        self.type = type  # options: 'normal', 'ins' (inserted), 'del' (deleted)


def clean_text(text: str) -> str:
    """Removes invisible control characters that can break XML parsing."""
    if not text: return ""
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)


def split_text_with_indices(text: str):
    """
    Splits a string into a list of sentences.
    Supports both Japanese (。！？) and English (.!?) punctuation.
    """
    if not text:
        return []
    # Regex looks for punctuation marks to split by
    pattern = r'(?<=[。！？])|(?<=[.!?])\s+'
    parts = re.split(pattern, text)
    sentences = [p for p in parts if p]
    return sentences


def slice_segments(segments, sentences):
    """
    Complex logic to align XML segments (which might be half a sentence) 
    to the detected sentence boundaries.
    """
    sliced_groups = []
    current_group = []
    current_sent_idx = 0

    # Cursor position in the current sentence (counting 'normal' and 'ins' only)
    sent_cursor = 0

    # Flag to indicate we have filled the visual text of the current sentence
    # but are waiting to see if 'del' tags follow.
    sentence_filled = False

    if not sentences:
        return [segments]

    target_length = len(sentences[0])

    for seg in segments:
        text = seg.text
        type_ = seg.type

        # --- HANDLE DELETIONS ---
        # Deletions are invisible in the final sentence. 
        # Always append them to the current group, even if the sentence is "filled".
        if type_ == 'del':
            current_group.append(seg)
            continue

        # --- HANDLE NEW TEXT (Normal / Ins) ---

        # If we previously filled the sentence, and we just hit NEW text,
        # NOW we close the old group and start the new one.
        if sentence_filled:
            sliced_groups.append(current_group)
            current_group = []
            sent_cursor = 0
            sentence_filled = False
            current_sent_idx += 1
            if current_sent_idx < len(sentences):
                target_length = len(sentences[current_sent_idx])
            else:
                target_length = 9999999

        # Process the current text segment
        while text:
            remaining_len = target_length - sent_cursor

            if len(text) <= remaining_len:
                # Case A: The segment fits entirely within the current sentence
                current_group.append(DiffSegment(text, type_))
                sent_cursor += len(text)
                text = ""  # Consumed

                # Check if this exact segment finished the sentence
                if sent_cursor == target_length:
                    # DO NOT split immediately. Set flag and wait for next iteration
                    # in case a 'del' tag follows.
                    sentence_filled = True

            else:
                # Case B: The segment crosses the boundary (needs splitting)
                # If we are splitting a single text node, we MUST close the group
                # immediately after the first part, because a 'del' cannot exist
                # *inside* a single text node.

                part1 = text[:remaining_len]
                part2 = text[remaining_len:]

                # 1. Finish current sentence
                current_group.append(DiffSegment(part1, type_))
                sliced_groups.append(current_group)

                # 2. Setup for next sentence
                current_group = []
                sent_cursor = 0
                current_sent_idx += 1
                if current_sent_idx < len(sentences):
                    target_length = len(sentences[current_sent_idx])
                else:
                    target_length = 9999999

                # 3. Continue loop with remainder
                text = part2
                # Since we just started a new group with part2, sentence_filled is False
                sentence_filled = False

    # Append whatever is left
    if current_group:
        sliced_groups.append(current_group)

    return sliced_groups


def segments_to_html(segments):
    """Converts a list of DiffSegments into HTML with color coding."""
    html_parts = []
    for seg in segments:
        text = html_lib.escape(seg.text)
        if seg.type == 'del':
            html_parts.append(f'<span class="del">{text}</span>')
        elif seg.type == 'ins':
            html_parts.append(f'<span class="ins">{text}</span>')
        else:
            html_parts.append(f'<span>{text}</span>')
    return "".join(html_parts)


def extract_sentence_diffs(docx_path):
    """
    Main Logic Function:
    1. Opens DOCX as Zip.
    2. Parses document.xml.
    3. Extracts Tracked Changes (<w:ins>, <w:del>).
    4. Reconstructs sentences and aligns changes to them.
    """
    results = []
    try:
        with zipfile.ZipFile(docx_path) as z:
            xml_content = z.read("word/document.xml")
    except KeyError:
        return []

    root = etree.fromstring(xml_content)

    for para in root.xpath("//w:p", namespaces=NS):
        raw_segments = []
        # Flatten paragraph into linear segments
        for node in para.iter():
            tag = etree.QName(node).localname
            if tag == "delText":
                text = clean_text(node.text)
                if text: raw_segments.append(DiffSegment(text, "del"))
            elif tag == "t":
                parent = node.getparent()
                is_inserted = False
                # Check parents to see if text is inside an insertion tag
                while parent is not None and parent != para:
                    if etree.QName(parent).localname == "ins":
                        is_inserted = True
                        break
                    parent = parent.getparent()
                text = clean_text(node.text)
                if text:
                    seg_type = "ins" if is_inserted else "normal"
                    raw_segments.append(DiffSegment(text, seg_type))

        if not raw_segments: continue

        # Reconstruct "Edited" text to find sentence boundaries
        edit_text_full = "".join([s.text for s in raw_segments if s.type in ('normal', 'ins')])
        sentences = split_text_with_indices(edit_text_full)

        if not sentences:
            grouped_segments = [raw_segments]
        else:
            grouped_segments = slice_segments(raw_segments, sentences)

        # Process each sentence group
        for group in grouped_segments:
            orig_text = "".join([s.text for s in group if s.type in ('normal', 'del')])
            edit_text = "".join([s.text for s in group if s.type in ('normal', 'ins')])

            # Skip empty or identical rows
            if not orig_text.strip() and not edit_text.strip(): continue
            if orig_text == edit_text: continue

            html_display = segments_to_html(group)
            results.append((orig_text, edit_text, html_display))

    return results


def create_html_report(all_changes):
    """
    Orchestrates the creation of the HTML string.
    1. Generates the table rows from the changes list.
    2. Adds IDs and Timestamps.
    3. Calls get_html_template to wrap it all up.
    """
    html_rows = ""
    row_counter = 1

    # Iterate through the combined list of changes
    for filename, orig, edit, html_diff in all_changes:
        # Create a unique hash for the row (for localstorage saving)
        # Using SHA256 for better compliance
        row_id_raw = f"{filename}_{orig[:50]}_{row_counter}"
        row_hash = hashlib.sha256(row_id_raw.encode('utf-8')).hexdigest()

        # Build the HTML row
        html_rows += f'''
        <tr data-id="{row_hash}">
            <td class="status-cell"><input type="checkbox" onchange="updateStatus(this)"></td>
            <td class="id-cell">{row_counter}</td>
            <td class="meta">{html_lib.escape(filename)}</td>
            <td class="content">{html_lib.escape(orig)}</td>
            <td class="content">{html_lib.escape(edit)}</td>
            <td class="content">{html_diff}</td>
            <td><textarea oninput="updateComment(this)"></textarea></td>
        </tr>
        '''
        row_counter += 1

    # Get current timestamp for the report header
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Combine rows with the main template
    return get_html_template(html_rows, timestamp)
