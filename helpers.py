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
from scrapy_playwright.page import PageMethod

NON_HTML_EXTENSIONS = (
        '.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.pdf', '.doc', 
        '.docx', '.xls', '.xlsx', '.js', '.css', '.ico', '.zip', '.rar', 
        '.exe', '.mp4', '.mp3', '.avi', '.mov', '.wmv'
        )

info_message = ("\nWelcome to the Link Spider by JDT using scrapy!\n"
                "\nParams:\n" 
                "   [--url <start_url>] = the seed URL where crawling starts\n"
                "   [--tag <tag>] = the HTML tag to target (default 'a' and 'link')\n"
                "   [--attr <attribute>] = the HTML tag attribute target (default is 'href)\n"
                "   [--ctag <container_tags] = a specific content container tag to target (format: [tag_type][. or #][name])\n"
                "   [--crawl] = including this parameter activates the recursive crawling capability (default is non-recursive)\n"
                "   [--depth <crawl_depth>] = an integer to control recursive crawl depth (0 is infinite/full site crawl, 1 is only the seed)\n"
                "   [--include <str>] = Only include links that contain one or more comma-separated substrings (case-insensitive)\n"
                "   [--exclude <str>] = Exclude links that contain one or more comma-separated substrings (case-insensitive)\n"
                "   [--log <log_level>]\n"
                "   [--auto <'save' or 'view'>] = Auto output mode: 'save' to export CSV, 'view' to show table\n"
                "   [--output <str>] = Optional filename (without extension) for CSV output (default = '[spider_name]_[timestamp].csv')\n"
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

# playwright
def playwright_meta(url):
    return {
        "playwright": True,
        "playwright_include_page": True,
        "playwright_page_methods": [
            PageMethod("goto", url, wait_until="domcontentloaded", timeout=60000)
        ],
        "playwright_context": "default",
    }

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

# filename handling
def sanitize_filename(name):
    """
    Removes invalid filename characters for cross-platform safety.
    """
    return re.sub(r'[<>:"/\\|?*]', '', name)

def generate_url_filename(seed_url=None, spider_name=None):
    """
    Generate a default filename referencing the spider used to crawl and the time/date stamp of the crawl.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    spider = spider_name or 'spiderfarm'
    if seed_url:
        parsed = urlparse(seed_url)
        domain = parsed.netloc.replace('www.', '').replace('.', '_')
        return f"{spider}_{domain}_{timestamp}.csv"
    return f"{spider}_{timestamp}.csv"

def filename_input(seed_url=None, spider_name=None):
    """
    Prompt user for filename and ensure .csv extension.
    """
    default_file_name = generate_url_filename(seed_url, spider_name)
    file_name_input = input("Enter a file name (or leave blank for default): ").strip()
    if file_name_input:
        base_name, _ = os.path.splitext(file_name_input)
        sanitized_name = sanitize_filename(base_name.strip())
        if not sanitized_name:
            print("Invalid file name entered. Using default instead.")
            return default_file_name
        return f"{sanitized_name}.csv"
    else:
        return default_file_name

# data reviews
def save_csv(table_data, headers, auto_save=False, output_filename=None, seed_url=None, spider_name=None):
    """
    Save the table data to a CSV file.
    - If output_filename is provided: sanitize it and force .csv
    - If auto_save is True: use default filename
    - Else: prompt the user
    """
    if output_filename:
        base, _ = os.path.splitext(output_filename.strip())
        sanitized_name = sanitize_filename(base)
        file_name = f"{sanitized_name}.csv" if sanitized_name else generate_url_filename(seed_url, spider_name)
    elif auto_save:
        file_name = generate_url_filename(seed_url, spider_name)
    else:
        file_name = filename_input(seed_url, spider_name)
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

# main data handling
def data_handling_options(
        table_data, 
        headers, 
        auto_view=False, 
        auto_save=False, 
        output_filename=None, 
        seed_url=None,
        spider_name=None
        ):
    if not table_data or not headers:
        print("No table data or headers provided.")
        return
    if auto_save:
        save_csv(
            table_data, 
            headers, 
            auto_save=True, 
            output_filename=output_filename,
            seed_url=seed_url,
            spider_name=spider_name)
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
        save_csv(
            table_data,
            headers,
            auto_save=False,
            output_filename=output_filename,
            seed_url=seed_url,
            spider_name=spider_name)
    elif report_view == '2':
        # display table
        display_table(table_data, headers, auto_view=False)
    else:
        print("Invalid input, please select one of the indicated options.")
        sys.exit(1)