import os
import re
import xml.etree.ElementTree as ET
import openpyxl
from openpyxl.styles import Font, Alignment

# IMPORT THE NEW AI MODULE
from modules.termweb.termweb_ai import batch_ai_term_review

def get_languages(root):
    """Scans the XML to find the first two unique language codes."""
    langs = []
    for termEntry in root.iter('termEntry'):
        for langSet in termEntry.findall('langSet'):
            lang = langSet.get('{http://www.w3.org/XML/1998/namespace}lang')
            if lang and lang not in langs:
                langs.append(lang)
        if len(langs) >= 2:
            break

    lang1 = langs[0] if len(langs) > 0 else 'Language_1'
    lang2 = langs[1] if len(langs) > 1 else 'Language_2'
    return lang1, lang2


def align_terms(list1, list2):
    """
    Aligns list2 to match list1 and calculates a percentage accuracy score.
    Applies a THREE-TIER lexical matching "magnet" to short forms/acronyms to
    prioritize case-sensitive matches over case-insensitive and normalized matches.
    """
    aligned_list2 = [None] * len(list1)

    def get_match_scores(t1, t2):
        qa_score = 0

        # 1. Administrative Status Match
        t1_status = t1.get('admin_status', '')
        t2_status = t2.get('admin_status', '')
        if t1_status == t2_status and t1_status != '':
            qa_score += 20

        # 2. Term Type Match
        t1_type = t1.get('term_type', '')
        t2_type = t2.get('term_type', '')
        SHORT_TYPES = {'abbreviation', 'shortForm', 'acronym'}

        if t1_type == t2_type and t1_type != '':
            qa_score += 10
        elif t1_type in SHORT_TYPES and t2_type in SHORT_TYPES:
            if t1_type == 'abbreviation' and t2_type == 'acronym':
                qa_score += 8
            else:
                qa_score += 6

        alignment_score = qa_score

        # 3. Three-Tier Lexical String Match (RESTRICTED TO SHORT TYPES ONLY)
        if t1_type in SHORT_TYPES and t2_type in SHORT_TYPES:
            t1_exact = t1.get('term', '').strip()
            t2_exact = t2.get('term', '').strip()

            t1_lower = t1_exact.lower()
            t2_lower = t2_exact.lower()

            t1_norm = re.sub(r'[\W_]+', '', t1_lower)
            t2_norm = re.sub(r'[\W_]+', '', t2_lower)

            if t1_exact == t2_exact and t1_exact != '':
                qa_score += 5
                alignment_score += 200  # ULTIMATE MAGNET: Case-sensitive exact (SSH == SSH)
            elif t1_lower == t2_lower and t1_lower != '':
                qa_score += 5
                alignment_score += 150  # SUPER MAGNET: Case-insensitive (SSH == Ssh)
            elif t1_norm == t2_norm and t1_norm != '':
                qa_score += 5
                alignment_score += 100  # REGULAR MAGNET: Normalized match (hotplugging == Hot-Plugging)

        return alignment_score, qa_score

    matches = []
    for i, t1 in enumerate(list1):
        for j, t2 in enumerate(list2):
            align_score, qa_score = get_match_scores(t1, t2)
            if align_score > 0:
                matches.append((align_score, qa_score, i, j))

    # Sort by ALIGNMENT SCORE.
    # Distance penalty (-abs(x[2] - x[3])) resolves ties by preserving original tig id sequence.
    matches.sort(key=lambda x: (x[0], -abs(x[2] - x[3]), -x[2], -x[3]), reverse=True)

    used_t1 = set()
    used_t2 = set()

    for align_score, qa_score, i, j in matches:
        if i not in used_t1 and j not in used_t2:
            pct = int(round((qa_score / 30.0) * 100))
            if pct > 100: pct = 100
            aligned_list2[i] = (list2[j], pct)
            used_t1.add(i)
            used_t2.add(j)

    for i in range(len(aligned_list2)):
        if aligned_list2[i] is None:
            filled = False
            for j in range(len(list2)):
                if j not in used_t2:
                    aligned_list2[i] = (list2[j], 0)
                    used_t2.add(j)
                    filled = True
                    break
            if not filled:
                aligned_list2[i] = (None, 0)

    for j in range(len(list2)):
        if j not in used_t2:
            aligned_list2.append((list2[j], 0))

    return aligned_list2


