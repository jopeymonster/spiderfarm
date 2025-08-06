# -*- coding: utf-8 -*-
# spiderfarm/helpers.py
import csv
import sys
import re
import pydoc
from urllib.parse import urljoin, urlparse
from pathlib import Path
import os
import pydoc
from datetime import datetime
from tabulate import tabulate

NON_HTML_EXTENSIONS = (
        '.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.pdf', '.doc', 
        '.docx', '.xls', '.xlsx', '.js', '.css', '.ico', '.zip', '.rar', 
        '.exe', '.mp4', '.mp3', '.avi', '.mov', '.wmv'
        )

info_message = ("\nWelcome to the Link Spider by JDT using scrapy!\n"
                "\nUsage: python main.py [--url <start_url>] [--tag <tag>] [--attr <attribute>] [--ctag <container_tags] [--depth <crawl_depth>] [--log <log_level>]\n"
                "\nExample: python main.py --url https://example.com --tag a --attr href --ctag div.article --depth 3 --log INFO\n"
                "\nThis is a recursive spider that will crawl links from a starting URL.\n"
                "A HTML tag and attribute can be specified to narrow the scope of the links that are crawled.\n"
                "Default HTML tags set to be discovered are 'a' and 'link', with the default attribute being 'href'.\n"
                "Content tags (div & span) can be used as targeting options as well.\n"
                "This spider has an option for crawling depth (default is 2, infinity is 0), which allows it to follow links up to the depth specified.\n")

# URL validation
def validate_and_normalize_url(url):
    """
    Validate and normalize URLs to reduce duplicates.
    """
    if not url:
        return None
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

# xpath conversion
def get_container_xpath(obj):
    """
    Converts a selector into xpath
    """
    if '.' in obj.ctag:
        tag, classname = obj.ctag.split('.',1)
        return f'//{tag}[contains(@class,"{classname}")]'
    elif '#' in obj.ctag:
        tag, idname = obj.ctag.split('#',1)
        return f'//{tag}[@id="{idname}"]'
    else:
        return f'//{obj.ctag}'

# generate timestamp
def generate_timestamp():
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    # print(now_time)
    return timestamp

# data handling
def data_handling_options(table_data, headers, auto_view=False, auto_save=False, output_filename=None, seed_url=None):
    if not table_data or not headers:
        print("No table data or headers provided.")
        return
    if auto_save:
        save_csv(table_data, headers, auto_save=True, output_filename=output_filename, seed_url=seed_url)
        return
    if auto_view:
        display_table(table_data, headers, auto_view=True)
        return
    print("\nHow would you like to view the report?\n"
            "1. CSV\n"
            "2. Display table on screen\n")
    report_view = input("Choose 1 or 2 ('exit' to exit): ")
    if report_view == '1':
        # save to csv
        save_csv(table_data, headers, auto_save=False, output_filename=output_filename, seed_url=seed_url)
    elif report_view == '2':
        # display table
        display_table(table_data, headers, auto_view=False)
    else:
        print("Invalid input, please select one of the indicated options.")
        sys.exit(1)

def sanitize_filename(name):
    """
    Removes invalid filename characters for cross-platform safety.
    """
    return re.sub(r'[<>:"/\\|?*]', '', name)

def default_filename():
    """
    Generates a default filename based on the current timestamp.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    default_file_name = f"linkspider_{timestamp}.csv"
    print(f"Default file name: {default_file_name}")
    return default_file_name

def filename_input(seed_url=None):
    """
    Prompt user for filename and ensure .csv extension.
    """
    default_file_name = generate_url_filename(seed_url)
    file_name_input = input("Enter a file name (or leave blank for default): ").strip()
    if file_name_input:
        base_name, _ = os.path.splitext(file_name_input)
        safe_name = sanitize_filename(base_name.strip())
        if not safe_name:
            print("Invalid file name entered. Using default instead.")
            return default_file_name
        return f"{safe_name}.csv"
    else:
        return default_file_name

def generate_url_filename(seed_url=None):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    if seed_url:
        parsed = urlparse(seed_url)
        domain = parsed.netloc.replace('www.', '').replace('.', '_')
        return f"linkspider_{domain}_{timestamp}.csv"
    return f"linkspider_{timestamp}.csv"

def save_csv(table_data, headers, auto_save=False, output_filename=None, seed_url=None):
    """
    Save the table data to a CSV file.
    - If output_filename is provided: sanitize it and force .csv
    - If auto_save is True: use default filename
    - Else: prompt the user
    """
    if output_filename:
        base, _ = os.path.splitext(output_filename.strip())
        safe_name = sanitize_filename(base)
        if not safe_name:
            print("Invalid output filename provided. Using default.")
            file_name = generate_url_filename(seed_url=seed_url)
        else:
            file_name = f"{safe_name}.csv"
    elif auto_save:
        file_name = generate_url_filename(seed_url=seed_url)
    else:
        file_name = filename_input(seed_url=seed_url)
    file_path = Path.home() / file_name
    try:
        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            writer.writerows(table_data)
        print(f"\nData saved to: {file_path} ({len(table_data)} rows)\n")
    except Exception as e:
        print(f"\nFailed to save file: {e}\n")

def display_table(table_data, headers, auto_view=False):
    """
    Displays a table using the tabulate library.
    Args:
        table_data (list): The data to display in the table.
        headers (list): The headers for the table.
    """
    if auto_view is True:
        print(tabulate(table_data, headers, tablefmt="simple_grid"))
    else:
        input("Report ready for viewing. Press ENTER to display results and 'Q' to exit output when done...")
        pydoc.pager(tabulate(table_data, headers=headers, tablefmt="simple_grid")) 