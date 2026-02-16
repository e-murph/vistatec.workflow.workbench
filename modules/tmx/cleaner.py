import os
import re
from datetime import datetime

def clean_tmx_files(input_folder, output_folder, char_threshold, tag_threshold, status_callback=None):
    """
    Scans TMX files in input_folder, removes TUs exceeding thresholds,
    and saves the results to output_folder along with a report.
    """
    
    # Regex pattern to capture <tu ...> to </tu> inclusive
    # We use DOTALL to let . match newlines
    tu_pattern = re.compile(r'(<tu(?:\s[^>]*)?>.*?</tu>)', re.DOTALL | re.IGNORECASE)

    # Initialize Report Data
    report_lines = []
    report_lines.append(f"TMX Cleaning Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Settings: Char Limit={char_threshold}, Tag Limit={tag_threshold}")
    report_lines.append("-" * 60)

    total_files_scanned = 0
    total_files_cleaned = 0
    total_tus_removed = 0

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

                def process_tu(match):
                    nonlocal deleted_count
                    tu_block = match.group(1)

                    # Count tags (simple substring counting)
                    tag_count = tu_block.count('<ph') + tu_block.count('<bpt') + \
                                tu_block.count('<ept') + tu_block.count('<it') + \
                                tu_block.count('<x')

                    # Check criteria
                    if len(tu_block) > char_threshold or tag_count > tag_threshold:
                        deleted_count += 1
                        return ''  # Delete block (replace with empty string)
                    else:
                        return tu_block  # Keep block

                # Perform substitution
                new_content = tu_pattern.sub(process_tu, content)

                # Ensure output directory exists
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)

                # Write the file (we write it even if no changes, so user gets a full return package)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                if deleted_count > 0:
                    status = f"[CLEANED] {display_name} -> Removed {deleted_count} TUs"
                    total_files_cleaned += 1
                    total_tus_removed += deleted_count
                else:
                    status = f"[OK] {display_name} -> No issues found"
                
                report_lines.append(status)

            except Exception as e:
                error_msg = f"[ERROR] {display_name} -> {str(e)}"
                report_lines.append(error_msg)

    # Finalize Report
    report_lines.append("-" * 60)
    report_lines.append("SUMMARY:")
    report_lines.append(f"Total Files Scanned: {total_files_scanned}")
    report_lines.append(f"Files Modified:      {total_files_cleaned}")
    report_lines.append(f"Total TUs Removed:   {total_tus_removed}")

    # Write report file
    report_file_path = os.path.join(output_folder, 'cleaning_report.txt')
    with open(report_file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

    return total_files_scanned, total_files_cleaned, total_tus_removed
