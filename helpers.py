from urllib.parse import urljoin, urlparse
import time
import sys
import json
import pydoc
import requests
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

# exceptions wrapper
def handle_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            print_error(func.__name__, e)
        except KeyboardInterrupt as e:
            print_error(func.__name__, e)
        except FileNotFoundError as e:
            print_error(func.__name__, e)
        except AttributeError as e:
            print_error(func.__name__, )
        except Exception as e:
            print_error(func.__name__, e)
    def print_error(func_name, error):
        print(f"\nError in function '{func_name}': {repr(error)} - Exiting...\n")
    return wrapper

# validate URL
def is_valid_url(url):
    if not url or not url.startswith(('http://', 'https://')):
        return
    result = urlparse(url)
    return all([result.scheme, result.netloc])

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