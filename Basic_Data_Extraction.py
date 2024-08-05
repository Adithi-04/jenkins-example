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
from datetime import datetime


#Read config.ini file
config_object = ConfigParser()
config_object.read("config.ini")

#Get the password
RTF_tags = config_object["RTF TAGS"]
RE_expressions = config_object["RE EXPRESSIONS"]

log_file_exceptions = open("/Users/adithi/Desktop/Log File Exceptions.txt", 'a')
log_file_success = open("/Users/adithi/Desktop/Log File Success.txt", 'a')

log_file_exceptions.write('\n' + str(datetime.now()) + '\n')
log_file_success.write('\n' + str(datetime.now()) + '\n')


# Global debugging flag
DEBUG = True
output_directory = ""
folder_to_delete = ""

def debug_print(message):
    if DEBUG:
        print(message)

# Function to check if RTF File adheres to the schema

''' 
This is a function that checks whether the RTF File adheres to the schema mentioned. 
The adherence to the schema is found by checking whether the commonly used RTF control tags are used in the RTF file.
The RTF file is loaded, and then the content is read using the "file.read()" function
A list is created to store the RTF tags
An iterator is used to parse the list and check if all the tags are present in the file
'''

def check_rtf(file_path):
    with open(file_path, 'r') as file:
        rtf_content = file.read().replace("{\\line}\n", " ").replace("\\~", " ")
     # Commonly used RTF tags
    rtf_tags = [RTF_tags["page break"],RTF_tags['header'], RTF_tags['title'], RTF_tags["row start"], RTF_tags["row end"], RTF_tags["cell end"]]
    flag = True
    for i in rtf_tags:
        if i in rtf_content:
            continue
        else:
            print(i," not in rtf") # If RTF tag is not present, the RTF does not adhere to the schema
            log_file_exceptions.write(i + " not in RTF \n")
            flag = False
            break
    return flag

# Function to extract font details from RTF content

'''
This is a function to extract the font details of the RTF file
The font details are found by using the '\\fonttbl' RTF tag
The fonts are then extracted using an re expression to match the patterns
The fonts are stored along with the font ID in a dictionary
These key value pairs will be used later to extract the font details on each section
'''

def extract_font_details(rtf_content):

    # Extract font table
    font_table_pattern = re.compile(RE_expressions['font table'], re.DOTALL) 

    font_table_match = font_table_pattern.search(rtf_content)
    if font_table_match:
        font_table = font_table_match.group(1)

    else: # pragma: no cover
        debug_print("No font table found") # pragma: no cover
        return {} # pragma: no cover

    # Extract font details from font table
    font_pattern = re.compile(RE_expressions['font pattern'])

    fonts = {}
    for match in font_pattern.finditer(font_table):
        font_id, font_name = match.groups()
        fonts['f'+font_id] = font_name    
    return fonts

# Function to extract page breaks in the RTF File

'''
This function finds the page breaks using '\\endnhere' RTF tag
This function is used to split and extract the RTF content for each page
'''

def extract_page_breaks(rtf_content):
    page_breaks = []
    for p in re.finditer(r"\\endnhere", rtf_content): # Using the '\endhere' tag to find page breaks
        page_breaks.append(p.start())
    page_breaks.append(len(rtf_content))
    return page_breaks

# Function to extract the page header

'''
This function extracts the page header using the '\\header' RTF tag
The content enclosed within the '\\header' tag, is found, and the data is extracted using an re expression
'''

