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

# tmx_processor.py
# This script contains functions for parsing TMX files, detecting languages,
# and creating a new TMX file by "pivoting" two existing TMX files based on a common language.

import os
import lxml.etree as ET
import re
from fuzzywuzzy import fuzz
import io
from contextlib import redirect_stdout


def parse_tmx(file_path):
    """
    Parses a TMX (Translation Memory eXchange) file and returns its root element.

    Args:
        file_path (str): The path to the TMX file.

    Returns:
        lxml.etree._Element: The root element of the TMX file.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the file is not a valid TMX file or parsing fails.
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"TMX file not found: {file_path}")
        
        # Use a custom XML parser to preserve whitespace and CDATA sections.
        parser = ET.XMLParser(remove_blank_text=False, strip_cdata=False)
        tree = ET.parse(file_path, parser)
        root = tree.getroot()
        
        # Validate that the root element is a TMX tag.
        if root.tag.endswith('tmx'):
            return root
        else:
            raise ValueError(f"Invalid TMX file: {file_path}. Root tag is not 'tmx'.")
            
    except ET.ParseError as e:
        raise ValueError(f"Failed to parse {file_path}: {str(e)}")


def detect_lang_codes_set(root):
    """
    Detects all unique language codes present in the TMX file.

    Args:
        root (lxml.etree._Element): The root element of the TMX file.

    Returns:
        set: A set of unique language codes (e.g., {'en', 'de', 'fr-FR'}).
    """
    langs = set()
    # Iterate through all <tu> (translation unit) and <tuv> (translation unit variant) elements.
    for tu in root.find('body').findall('tu'):
        for tuv in tu.findall('tuv'):
            # The language code is stored in the 'xml:lang' attribute.
            lang = tuv.get('{http://www.w3.org/XML/1998/namespace}lang')
            if lang:
                langs.add(lang)
    return langs


def print_lang_codes(root, file_name):
    """Prints the detected language codes to the console."""
    langs = detect_lang_codes_set(root)
    print(f"Language codes in {os.path.basename(file_name)}: {langs}")


def normalize_seg(seg_xml):
    """
    Normalizes a segment's XML content for consistent matching.
    This involves removing extra whitespace and trimming.

    Args:
        seg_xml (str): The raw XML string of a <seg> element.

    Returns:
        str: The normalized string, or None if the input is None.
    """
    if seg_xml is None:
        return None
    # Replace one or more whitespace characters with a single space.
    seg_xml = re.sub(r'\s+', ' ', seg_xml.strip())
    return seg_xml


def get_seg_xml(tuv):
    """
    Extracts the raw XML content of the <seg> element from a <tuv> element.
    This preserves all original formatting and tags within the segment.

    Args:
        tuv (lxml.etree._Element): The <tuv> element.

    Returns:
        str: The raw XML string of the <seg> element, or None if not found.
    """
    seg = tuv.find('seg')
    if seg is not None:
        # Convert the element to a string, excluding the parent tag.
        raw_xml = ET.tostring(seg, encoding='unicode', method='xml', with_tail=False)
        return raw_xml
    return None


def get_seg_key(tuv):
    """
    Extracts and normalizes the content of the <seg> element for use as a dictionary key.

    Args:
        tuv (lxml.etree._Element): The <tuv> element.

    Returns:
        str: The normalized segment content, or None if not found.
    """
    seg = tuv.find('seg')
    if seg is not None:
        return normalize_seg(ET.tostring(seg, encoding='unicode', method='xml'))
    return None


def create_pivot_tmx(pivot_root, target_root, output_file, target_file, output_target_lang, input_target_lang,
                     pivot_target_lang, pivot_source_lang, output_source_lang, source_file):
    """
    Creates a new TMX file by merging two existing TMX files based on a common "pivot" language.

    The process involves:
    1. Building a dictionary of segments from the 'pivot' TMX file using the common language as keys.
    2. Iterating through the 'target' TMX file and finding matching segments in the pivot dictionary.
    3. Creating new translation units from the matched pairs and adding them to a new TMX structure.
    4. Generating various reports (full, client, and unmatched segments) for the process.
    5. Writing the final pivoted TMX file to disk.
    """
    # Capture all print statements to a buffer for later use in reports.
    console_output = io.StringIO()
    with redirect_stdout(console_output):
        # Define namespaces for easier XML element searching.
        namespaces = {
            'xml': 'http://www.w3.org/XML/1998/namespace',
            'tmx': 'http://www.lisa.org/tmx14'
        }

        print_lang_codes(pivot_root, source_file)
        print_lang_codes(target_root, target_file)

        # Get all translation units from both TMX files.
        pivot_tus = pivot_root.find('body').findall('tu')
        target_tus = target_root.find('body').findall('tu')
        print(f"Total TUs in pivot file: {len(pivot_tus)}")
        print(f"Total TUs in {os.path.basename(target_file)}: {len(target_tus)}")

        # Step 1: Build a dictionary from the pivot TMX file.
        pivot_dict = {}
        pivot_seg_samples = []
        skipped_pivot = 0
        for i, tu in enumerate(pivot_tus):
            # Find the translation unit variant for the common language.
            common_tuv = tu.find(f"tuv[@xml:lang='{pivot_source_lang}']", namespaces=namespaces)
            if common_tuv is None:
                skipped_pivot += 1
                continue
            
            # Use the normalized common segment as the dictionary key.
            seg_key = get_seg_key(common_tuv)
            common_seg_raw = get_seg_xml(common_tuv)
            
            # Find the translation unit variant for the pivot's target language.
            source_tuv = tu.find(f"tuv[@xml:lang='{pivot_target_lang}']", namespaces=namespaces)
            
            # Store the raw source segment, the original translation unit, and the raw common segment.
            if seg_key and source_tuv is not None:
                source_seg_raw = get_seg_xml(source_tuv)
                pivot_dict[seg_key] = (source_seg_raw, tu, common_seg_raw)
                if i < 5:
                    pivot_seg_samples.append(seg_key)
            else:
                skipped_pivot += 1

        print(f"Common segments in pivot file (first 5): {pivot_seg_samples}")
        print(f"Total pivot pairs: {len(pivot_dict)}")
        print(f"Skipped TUs in pivot file (missing {pivot_source_lang}/{pivot_target_lang}/seg): {skipped_pivot}")

        # Step 2 & 3: Match segments and build the new TMX body.
        new_body = ET.Element('body')
        match_count = 0
        target_seg_samples = []
        skipped_target = 0
        unmatched_segments = []
        matched_tus = []
        
        for i, tu in enumerate(target_tus):
            # Find the common language segment in the target TMX.
            common_tuv = tu.find(f"tuv[@xml:lang='{pivot_source_lang}']", namespaces=namespaces)
            if common_tuv is None:
                skipped_target += 1
                continue
            
            # Get the normalized segment key to look up in the pivot dictionary.
            seg_key = get_seg_key(common_tuv)
            if i < 5:
                target_seg_samples.append(seg_key)
            
            # Check for a match in the pivot dictionary.
            if seg_key in pivot_dict:
                source_seg_raw, original_tu, common_seg_pivot = pivot_dict[seg_key]
                target_tuv = tu.find(f"tuv[@xml:lang='{input_target_lang}']", namespaces=namespaces)
                
                if target_tuv is not None:
                    target_seg_raw = get_seg_xml(target_tuv)
                    common_seg_target = get_seg_xml(common_tuv)
                    
                    # Calculate a fuzzy matching confidence score.
                    confidence = fuzz.ratio(common_seg_pivot, common_seg_target)
                    
                    # Create the new <tu> element for the output TMX.
                    new_tu = ET.Element('tu')
                    
                    # Copy attributes and <prop> elements from the original pivot TU.
                    for attr, value in original_tu.attrib.items():
                        new_tu.set(attr, value)
                    for prop in original_tu.findall('prop'):
                        new_tu.append(prop)
                        
                    # Add a new <prop> element for the confidence score.
                    confidence_prop = ET.Element('prop', {'type': 'confidence'})
                    confidence_prop.text = str(confidence)
                    new_tu.append(confidence_prop)

                    # Create the new source <tuv> from the pivot TMX.
                    new_source_tuv = ET.Element('tuv')
                    new_source_tuv.set('{http://www.w3.org/XML/1998/namespace}lang', output_source_lang)
                    source_seg_element = ET.fromstring(source_seg_raw)
                    new_source_tuv.append(source_seg_element)

                    # Create the new target <tuv> from the target TMX.
                    new_target_tuv = ET.Element('tuv')
                    new_target_tuv.set('{http://www.w3.org/XML/1998/namespace}lang', output_target_lang)
                    target_seg_element = ET.fromstring(target_seg_raw)
                    new_target_tuv.append(target_seg_element)
                    
                    # Append the new TUVs to the new TU.
                    new_tu.append(new_source_tuv)
                    new_tu.append(new_target_tuv)
                    new_body.append(new_tu)
                    match_count += 1
                    
                    # Store information about the matched TU for the report.
                    matched_tus.append({
                        'common_seg': common_seg_pivot,
                        'source_seg': source_seg_raw,
                        'target_seg': target_seg_raw,
                        'confidence': confidence
                    })
            else:
                # Store unmatched segments for the report.
                if seg_key and i < 100:
                    unmatched_segments.append(seg_key)

        print(f"Common segments in {os.path.basename(target_file)} (first 5): {target_seg_samples}")
        print(f"Total matches found: {match_count}")
        print(
            f"Skipped TUs in {os.path.basename(target_file)} (missing {pivot_source_lang}/{input_target_lang}/seg): {skipped_target}")
        
        # Write the list of unmatched segments to a text file.
        if unmatched_segments:
            unmatched_file = os.path.join(os.path.dirname(output_file),
                                          f"unmatched_segments_{os.path.basename(output_file).replace('.tmx', '')}.txt")
            with open(unmatched_file, 'w', encoding='utf-8') as f:
                f.write(f"Unmatched common segments from {os.path.basename(target_file)} (first 100):\n")
                for seg in unmatched_segments:
                    f.write(f"{seg}\n")
            print(f"Wrote unmatched segments to {os.path.basename(unmatched_file)}")

    # Filter console output for client report
    client_console_output = "\n".join(
        line for line in console_output.getvalue().splitlines()
        if not any(phrase in line.lower() for phrase in [
            "common segments in pivot file (first 5):",
            "total pivot pairs:",
            "skipped tus in pivot file",
            "common segments in",
            "skipped tus in"
        ])
    )

    # Create main report
    report_file = os.path.join(os.path.dirname(output_file),
                               f"report_{os.path.basename(output_file).replace('.tmx', '')}.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=== TMX Pivot Report ===\n")
        f.write(f"Output File: {os.path.basename(output_file)}\n")
        f.write(f"Target Language: {output_target_lang}\n")
        f.write("\n=== Console Output ===\n")
        f.write(console_output.getvalue())
        f.write("\n=== Matched Translation Units ===\n")
        if matched_tus:
            for i, tu in enumerate(matched_tus, 1):
                f.write(f"\nTU {i}:\n")
                f.write(f"Confidence Score: {tu['confidence']}%\n")
                f.write(f"Common Source Segment ({pivot_source_lang}): {tu['common_seg']}\n")
                f.write(f"Output Source Segment ({output_source_lang}): {tu['source_seg']}\n")
                f.write(f"Target Segment ({output_target_lang}): {tu['target_seg']}\n")
        else:
            f.write("No matched TUs found.\n")
    print(f"Wrote report to {os.path.basename(report_file)}")
    
    # Create the client-facing report file (less technical details).
    client_report_file = os.path.join(os.path.dirname(output_file),
                                      f"client_report_{os.path.basename(output_file).replace('.tmx', '')}.txt")
    with open(client_report_file, 'w', encoding='utf-8') as f:
        f.write("=== TMX Client Report ===\n")
        f.write(f"Output File: {os.path.basename(output_file)}\n")
        f.write(f"Target Language: {output_target_lang}\n")
        f.write("\n=== Console Output ===\n")
        f.write(client_console_output)
        f.write("\n=== Matched Translation Units ===\n")
        if matched_tus:
            for i, tu in enumerate(matched_tus, 1):
                f.write(f"\nTU {i}:\n")
                f.write(f"Common Source Segment ({pivot_source_lang}): {tu['common_seg']}\n")
                f.write(f"Output Source Segment ({output_source_lang}): {tu['source_seg']}\n")
                f.write(f"Target Segment ({output_target_lang}): {tu['target_seg']}\n")
        else:
            f.write("No matched TUs found.\n")
    print(f"Wrote client report to {os.path.basename(client_report_file)}")

    # Step 5: Write the final TMX file.
    # Manually construct the XML string to ensure correct formatting and headers.
    xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_str += '<tmx version="1.4">\n'
    xml_str += f'  <header creationtool="TMX Aligner" creationtoolversion="1.0" segtype="sentence" o-tmf="TMX" adminlang="en" srclang="{output_source_lang}" datatype="plaintext"/>\n'
    xml_str += '  <body>\n'

    for tu in new_body.findall('tu'):
        tu_str = '    <tu'
        for attr, value in tu.attrib.items():
            tu_str += f' {attr}="{value}"'
        tu_str += '>\n'
        for prop in tu.findall('prop'):
            prop_str = ET.tostring(prop, encoding='unicode', method='xml')
            tu_str += f'      {prop_str}\n'
        for tuv in tu.findall('tuv'):
            lang = tuv.get('{http://www.w3.org/XML/1998/namespace}lang')
            seg = tuv.find('seg')
            # Use ET.tostring to get the segment's content as a string.
            seg_str = ET.tostring(seg, encoding='unicode', method='xml', with_tail=False)
            tu_str += f'      <tuv xml:lang="{lang}">\n'
            tu_str += f'        {seg_str}\n'
            tu_str += '      </tuv>\n'
        tu_str += '    </tu>\n'
        xml_str += tu_str
        
    xml_str += '  </body>\n'
    xml_str += '</tmx>'

    # Ensure the output directory exists before writing the file.
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(xml_str)
        
    print(f"New TMX created: {os.path.basename(output_file)} with {match_count} TUs")
    console_output.close()
