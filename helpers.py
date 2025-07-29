# spiderfarm/helpers.py
from urllib.parse import urljoin, urlparse
import json
import pydoc
from datetime import datetime
from tabulate import tabulate

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

def display_dict(dict_data):
  print(json.dumps(dict_data, indent=2))

def display_table(table_data):
    table_output = tabulate(tabular_data=table_data, headers="keys", tablefmt="simple_grid", showindex=False)
    pydoc.pager(table_output)
    # print(table_output)