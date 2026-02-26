import re
from docx import Document

def format_timecode_to_mmss(timecode):
    """Converts a timecode in seconds with fractions (e.g., 19.480000) to (MM:SS)."""
    try:
        time_in_seconds = float(timecode)
        minutes = int(time_in_seconds // 60)
        seconds = int(time_in_seconds % 60)
        return f"({minutes:02}:{seconds:02})"
    except ValueError:
        return None

def process_line(text):
    """Processes a line to replace the timecode with the formatted (MM:SS) format."""
    match = re.search(r"(\d+\.\d+)\s+-->\s+\d+\.\d+", text)
    if match:
        start_timecode = match.group(1)
        formatted_time = format_timecode_to_mmss(start_timecode)
        # Ensure we don't pass None to re.sub
        if formatted_time:
            processed_text = re.sub(r"\d+\.\d+\s+-->\s+\d+\.\d+", formatted_time, text)
            return processed_text
    return text

def process_docx(input_file, output_file):
    """Processes a .docx file, converts timecodes, and writes output to a new file."""
    document = Document(input_file)
    for paragraph in document.paragraphs:
        original_text = paragraph.text
        processed_text = process_line(original_text)
        if processed_text != original_text:
            paragraph.text = processed_text
    document.save(output_file)

def process_vtt(input_file, output_file):
    """Processes a .vtt file to convert timecodes and writes output to a new file."""
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            processed_line = process_line(line)
            outfile.write(processed_line)