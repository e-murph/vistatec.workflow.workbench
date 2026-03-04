import os
import re
from datetime import datetime
from modules.tmx.tmx_qe_ai import batch_ai_qe_review

def clean_tmx_files(input_folder, output_folder, char_threshold, tag_threshold, status_callback=None, enable_ai=False):
    """
    Scans TMX files in input_folder, removes TUs exceeding thresholds (and optionally 
    uses AI to remove semantic failures), and saves the results to output_folder.
    """
    
    # Regex patterns
    tu_pattern = re.compile(r'(<tu(?:\s[^>]*)?>.*?</tu>)', re.DOTALL | re.IGNORECASE)
    # Pattern to extract text inside <seg> tags for the AI to read
    seg_pattern = re.compile(r'<seg[^>]*>(.*?)</seg>', re.DOTALL | re.IGNORECASE)

    # Initialize Report Data
    report_lines = []
    report_lines.append(f"TMX Cleaning Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Settings: Char Limit={char_threshold}, Tag Limit={tag_threshold}, AI QE={enable_ai}")
    report_lines.append("-" * 60)

    total_files_scanned = 0
    total_files_cleaned = 0
    total_tus_removed = 0
    total_ai_removals = 0

    # Walk through folders
    for current_root, dirs, files in os.walk(input_folder):
        for filename in files:
            if not filename.lower().endswith('.tmx'):
                continue

            total_files_scanned += 1
            input_path = os.path.join(current_root, filename)

            # Calculate output paths (maintain subdirectory structure)
            relative_path = os.path.relpath(current_root, input_folder)
            target_dir = os.path.join(output_folder, relative_path)
            output_path = os.path.join(target_dir, filename)
            
            # Display name for logs/status
            display_name = filename if relative_path == '.' else os.path.join(relative_path, filename)

            if status_callback:
                status_callback(f"Scanning: {display_name}")

            try:
                # Read file content
                with open(input_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                deleted_count = 0
                ai_deleted_count = 0
                
                # --- PASS 1: GATHER & ANALYZE ---
                tu_matches = list(tu_pattern.finditer(content))
                tu_decisions = [] # True = Keep, False = Remove
                
                ai_batch = []
                row_map = {} # Maps ai_batch index to the master tu_matches index

                for idx, match in enumerate(tu_matches):
                    tu_block = match.group(1)

                    # 1. Mechanical Checks (Tags & Length)
                    tag_count = tu_block.count('<ph') + tu_block.count('<bpt') + \
                                tu_block.count('<ept') + tu_block.count('<it') + \
                                tu_block.count('<x')

                    if len(tu_block) > char_threshold or tag_count > tag_threshold:
                        tu_decisions.append(False) # Mark for removal
                        deleted_count += 1
                    else:
                        tu_decisions.append(True) # Default Keep
                        
                        # 2. AI Semantic Check (if enabled)
                        if enable_ai:
                            segs = seg_pattern.findall(tu_block)
                            if len(segs) >= 2:
                                # Strip inner XML tags so AI just reads pure text
                                src_text = re.sub(r'<[^>]+>', '', segs[0]).strip()
                                tgt_text = re.sub(r'<[^>]+>', '', segs[1]).strip()
                                
                                if src_text and tgt_text:
                                    row_map[str(len(ai_batch))] = idx
                                    ai_batch.append({'source': src_text, 'target': tgt_text})

                # --- AI BATCH PROCESSING ---
                if enable_ai and ai_batch:
                    if status_callback:
                        status_callback(f"🤖 Running AI Quality Estimation on {len(ai_batch)} segments in {display_name}...")
                    
                    chunk_size = 50
                    for i in range(0, len(ai_batch), chunk_size):
                        chunk = ai_batch[i:i + chunk_size]
                        
                        # Send chunk to Gemini
                        ai_insights = batch_ai_qe_review(chunk)
                        
                        # Apply AI verdicts back to our decision list
                        for local_id, insight in ai_insights.items():
                            global_id = str(i + int(local_id))
                            if global_id in row_map:
                                actual_idx = row_map[global_id]
                                action = insight.get('action', 'Keep')
                                
                                if action == 'Remove':
                                    tu_decisions[actual_idx] = False
                                    deleted_count += 1
                                    ai_deleted_count += 1
                                    
                                    # Optional: Log the AI's reason to the report
                                    reason = insight.get('reason', 'AI flagged as poor quality.')
                                    report_lines.append(f"  [AI REMOVED] File: {display_name} | Reason: {reason}")

                # --- PASS 2: SUBSTITUTE ---
                current_tu_idx = 0
                
                def process_tu(match):
                    nonlocal current_tu_idx
                    # Look up the decision we made in Pass 1
                    decision = tu_decisions[current_tu_idx]
                    current_tu_idx += 1
                    
                    if decision:
                        return match.group(1) # Keep
                    else:
                        return '' # Delete

                # Perform substitution
                new_content = tu_pattern.sub(process_tu, content)

                # Ensure output directory exists
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)

                # Write the file
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                if deleted_count > 0:
                    status_text = f"[CLEANED] {display_name} -> Removed {deleted_count} TUs"
                    if enable_ai:
                        status_text += f" ({ai_deleted_count} by AI)"
                        
                    total_files_cleaned += 1
                    total_tus_removed += deleted_count
                    total_ai_removals += ai_deleted_count
                else:
                    status_text = f"[OK] {display_name} -> No issues found"
                
                report_lines.append(status_text)

            except Exception as e:
                error_msg = f"[ERROR] {display_name} -> {str(e)}"
                report_lines.append(error_msg)

    # Finalize Report
    report_lines.append("-" * 60)
    report_lines.append("SUMMARY:")
    report_lines.append(f"Total Files Scanned: {total_files_scanned}")
    report_lines.append(f"Files Modified:      {total_files_cleaned}")
    report_lines.append(f"Total TUs Removed:   {total_tus_removed}")
    if enable_ai:
        report_lines.append(f"  ↳ Removed by AI:   {total_ai_removals}")

    # Write report file
    report_file_path = os.path.join(output_folder, 'cleaning_report.txt')
    with open(report_file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

    return total_files_scanned, total_files_cleaned, total_tus_removed