def get_tig_num(item):
    """Extracts numeric value from tig id to sort perfectly sequentially"""
    tid = item.get('tig_id', '')
    parts = tid.split('-')
    if len(parts) > 1 and parts[-1].isdigit():
        return int(parts[-1])
    return 999999

# --- AI ADD-ON: Added enable_ai parameter ---
def parse_xml_to_xlsx(xml_file, out_dir, enable_ai=False):
    """Parses a TermWeb XML file and generates multiple QA Excel reports."""
    filename = os.path.basename(xml_file)
    base_name = os.path.splitext(filename)[0]

    # Output file paths
    full_xlsx_path = os.path.join(out_dir, f"{base_name}_full.xlsx")
    filtered_xlsx_path = os.path.join(out_dir, f"{base_name}_excl_notRecommended.xlsx")
    preferred_xlsx_path = os.path.join(out_dir, f"{base_name}_only_preferred.xlsx")
    perfect_xlsx_path = os.path.join(out_dir, f"{base_name}_perfect_100.xlsx")
    imperfect_xlsx_path = os.path.join(out_dir, f"{base_name}_under_100.xlsx")
    missing_xlsx_path = os.path.join(out_dir, f"{base_name}_missing_target.xlsx")

    tree = ET.parse(xml_file)
    root = tree.getroot()

    lang1, lang2 = get_languages(root)

    # --- AI ADD-ON: Added 'AI Notes' to headers ---
    headers = [
        'termEntry id',
        lang1, 'tig id', 'administrativeStatus', 'termType',
        lang2, 'tig id', 'administrativeStatus', 'termType',
        'definition', 'Accuracy Score', 'AI Notes'
    ]

    def extract_rows(filter_mode='none'):
        rows = []
        for termEntry in root.iter('termEntry'):
            entry_id = termEntry.get('id', '')

            definition = ''
            for desc in termEntry.findall('descrip'):
                if desc.get('type') == 'definition':
                    definition = desc.text or ''

            lang_data = {lang1: [], lang2: []}

            for langSet in termEntry.findall('langSet'):
                l = langSet.get('{http://www.w3.org/XML/1998/namespace}lang')
                if l not in lang_data:
                    continue

                for tig in langSet.findall('tig'):
                    tig_id = tig.get('id', '')
                    term = ''
                    term_elem = tig.find('term')
                    if term_elem is not None:
                        term = term_elem.text or ''

                    admin_status = ''
                    term_type = ''
                    for termNote in tig.findall('termNote'):
                        if termNote.get('type') == 'administrativeStatus':
                            admin_status = termNote.text or ''
                        elif termNote.get('type') == 'termType':
                            term_type = termNote.text or ''

                    # COMBINED FILTERS:
                    if filter_mode in ['exclude_not_recommended',
                                       'imperfect_match'] and admin_status == 'notRecommended':
                        continue
                    if filter_mode in ['only_preferred', 'perfect_match'] and admin_status != 'preferred':
                        continue

                    if filter_mode == 'missing_target':
                        if l == lang1 and admin_status != 'preferred':
                            continue

                    lang_data[l].append({
                        'term': term,
                        'tig_id': tig_id,
                        'admin_status': admin_status,
                        'term_type': term_type
                    })

            list1 = lang_data[lang1]
            raw_list2 = lang_data[lang2]

            # Filter Check for the 6th Output:
            if filter_mode == 'missing_target':
                if len(raw_list2) > 0 or len(list1) == 0:
                    continue

            list1.sort(key=get_tig_num)
            raw_list2.sort(key=get_tig_num)

            # Align lists and grab the accuracy scores
            list2_aligned = align_terms(list1, raw_list2)
            max_len = max(len(list1), len(list2_aligned))

            # Check if this specific entry is a "Perfect Match"
            entry_perfect = True
            if len(list1) != len(raw_list2) or max_len == 0:
                entry_perfect = False
            else:
                for t2_item, score in list2_aligned:
                    if score < 100:
                        entry_perfect = False
                        break

            # Filter for the 100% / <100% lists
            if filter_mode == 'perfect_match' and not entry_perfect:
                continue
            if filter_mode == 'imperfect_match' and entry_perfect:
                continue

            if max_len == 0:
                # --- AI ADD-ON: Added extra blank space for AI column ---
                rows.append([entry_id, '', '', '', '', '', '', '', '', definition, '', ''])
                continue

            for i in range(max_len):
                row = [entry_id if i == 0 else '']

                # First language data
                if i < len(list1) and list1[i]:
                    row.extend([list1[i]['term'], list1[i]['tig_id'], list1[i]['admin_status'], list1[i]['term_type']])
                else:
                    row.extend(['', '', '', ''])

                # Second language data + Score unpacking
                t2_tuple = list2_aligned[i] if i < len(list2_aligned) else (None, 0)
                if t2_tuple[0]:
                    t2_term = t2_tuple[0]
                else:
                    t2_term = None
                    
                match_score = t2_tuple[1]

                if t2_term:
                    row.extend([t2_term['term'], t2_term['tig_id'], t2_term['admin_status'], t2_term['term_type']])
                else:
                    row.extend(['', '', '', ''])

                row.append(definition if i == 0 else '')

                if i < len(list1) or t2_term:
                    row.append(f"{match_score}%")
                else:
                    row.append("")
                    
                # --- AI ADD-ON: Append blank placeholder for AI Notes ---
                row.append("")

                rows.append(row)

        return rows

    def write_to_excel(filepath, filter_mode):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "TermWeb Data"

        ws.append(headers)

        data_rows = extract_rows(filter_mode)
        if not data_rows and filter_mode in ['perfect_match', 'imperfect_match', 'missing_target']:
            return

        # --- AI ADD-ON: Intercept the data and run the AI batch before writing to Excel ---
        if enable_ai and filter_mode in ['imperfect_match', 'none', 'missing_target']:
            ai_batch = []
            row_map = {} # Map global batch index to actual Excel row index
            
            # 1. Gather ALL rows that need AI review (No more 50 limit!)
            for r_idx, row in enumerate(data_rows):
                t1, t2, missing_def = row[1], row[5], (not row[9].strip())
                score_str = row[10].replace('%', '') if isinstance(row[10], str) else str(row[10])
                score = int(score_str) if score_str.isdigit() else 100
                
                if (score < 100 and t1 and t2) or (t1 and missing_def):
                    row_map[str(len(ai_batch))] = r_idx
                    ai_batch.append({'t1': t1, 't2': t2, 'missing_def': missing_def})
            
            # 2. Process them in safe chunks of 50 to prevent API timeouts/truncation
            if ai_batch:
                chunk_size = 50
                for i in range(0, len(ai_batch), chunk_size):
                    chunk = ai_batch[i:i + chunk_size]
                    
                    # Send this specific chunk to Gemini
                    ai_insights = batch_ai_term_review(chunk, lang1, lang2)
                    
                    # Map the local chunk answers back to the global Excel rows
                    for local_id, insight in ai_insights.items():
                        global_id = str(i + int(local_id))
                        if global_id in row_map:
                            actual_row_idx = row_map[global_id]
                            data_rows[actual_row_idx][11] = insight # Add to AI Notes column
        # --- END AI ADD-ON ---

        for row in data_rows:
            ws.append(row)

        bold_font = Font(bold=True)
        no_wrap_alignment = Alignment(wrap_text=False)

        for cell in ws[1]:
            cell.font = bold_font

        for col in ws.columns:
            max_length = 0
            column_letter = col[0].column_letter
            for cell in col:
                cell.alignment = no_wrap_alignment
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            ws.column_dimensions[column_letter].width = (max_length + 2)

        wb.save(filepath)

    write_to_excel(full_xlsx_path, filter_mode='none')
    write_to_excel(filtered_xlsx_path, filter_mode='exclude_not_recommended')
    write_to_excel(preferred_xlsx_path, filter_mode='only_preferred')
    write_to_excel(perfect_xlsx_path, filter_mode='perfect_match')
    write_to_excel(imperfect_xlsx_path, filter_mode='imperfect_match')
    write_to_excel(missing_xlsx_path, filter_mode='missing_target')