def extract_header(page_content):
    global PAGE
    PAGE += 1
    try:
        header_start = re.search(r'{\\header' , page_content).start() # Finding the '\header' tag to find the header
        i = header_start+1
        flag = 0
        header_end = 0
        '''
        this while loop is used to find the header content in the page
        it parses through the data to find the '}' symbol
        '''
        while i < len(page_content) :
            if page_content[i] == '{' :
                flag += 1
            if page_content[i] == '}' :
                if flag == 0 :
                    header_end = i
                    break
                else :
                    flag -= 1
            i += 1

        header = re.findall(RE_expressions['header'] , page_content[header_start : header_end])
    
        for h in range (len(header)):
            header[h] = header[h].replace('{\\field{\\*\\fldinst { PAGE }}}{',str(PAGE)).replace('}{\\field{\\*\\fldinst { NUMPAGES }}}',str(NUMPAGES))
        # debug_print("Header extracted successfully")

    except:
        debug_print("Header not found")
        log_file_exceptions.write("Header not found in " + str(PAGE))
    return header, page_content[header_end+1:]

# Function to extract the table title

'''
This function is used to extract the table title using the '\\trhdr' RTF tag
The '\\row' tag is used to find the end of the title rows
Re expressions are used to extract the titles data
'''

def extract_title(page_content):
    try:
        trhdr = []
        end_row = []
        for t in re.finditer(r'\\trhdr' , page_content) :
            trhdr.append(t.start())
        for e in re.finditer(r'{\\row}' , page_content) :
            end_row.append(e.end())
        
        title = []
        for i in range(len(trhdr)-1):
            title_line = re.search(r'{(.+)\\cell}' , page_content[trhdr[i]:end_row[i]]).group()[1:-6]
            title_line = re.sub(r"\\(\w+)", "", title_line).strip()
            title.append(title_line)
        # debug_print("Title extracted successfully")
        if len(trhdr)>1:
            return title, page_content[end_row[len(trhdr)-2]+1:]
        else:
            return title, page_content[trhdr[0]:]

    except:
        debug_print("No title found")
        log_file_exceptions.write("Title not found in " + str(PAGE))
 
# Function to extract the table column headers

'''
This function extracts the column headers
The '\\row' tag is used to find the end of the column headers row
'''

def extract_column_headers(page_content):
    try:
        end_row = re.search(r'{\\row}', page_content).end()

        headers = re.findall(r'{(.+)\\cell}' , page_content[:end_row])
        column_headers = [re.sub(r"\\(\w+)", "", h).strip() for h in headers]
        # debug_print("Column headers extracted succesfully")
    except:
        debug_print("Column headers not found")
        log_file_exceptions.write("Column headers not found in " + str(PAGE))
        column_headers = []
    return column_headers, page_content[end_row+1:]

# Function to extract the table data

'''
This function is used to extract the table data 
The '\\trowd' tag is used to find the beginning of each row
The '\\row' tag is used to find the end of each row
The data in each row is extracted, and mapped to the column headers in a dictionary
The presence of footnotes in the page is checked using the '\\keepn' tag
'''

def extract_table_data(page_content, column_headers):
    try:
        trowd = []
        end_row = []
        for t in re.finditer(r'\\trowd' , page_content) :
            trowd.append(t.start())
        for e in re.finditer(r'{\\row}' , page_content) :
            end_row.append(e.end())

        subjects = []
        Iter = len(trowd)
        if re.search(r'\\keepn', page_content[trowd[-1]:end_row[-1]]):
            Iter -= 1
        for r in range(Iter):
            row_data = re.findall(r'{(.+)\\cell}' , page_content[trowd[r]:end_row[r]])
            row_data = list(filter(None, [re.sub(r"\\\w+" , "" , rd).strip() for rd in row_data]))
            if row_data :
                subject_details = {}
                for i in range(len(row_data)) :
                    subject_details[column_headers[i]] = row_data[i] if not row_data[i].isdigit() else int(row_data[i])
                subjects.append(subject_details)
        # debug_print("Table data extracted successfully")
    except:
        debug_print("Table data not found")
        log_file_exceptions.write("Table data not found in " + str(PAGE))
        subjects = []
    
    return subjects, page_content[end_row[r]:]

# Function to extract the table footnotes 

'''
This function is used to extract the footnotes using an re expression
'''

