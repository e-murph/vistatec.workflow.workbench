import xml.etree.ElementTree as ET
import pandas as pd
import os
import logging

# Helper to extract the xml:lang attribute
def get_xml_lang(element):
    namespace = '{http://www.w3.org/XML/1998/namespace}'
    lang = element.attrib.get(f'{namespace}lang')
    if lang is None:
        lang = element.attrib.get('lang')
    return lang

# Generates a valid TMX XML tree including creation metadata
def create_tmx_structure(source_lang, target_lang, segments):
    tmx_root = ET.Element('tmx', version="1.4")
    
    header = ET.SubElement(tmx_root, 'header', {
        'creationtool': 'VistatecUtilityHub',
        'creationtoolversion': '1.0',
        'segtype': 'sentence',
        'o-tmf': 'ATM',
        'adminlang': 'en-US',
        'srclang': source_lang,
        'datatype': 'plaintext'
    })

    body = ET.SubElement(tmx_root, 'body')

    for src_txt, tgt_txt, c_date, c_id in segments:
        tu = ET.SubElement(body, 'tu')

        # --- Source TUV ---
        tuv_src = ET.SubElement(tu, 'tuv', {
            '{http://www.w3.org/XML/1998/namespace}lang': source_lang
        })
        seg_src = ET.SubElement(tuv_src, 'seg')
        seg_src.text = str(src_txt) if src_txt else ""

        # --- Target TUV ---
        tgt_attrs = {'{http://www.w3.org/XML/1998/namespace}lang': target_lang}
        if c_date: tgt_attrs['creationdate'] = c_date
        if c_id: tgt_attrs['creationid'] = c_id

        tuv_tgt = ET.SubElement(tu, 'tuv', tgt_attrs)
        seg_tgt = ET.SubElement(tuv_tgt, 'seg')
        seg_tgt.text = str(tgt_txt) if tgt_txt else ""

    return ET.ElementTree(tmx_root)

# Main Processing Function adapted for Streamlit
def process_multilingual_tmx(file_path, output_dir, status_callback=None):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        if status_callback: status_callback("Parsing TMX structure...")
        
        # Parse XML
        # Note: For huge files, iterparse is better, but keeping simple for now
        tree = ET.parse(file_path)
        root = tree.getroot()
        body = root.find('body')

        if body is None:
            raise ValueError("Invalid TMX structure (no <body> tag found).")

        pair_groups = {}
        processed_count = 0
        skipped_count = 0

        # Iterate through TUs
        for tu in body.findall('tu'):
            tuvs = tu.findall('tuv')

            if len(tuvs) < 2:
                skipped_count += 1
                continue

            # Assume first TUV is source
            source_tuv = tuvs[0]
            source_lang = get_xml_lang(source_tuv) or "unknown-source"
            source_seg = source_tuv.find('seg')
            source_text = source_seg.text if source_seg is not None else ""

            # Iterate Targets
            for target_tuv in tuvs[1:]:
                target_lang = get_xml_lang(target_tuv) or "MISSING_LANG"
                target_seg = target_tuv.find('seg')
                target_text = target_seg.text if target_seg is not None else ""
                
                # Metadata
                c_date = target_tuv.attrib.get('creationdate', '')
                c_id = target_tuv.attrib.get('creationid', '')

                # Grouping Key
                pair_key = (source_lang, target_lang)

                if pair_key not in pair_groups:
                    pair_groups[pair_key] = []

                pair_groups[pair_key].append((source_text, target_text, c_date, c_id))
                processed_count += 1

        if status_callback: status_callback(f"Found {len(pair_groups)} language pairs. Generating files...")

        # Output Generation
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        generated_files = []

        for (src_lang, tgt_lang), data_list in pair_groups.items():
            safe_src = str(src_lang).replace(':', '_').replace('/', '_')
            safe_tgt = str(tgt_lang).replace(':', '_').replace('/', '_')
            filename_suffix = f"{safe_src}_to_{safe_tgt}"
            
            # 1. Generate CSV
            df = pd.DataFrame(data_list, columns=['Source Text', 'Target Text', 'Creation Date', 'Creation ID'])
            df.insert(0, 'Source Lang', src_lang)
            df.insert(2, 'Target Lang', tgt_lang)

            csv_name = f"{base_name}_{filename_suffix}.csv"
            csv_path = os.path.join(output_dir, csv_name)
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            generated_files.append(csv_name)

            # 2. Generate TMX
            tmx_tree = create_tmx_structure(src_lang, tgt_lang, data_list)
            tmx_name = f"{base_name}_{filename_suffix}.tmx"
            tmx_path = os.path.join(output_dir, tmx_name)
            tmx_tree.write(tmx_path, encoding='UTF-8', xml_declaration=True)
            generated_files.append(tmx_name)

        return processed_count, len(pair_groups)

    except ET.ParseError as e:
        raise ValueError(f"XML Parsing Error: {e}")
    except Exception as e:
        raise Exception(f"Critical error: {e}")