import re
from configparser import ConfigParser
from datetime import datetime
from json_creation import json_conversion
import logging

# Read config.ini file
config_object = ConfigParser()
config_object.read("config.ini")

# Get the RTF tags, RE expressions and alignment data from the config file
Debug_flag = config_object["DEBUG FLAG"]
RTF_tags = config_object["RTF TAGS"]
RE_expressions = config_object["RE EXPRESSIONS"]
Header_alignment = config_object['HEADER ALIGNMENT']
Log_files = config_object['LOG FILE DETAILS']
RTF_Style_Tags = config_object['RTF STYLE TAGS']

logging.start_logging()

# Global debugging flag
DEBUG = Debug_flag["debug"]
json_dictionary = {}
STYLE_LEVEL = "None"

# global PAGE variable declaration to count the number of pages
PAGE = 0
NUMPAGES = 0

def debug_print(message):
    '''
    This function serves as the debugging switch
    '''
    if DEBUG != "False":
        print(message)

# Function to extract font details from RTF content
def extract_font_details(rtf_content):
    '''This is a function to extract the font details of the RTF file
    The font details are found by using the '\\fonttbl' RTF tag
    The fonts are then extracted using an re expression to match the patterns
    The fonts are stored along with the font ID in a dictionary
    These key value pairs will be used later to extract the font details on each section
    '''
    # Extract font table
    font_table_pattern = re.compile(RE_expressions['font table'], re.DOTALL)

    font_table_match = font_table_pattern.search(rtf_content)
    if font_table_match:
        font_table = font_table_match.group(1)

    else:
        debug_print("No font table found")
        return {}

    # Extract font details from font table
    font_pattern = re.compile(RE_expressions['font pattern'])

    fonts = {}
    for match in font_pattern.finditer(font_table):
        font_id, font_name = match.groups()
        fonts['f'+font_id] = font_name
    return fonts

# Function to extract page breaks in the RTF File
def extract_colour_table(rtf_content):
    '''
    This function extracts the colour table
    '''
    colour_pattern = re.compile(RE_expressions['colour pattern'])
    colours = {}
    i = 1
    for match in colour_pattern.finditer(rtf_content):
        colours['cf'+str(i)] = tuple(int(i) for i in match.groups())
        i += 1
    return colours

def extract_font(style):
    '''
    This function is used to extract the font of a particular segment
    '''
    return json_dictionary['fonts'][style.groups()[0]]

def extract_size(style):
    '''
    This function is used to extract the size of a particular segment
    '''
    return int(style.groups()[1][2:])

def extract_colour(style):
    '''
    This function is used to extract the colour of a particular segment
    '''
    return json_dictionary['colours'][style.groups()[2]]

def check_bold(row_content):
    '''
    This function is used to check whether a particular segment is bold 
    '''
    if RTF_Style_Tags["bold"] in row_content:
        return "YES"

def check_italic(row_content):
    '''
    This function is used to check whether a particular segment is italic 
    '''
    if RTF_Style_Tags["italic"] in row_content:
        return "YES"
    
def check_underline(row_content):
    '''
    This function is used to check whether a particular segment is underlined 
    '''
    if RTF_Style_Tags["underline"] in row_content:
        return "YES"
    
def check_superscript(row_content):
    '''
    This function is used to check whether a particular segment is superscript 
    '''
    if RTF_Style_Tags["superscript"] in row_content:
        return "YES"
    
def check_subscript(row_content):
    '''
    This function is used to check whether a particular segment is subscript 
    '''
    if RTF_Style_Tags["subscript"] in row_content:
        return "YES"


def extract_style_details(row_content):
    '''
    This function is used to extract the style details of a particular segment
    '''
    global STYLE_LEVEL
    if (STYLE_LEVEL == "ALL"):
        style = re.search(RE_expressions['styles'],row_content) 
        style_info = {}
        style_info['font'] = extract_font(style)
        style_info['size'] = extract_size(style)
        style_info['colour'] = extract_colour(style)
        style_info['bold'] = check_bold(row_content)
        style_info['italic'] = check_italic(row_content)
        style_info['underline'] = check_underline(row_content)
        style_info['subscript'] = check_subscript(row_content)
        style_info['superscript'] = check_superscript(row_content)
    
        return style_info
def special_characters(rtf_content):
    '''
    This function handles special characters
    '''
    pattern = r"\\u(\d+)"
    def replace_unicode(match):
        unicode_number = int(match.group(1))
        return chr(unicode_number)
    rtf_content = re.sub(pattern, replace_unicode, rtf_content)
    return rtf_content

def extract_page_breaks(rtf_content):
    '''This function finds the page breaks using '\\endnhere' RTF tag
    This function is used to split and extract the RTF content for each page
    '''
    page_breaks = []
    for p in re.finditer(r"\\endnhere", rtf_content): # Using the '\endhere' tag to find page breaks
        page_breaks.append(p.start())
    page_breaks.append(len(rtf_content))
    return page_breaks


