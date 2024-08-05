'''
* PROGRAM NAME: RTF TO JSON CONVERTOR
* VERSION AND DATE: 2.1 04-08-2024
* AUTHOR NAME(s): Shreeja Katama

* LANGUAGE AND LIBRARY REFERENCE: Python3,
Python Standard Libraries:
  - json
  - re
  - os
  - tkinter

* PURPOSE: Processes RTF files to extract basic data and convert it to JSON format. Includes dynamic extraction using control words and robust error handling.
* PARAMETERS: Folder containing RTF files as an input parameter.
* RETURNS: JSON outputs saved in a new directory.
* FUNCTION CALL NAME(s): rtf_to_json
* FUNCTION PURPOSE: Extracts data from RTF files and converts it to JSON format.
* EMBEDDED PROGRAMS: None
* MODULE: rtf_to_json.py

* COPY RIGHT: M/s CARE2DATA 2024  All Rights Reserved
**************************************************************************************************************************

* VERSION HISTORY

* REVISED VERSION AND DATE: 1.0.0 01-07-2024
* AUTHOR NAME(s): Shreeja Katama

* CHANGE REASON: Initial Version

* REVISED VERSION AND DATE: 1.2.4 31-07-2024
* AUTHOR NAME(s): Shreeja Katama

* CHANGE REASON: Updates and improvements
'''
import json
import re
import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from configparser import ConfigParser

# Global debugging flag
DEBUG = True
OUTPUT_DIRECTORY = ""
FOLDER_TO_DELETE = ""

def debug_print(message):
    """Print debug messages if debugging is enabled."""
    if DEBUG:
        print(message)

def check_rtf(file_path):
    """Check if RTF File adheres to the schema."""
    with open(file_path, 'r', encoding='utf-8') as file:
        rtf_content = file.read().replace("{\\line}\n", " ").replace("\\~", " ")
    rtf_tags = ['\\fonttbl', '\\header', '\\trowd', '\\row']
    for tag in rtf_tags:
        if tag not in rtf_content:
            print(tag, "not in rtf") # If RTF tag is not present, the RTF does not adhere to the schema
            return False
    return True

def extract_font_details(rtf_content):
    """Extract font details from RTF content."""
    font_table_pattern = re.compile(r'{\\fonttbl(.*?)}', re.DOTALL)
    font_table_match = font_table_pattern.search(rtf_content)
    if font_table_match:
        font_table = font_table_match.group(1)
    else:
        debug_print("No font table found")
        return {}

    font_pattern = re.compile(r'{\\f(\d+)\\.*? ([^;]+?);}')
    fonts = {}
    for match in font_pattern.finditer(font_table):
        font_id, font_name = match.groups()
        fonts['f' + font_id] = font_name
    return fonts

def extract_page_breaks(rtf_content):
    """Extract page breaks in the RTF File."""
    page_breaks = [p.start() for p in re.finditer(r"\\page", rtf_content)]
    page_breaks.append(len(rtf_content))
    return page_breaks

def extract_header(page_content):
    """Extract the page header."""
    try:
        header_start = re.search(r'{\\header', page_content).start()
        i = header_start + 1
        flag = 0
        header_end = 0
        while i < len(page_content):
            if page_content[i] == '{':
                flag += 1
            if page_content[i] == '}':
                if flag == 0:
                    header_end = i
                    break
                flag -= 1
            i += 1

        header = re.findall(r'{(?!\\)(.+)\\cell}', page_content[header_start:header_end])
        global PAGE
        PAGE += 1
        for h in range(len(header)):
            header[h] = header[h].replace('{\\field{\\*\\fldinst { PAGE }}}{', str(PAGE)).replace('}{\\field{\\*\\fldinst { NUMPAGES }}}', str(NUMPAGES))
    except:
        debug_print("Header not found")
    return header, page_content[header_end+1:]

def extract_title(page_content):
    """Extract the table title."""
    try:
        trhdr = []
        end_row = []
        for t in re.finditer(r'\\trhdr', page_content):
            trhdr.append(t.start())
        for e in re.finditer(r'{\\row}', page_content):
            end_row.append(e.end())

        title = []
        for i in range(len(trhdr)-1):
            title_line = re.search(r'{(.+)\\cell}', page_content[trhdr[i]:end_row[i]]).group()[1:-6]
            title_line = re.sub(r"\\(\w+)", "", title_line).strip()
            title.append(title_line)
        if len(trhdr) > 1:
            return title, page_content[end_row[len(trhdr)-2]+1:]
        return title, page_content[trhdr[0]:]
    except:
        debug_print("No title found")
        return [], page_content

def extract_column_headers(page_content):
    """Extract the table column headers."""
    try:
        end_row = re.search(r'{\\row}', page_content).end()
        headers = re.findall(r'{(.+)\\cell}', page_content[:end_row])
        column_headers = [re.sub(r"\\(\w+)", "", h).strip() for h in headers]
    except:
        debug_print("Column headers not found")
        column_headers = []
    return column_headers, page_content[end_row+1:]

def extract_table_data(page_content, column_headers):
    """Extract the table data."""
    try:
        trowd = []
        end_row = []
        for t in re.finditer(r'\\trowd', page_content):
            trowd.append(t.start())
        for e in re.finditer(r'{\\row}', page_content):
            end_row.append(e.end())

        subjects = []
        iter_count = len(trowd)
        if re.search(r'\\keepn', page_content[trowd[-1]:end_row[-1]]):
            iter_count -= 1
        for r in range(iter_count):
            row_data = re.findall(r'{(.+)\\cell}', page_content[trowd[r]:end_row[r]])
            row_data = list(filter(None, [re.sub(r"\\\w+", "", rd).strip() for rd in row_data]))
            if row_data:
                subject_details = {}
                for i in range(len(row_data)):
                    subject_details[column_headers[i]] = row_data[i]
                subjects.append(subject_details)
        return subjects
    except:
        debug_print("Table data extraction failed")
        return []

def main():
    """Main function to execute the data extraction and conversion to JSON."""
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(filetypes=[("RTF files", "*.rtf")])
    if not file_path:
        return
    
    output_directory = filedialog.askdirectory()
    if not output_directory:
        return

    folder_to_delete = output_directory

    with open(file_path, 'r', encoding='utf-8') as file:
        rtf_content = file.read()
    
    font_details = extract_font_details(rtf_content)
    page_breaks = extract_page_breaks(rtf_content)

    extracted_data = []
    for i in range(len(page_breaks) - 1):
        page_content = rtf_content[page_breaks[i]:page_breaks[i+1]]
        header, page_content = extract_header(page_content)
        title, page_content = extract_title(page_content)
        column_headers, page_content = extract_column_headers(page_content)
        table_data = extract_table_data(page_content, column_headers)
        extracted_data.append({
            'header': header,
            'title': title,
            'columns': column_headers,
            'data': table_data
        })

    output_file = os.path.join(output_directory, 'extracted_data.json')
    with open(output_file, 'w', encoding='utf-8') as json_file:
        json.dump(extracted_data, json_file, ensure_ascii=False, indent=4)

    messagebox.showinfo("Success", f"Data extracted and saved to {output_file}")

if __name__ == "__main__":
    main()