def extract_footnotes(page_content):
    try:
        footnotes = [re.search(r'{(.+)\\cell}', page_content).group()[1:-6]]
        # debug_print(f"Footer found: {footnotes}")
        # debug_print("Footnotes extracted successfully")
    except:
        debug_print("Footnotes not found")
        log_file_exceptions.write("Footnotes not found in " + str(PAGE))
        footnotes = []
    return footnotes

# Function to extract the table footer 

'''
This function is used to find the table footer
The existence of table footer is found by searching for 'Source' or 'Dataset'
The table footers are then extracted
'''

def extract_footer(footnotes):
    try:
        # debug_print("Footer extracted successfully")
        if not footnotes :
            return [], []
        footnote = footnotes[0]
        if "Source" in footnote :
            i = footnote.find("Source")
            return footnote[:i] , footnote[i:]
        elif "Dataset" in footnote :
            i = footnote.find("Dataset")
            return footnote[:i] , footnote[i:]
    except:
        debug_print("Footer not found")
        log_file_exceptions.write("Footer not found in " + str(PAGE))

# Function to extract the contents of a page

'''
This function is used to extract the content of each page
A dictionary called 'page_details' is initialized
The respective functions to extract the page header, table title, column headers, subjects details, footnotes and footers are called

'''

def extract_page_content(page_content):
    page_details = {}
    page_details['header'], page_content = extract_header(page_content)
    page_details['title'], page_content = extract_title(page_content)
    page_details['column headers'], page_content = extract_column_headers(page_content)
    page_details['subjects'], page_content = extract_table_data(page_content, page_details['column headers'])
    page_details['footnotes'] = extract_footnotes(page_content)
    page_details['footnotes'] , page_details['footer'] = extract_footer(page_details['footnotes'])
    return page_details

# Function to convert an rtf file to json

'''
This function is used to convert the RTF file into JSON format
The page breaks function is called to split the content for each page
'''

def convert_rtf(item, file_no, output_directory):
    debug_print(f"Converting file {file_no}: {item}")
    # output_log = open('/Users/shreejakatama/Downloads/Internship/Folder Code/Output_log.txt','a')
    try:
      # Extract rtf content as a string in python
        with open(item, 'r') as file:
            rtf_content = file.read().replace("{\\line}\n", " ").replace("\\~", " ")
            debug_print(f"RTF content loaded for file {file_no}")

        fonts = extract_font_details(rtf_content)
        # debug_print(f"Fonts extracted: {fonts}")

        json_dictionary = {}
        data = []
        json_dictionary ['fonts'] = fonts
        json_dictionary ['data'] = data

        page_breaks = extract_page_breaks(rtf_content)
        # debug_print(f"Page breaks found: {page_breaks}")

        global PAGE
        PAGE = 0
        global NUMPAGES
        NUMPAGES = rtf_content.count("NUMPAGES")
        
        for i in range(len(page_breaks)-1) :

            page_content = rtf_content[page_breaks[i] : page_breaks[i+1]]
            # debug_print(f"Processing page {PAGE + 1}")

            page_details = extract_page_content(page_content)

            data.append(page_details)
        
        output_file = os.path.join(output_directory, f"{os.path.splitext(os.path.basename(item))[0]}.json")
        with open(output_file, 'w') as f:
            json.dump(json_dictionary , f, indent=4)
        # debug_print(f"JSON file {output_file} successfully created")
        log_file_success.write(f"Data successfully written to {output_file}\n")

        return "Successful", ""
    
    except Exception as e: # pragma: no cover 
        debug_print("Error, cannot be converted due to " + str(e)) # pragma: no cover 
        log_file_exceptions.write(item+"cannot be converted due to "+str(e)+"\n") # pragma: no cover 
        return "Failed", "Not in Scope" # pragma: no cover 


def upload_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        selected_folder_path.set(folder_selected)
        global selected_selected_folder_path
        selected_selected_folder_path = folder_selected
        process_files(folder_selected)