# Function to extract the page header
def extract_header(page_content):
    '''This function extracts the page header using the '\\header' RTF tag
    The content enclosed within the '\\header' tag, is found,
    and the data is extracted using an re expression
    '''
    global PAGE
    PAGE += 1
    try:
        header_start = re.search(r'{\\header' , page_content).start()
        # Finding the '\header' tag to find the header
        i = header_start+1
        flag = 0
        header_end = 0
        
        # This while loop is used to find the header content in the page
        # It parses through the data to find the'}'symbol
        while i < len(page_content):
            if page_content[i] == '{' :
                flag += 1
            if page_content[i] == '}' :
                if flag == 0 :
                    header_end = i
                    break
                flag -= 1
            i += 1

        styles = extract_style_details(page_content[header_start:header_end])
        header = re.findall(RE_expressions['header'] , page_content[header_start : header_end])
        headerstyle = re.findall(RE_expressions['headerstyle']
                                ,page_content[header_start : header_end])
        # Dict to store the header content with the alignment
        headers_and_styles = {}
        headers_and_styles['style'] = styles
        headers = {}
        for h, header_line in enumerate(header):
            header_line = header_line.replace(
                '{\\field{\\*\\fldinst { PAGE }}}{',str(PAGE)).replace(
                    '}{\\field{\\*\\fldinst { NUMPAGES }}}',str(NUMPAGES))
            headers[header_line]=headerstyle[h][0]
        debug_print("Header extracted successfully")
        headers_and_styles['data'] = headers

    # Used to check whether the header content is extracted successfully
    except AttributeError:
        debug_print("Header not found")
        logging.write_exceptions("Header not extracted successfully in page " + str(PAGE))
    return headers_and_styles, page_content[header_end+1:]

# Function to extract the table title
def extract_title(page_content):
    '''This function is used to extract the table title using the '\\trhdr' RTF tag
    The '\\row' tag is used to find the end of the title rows
    Re expressions are used to extract the titles data
    '''

    try:
        trhdr = []
        end_row = []
        for t in re.finditer(r'\\trhdr' , page_content) :
            trhdr.append(t.start())
        for e in re.finditer(r'{\\row}' , page_content) :
            end_row.append(e.end())
        title = []
        styles = extract_style_details(page_content[trhdr[0]:end_row[0]])
        titles_and_styles = {}
        titles_and_styles['style'] = styles
        for i in range(len(trhdr)-1):
            title_line=re.search(r'{(.+)\\cell}',page_content[trhdr[i]:end_row[i]]).group()[1:-6]
            title_line=re.sub(r"\\(\w+)","",title_line).strip()
            title.append(title_line)
        titles_and_styles['data'] = title
        debug_print("Title extracted successfully")
        if len(trhdr)>1:
            return titles_and_styles, page_content[end_row[len(trhdr)-2]+1:]
        return titles_and_styles, page_content[trhdr[0]:]

    # Used to check whether the table title is extracted successfully
    except AttributeError:
        debug_print("No title found")
        logging.write_exceptions("Title not extracted successfully in page " + str(PAGE))

# Function to extract the table column headers
def extract_column_headers(page_content):
    '''This function extracts the column headers
    The '\\row' tag is used to find the end of the column headers row
    '''
    try:
        end_row = re.search(r'{\\row}', page_content).end()
        styles = extract_style_details(page_content[:end_row])
        column_headers_and_styles = {}
        column_headers_and_styles['style'] = styles
        headers = re.findall(r'{(.+)\\cell}' , page_content[:end_row])
        column_headers = [re.sub(r"\\(\w+)", "", h).strip() for h in headers]
        column_headers_and_styles['data'] = column_headers
        debug_print("Column headers extracted successfully")

    # Used to check whether the column headers are extracted successfully
    except AttributeError:
        debug_print("Column headers not found")
        logging.write_exceptions("Column headers not extracted successfully in page " + str(PAGE))
        column_headers = []
    return column_headers_and_styles, page_content[end_row+1:]

# Function to extract the table data
def extract_table_data(page_content, column_headers):
    '''This function is used to extract the table data
    The '\\trowd' tag is used to find the beginning of each row
    The '\\row' tag is used to find the end of each row
    The data in each row is extracted, and mapped to the column headers in a dictionary
    The presence of footnotes in the page is checked using the '\\keepn' tag
    '''
    try:
        trowd = []
        end_row = []
        for t in re.finditer(r'\\trowd' , page_content) :
            trowd.append(t.start())
        for e in re.finditer(r'{\\row}' , page_content) :
            end_row.append(e.end())
        subjects_and_styles = {}
        subjects = []
        no_of_rows = len(trowd)
        style = extract_style_details(page_content[trowd[0]:end_row[0]])
        subjects_and_styles['style'] = style
        if re.search(r'\\keepn', page_content[trowd[-1]:end_row[-1]]):
            no_of_rows -= 1
        for r in range(no_of_rows):
            row_data = re.findall(r'{(.+)\\cell}' , page_content[trowd[r]:end_row[r]])
            row_data = list(filter(None, [re.sub(r"\\\w+" , "" , rd).strip() for rd in row_data]))
            if row_data :
                subject_details = {}
                for i, row_data_values in enumerate(row_data) :
                    if not row_data_values.isdigit():
                        subject_details[column_headers[i]] = row_data_values
                    else:
                        subject_details[column_headers[i]] = int(row_data_values)

                subjects.append(subject_details)
        subjects_and_styles['data'] = subjects
        debug_print(
            "Table data extracted successfully")
    # Used to check whether the table data is extracted successfully
    except AttributeError:
        debug_print("Table data not found")
        logging.write_exceptions("Table data not extracted successfully in page " + str(PAGE))
        subjects = []
    return subjects_and_styles, page_content[end_row[r]:]

# Function to extract the table footnotes
def extract_footnotes(page_content):
    '''This function is used to extract the footnotes using an re expression'''
    try:
        footnotes = [re.search(r'{(.+)\\cell}', page_content).group()[1:-6]]
        debug_print(f"Footer found: {footnotes}")
        debug_print("Footnotes extracted successfully")
    # Used to check whether the footnotes are extracted successfully
    except AttributeError:
        debug_print("Footnotes not found")
        message = "Footnotes not extracted successfully in page " + str(PAGE)
        logging.write_exceptions(message + "\n")
        footnotes = []
    return footnotes

# Function to extract the table footer
def extract_footer(footnotes):
    '''This function is used to find the table footer
    Is found by searching for 'Source'/'Dataset'
    The table footers are then extracted
    '''
    try:
        if not footnotes :
            return [], []
        footnote = footnotes[0]
        if "Source" in footnote :
            i = footnote.find("Source")
            return footnote[:i] , footnote[i:]
        if "Dataset" in footnote :
            i = footnote.find("Dataset")
            return footnote[:i] , footnote[i:]
    # Used to check whether the footer is extracted successfully
    except AttributeError:
        debug_print("Footer not found")
        logging.write_exceptions("Footer not extracted successfully in page " + str(PAGE))

# Function to extract the contents of a page
def extract_page_content(page_content):
    '''
    This function is used to extract the content of each page
    A dictionary called 'page_details' is initialized
    The respective functions to extract the page header, table title,
    column headers, subjects details, footnotes and footers are called
    '''
    page_details = {}
    page_details['header'], page_content = extract_header(page_content)
    page_details['title'], page_content = extract_title(page_content)
    page_details['column headers'], page_content = extract_column_headers(page_content)
    page_details['subjects'], page_content = (
    extract_table_data(page_content, page_details['column headers']['data'])
    )
    page_details['footnotes'] = extract_footnotes(page_content)
    page_details['footnotes'], page_details['footer'] = (
    extract_footer(page_details['footnotes'])
    )

    return page_details

# Function to convert an rtf file to json
def convert_rtf(item, file_no, output_directory):
    '''
    This function is used to convert the RTF file into JSON format
    The page breaks function is called to split the content for each page
    '''
    debug_print(f"Converting file {file_no}: {item}")
    try:
      # Extract rtf content as a string in python
        with open(item, 'r', encoding = "utf-8") as file:
            rtf_content = file.read().replace("{\\line}\n", " ").replace("\\~", " ")
            debug_print(f"RTF content loaded for file {file_no}")
        
        rtf_content = special_characters(rtf_content)

        fonts = extract_font_details(rtf_content)
        colours = extract_colour_table(rtf_content)
        debug_print(f"Fonts extracted: {fonts}")
        
        global json_dictionary
        json_dictionary = {}
        data = []
        json_dictionary ['fonts'] = fonts
        json_dictionary ['colours'] = colours
        json_dictionary ['data'] = data

        page_breaks = extract_page_breaks(rtf_content)
        debug_print(f"Page breaks found: {page_breaks}")

        global PAGE
        PAGE = 0
        global NUMPAGES
        NUMPAGES = rtf_content.count("NUMPAGES")
        for i in range(len(page_breaks)-1) :

            page_content = rtf_content[page_breaks[i] : page_breaks[i+1]]
            debug_print(f"Processing page {PAGE + 1}")
            page_details = extract_page_content(page_content)
            data.append(page_details)
        
        return json_conversion(json_dictionary, item, output_directory)

    except Exception as e:
        debug_print("Error, cannot be converted due to " + str(e))
        logging.write_exceptions(datetime.now().isoformat() + "\n" + item+" cannot be converted due to " + str(e) + "\n")
        return "Failed", "Not in Scope"
    