def process_files(selected_folder_path):
    global output_directory, folder_to_delete  # Declare as global variables
    # output_log = open("Output_log.txt", 'a')
    for row in table.get_children():
        table.delete(row)

    if not selected_folder_path:
        return

    files = os.listdir(selected_folder_path)
    output_directory = os.path.join(selected_folder_path, 'Output')
    folder_to_delete = output_directory  # Assign the output directory to folder_to_delete
    os.makedirs(output_directory, exist_ok=True)
    print('{output_directory} successfully created')
    file_no = 0
    for file in files:
        file_path = os.path.join(selected_folder_path, file)
        if not file.endswith('.rtf'):
            status = "Failed"
            remarks = "Choose a RTF File"
            color = 'red'
            debug_print("Not an RTF File, cannot be converted")
        elif os.path.isfile(file_path):
            file_no += 1
            if check_rtf(file_path):
                print("RTF File conforms to schema")
                status, remarks = convert_rtf(file_path, file_no, output_directory)
                color = 'green' if status == "Successful" else 'red'
                debug_print("RTF File converted successfully")
    
            else:
                print(f"RTF File {file} does not conform to schema, cannot be converted")
                log_file_exceptions.write(f"RTF File {file} does not conform to schema, cannot be converted\n")
                status = "Failed"
                remarks = "No remarks Found"
                color = 'red'
        else:
            status = "Failed"
            remarks = "No remarks Found"
            color = 'red'

        table.insert("", "end", values=(file, status, remarks), tags=(color,))

def on_continue():
    messagebox.showinfo("Info", "Continue button clicked!")


def on_delete():
    for row in table.get_children():
        table.delete(row)
    selected_folder_path.set("")

def user_interface():
    app = tk.Tk()
    app.title("RTF to JSON Converter")
    app.geometry("800x600")

    global selected_folder_path
    selected_folder_path = tk.StringVar()

    title_label = tk.Label(app, text="RTF to JSON Converter", font=("Times New Roman", 20, "bold"))
    title_label.place(relx=0.5, rely=0.05, anchor=tk.CENTER)

    subtitle1_label = tk.Label(app, text="Convert Your RTF Document to JSON Format", font=("Times New Roman", 8))
    subtitle1_label.place(relx=0.5, rely=0.1, anchor=tk.CENTER)

    subtitle2_label = tk.Label(app, text="Select the RTF Folder to be Uploaded", font=("Times New Roman", 14))
    subtitle2_label.place(relx=0.5, rely=0.2, anchor=tk.CENTER)

    upload_button = tk.Button(app, text="UPLOAD RTF FOLDER", command=upload_folder)
    upload_button.place(relx=0.5, rely=0.25, anchor=tk.CENTER)

    global table
    columns = ("File Name", "Status", "Remarks")
    table = ttk.Treeview(app, columns=columns, show="headings")
    table.heading("File Name", text="File Name")
    table.heading("Status", text="Status")
    table.heading("Remarks", text="Remarks")
    table.place(relx=0.5, rely=0.57, anchor=tk.CENTER, relwidth=0.8, relheight=0.55)

    table.tag_configure('green', background='lightgreen')
    table.tag_configure('red', background='lightcoral')

    style = ttk.Style()
    style.configure("TButton", padding=6, relief="flat", background="#ccc")
    style.map("TButton",
            background=[('active', '#0052cc'), ('!disabled', '#004080')],
            foreground=[('active', 'white'), ('!disabled', 'Black')],
            relief=[('pressed', 'sunken'), ('!pressed', 'raised')])

    continue_button = ttk.Button(app, text="CONTINUE", command=on_continue, style="TButton")
    continue_button.place(relx=0.3, rely=0.9, anchor=tk.CENTER)

    delete_button = ttk.Button(app, text="DELETE", command=on_delete, style="TButton")
    delete_button.place(relx=0.7, rely=0.9, anchor=tk.CENTER)

    app.mainloop()
    debug_print("UI loaded")

'''
Main function to call the user_interface() function
'''
if __name__ == "__main__" :
    try:
        user_interface()
    except: # pragma: no cover
        debug_print("UI unsuccessful") # pragma: no cover

