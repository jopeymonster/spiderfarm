# -*- coding: utf-8 -*-
# spiderfarm/main.py
import argparse
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from spiderfarm.spiders.linkspider import LinkSpider
from spiderfarm.spiders.schemaspider import SchemaSpider
import helpers

def init_menu(args, spider_class, include, exclude):
    settings = get_project_settings()
    # pass default link tag+attr values for link crawling process
    tag = args.tag
    attr = args.attr
    # content tag target class or ID, format must be 'div.<class>' for classes or 'div#<ID>' for IDs, <div> or <span> tags
    ctag = args.ctag
    depth = args.depth
    log_level = args.log.upper()
    include = args.include
    exclude = args.exclude
    auto = args.auto
    output = args.output
    crawl_enabled = args.crawl
    print(helpers.info_message)
    url_input = input("Enter the starting URL: ").strip()
    if not helpers.validate_and_normalize_url(url_input):
        print("Invalid URL - please enter a valid URL starting with http:// or https://")
        return
    # target validation
    if not ctag:
        ctag_input = input("Enter the content container tag (e.g., 'div.class' or 'div#id') [optional]: ").strip()
        if ctag_input:
            if '.' in ctag_input or '#' in ctag_input:
                ctag = ctag_input
            else:
                print("Invalid format. Use 'div.class' or 'div#id'. Skipping.")
                ctag = None
    # validate depth
    if depth < 0:
        print("Invalid depth - please enter a non-negative integer.")
        return
    if depth == 2:
        print("Crawl depth is set to default at 2.")
        depth_input = input("Enter a new depth (0 for infinite, leave blank to keep default): ").strip()
        if depth_input:
            try:
                depth_input_val = int(depth_input)
                if depth_input_val < 0:
                    print("Invalid depth - must be 0 or greater. Using default of 2.")
                else:
                    depth = depth_input_val
            except ValueError:
                print("Invalid input. Depth must be a number. Using default of 2.")
    print(f"Crawl depth: {depth}")
    # validate log level
    if log_level == 'INFO':
        print("Log level is set to default at INFO.")
        log_input = input("Please enter a different value now or leave it blank to continue with default, (NONE, DEBUG, WARNING, ERROR, CRITICAL): ").strip().upper()
        if log_input:
            if log_input in ['NONE','DEBUG', 'WARNING', 'ERROR', 'CRITICAL']:
                log_level = log_input
            else: print(f"Invalid log level: {log_input} - please enter NONE, DEBUG, INFO, WARNING, ERROR, or CRITICAL.")
        else: log_level = 'INFO'
    settings.set('DEPTH_LIMIT', depth)
    if log_level == 'NONE':
        settings.set('LOG_ENABLED', False)
    else:
        settings.set('LOG_ENABLED', True)
        settings.set('LOG_LEVEL', log_level)
    print(f"\nSettings for the crawl:\n"
          f"Start URL: {url_input}\n" # start_url for 'process_crawl()'
          #f"Tag: {tag}\n"
          #f"Attribute: {attr}\n"
          f"Container Tag: {ctag}\n"
          f"Crawl Enabled: {crawl_enabled}\n"
          f"Crawl Depth: {depth}\n"
          f"Log Level: {log_level}\n")
    input("Press Enter to start the crawl with the above settings...")
    process_crawl(settings, spider_class, url_input, tag, attr, ctag, include, exclude, auto=auto, output=output, crawl_enabled=crawl_enabled)

def process_crawl(settings, spider_class, start_urls, tag, attr, ctag, include, exclude, auto=None, output=None, crawl_enabled=False):
    """
    Process the crawl with the given settings and spider parameters.
    """
    print("Executing crawl...")
    # update settings
    if auto == 'save':
        settings.set('AUTO_SAVE',True)
        settings.set('AUTO_VIEW',False)
    elif auto == 'view':
        settings.set('AUTO_SAVE',False)
        settings.set('AUTO_VIEW',True)
    else:
        settings.set('AUTO_SAVE',False)
        settings.set('AUTO_VIEW',False)
    if output:
        settings.set('OUTPUT_FILENAME', output)
    process = CrawlerProcess(settings)
    process.crawl(
        spider_class,
        start_urls=start_urls,
        tag=tag,
        attr=attr,
        ctag=ctag,
        include=include,
        exclude=exclude,
        crawl_enabled=crawl_enabled
    )
    process.start()

def main():
    parser = argparse.ArgumentParser(description="Recursive Link Spider with Scrapy by JDT")
    parser.add_argument('--spider', 
                        choices=['link','schema'], default='link', 
                        help="Deploy a specific spider: 'link' for LinkSpider, 'schema' for SchemaSpider (default: 'link')")
    parser.add_argument('--crawl', action='store_true', 
                        help="Enable link crawling (default is False for Schemaspider, True for Linkspider)")
    parser.add_argument('--url', default=None, help="Starting URL to crawl")
    parser.add_argument('--tag', default='a', help='HTML tag to search for links (default: "a")')
    parser.add_argument('--attr', default='href', help='Attribute containing the link (default: "href")')
    parser.add_argument('--ctag', default=None, help="Optional container tag with class or ID (e.g. div.article)")
    parser.add_argument('--depth', type=int, default=2, help="Crawl depth limit (0 means unlimited, default is 2)")
    parser.add_argument('--log', 
                        default='INFO', 
                        help='Logging level (default: INFO)') # opts: NONE, DEBUG, INFO, WARNING, ERROR, CRITICAL
    parser.add_argument('--include', 
                        default=None, 
                        help='Only include links that contain one or more comma-separated substrings (case-insensitive)')
    parser.add_argument('--exclude', 
                        default=None, 
                        help='Exclude links that contain one or more comma-separated substrings (case-insensitive)')
    parser.add_argument('--auto', 
                        choices=['save', 'view'], 
                        help="Auto output mode: 'save' to export CSV, 'view' to show table")
    parser.add_argument('--output', 
                        default=None, 
                        help='Optional filename (without extension) for CSV output')
    args = parser.parse_args()
    SPIDER_MAP = {
        'link': LinkSpider,
        'schema': SchemaSpider,
    }
    spider_class = SPIDER_MAP[args.spider]
    print(f"Deploying {spider_class}...")
    include = [s.strip().lower() for s in args.include.split(',')] if args.include else []
    exclude = [s.strip().lower() for s in args.exclude.split(',')] if args.exclude else []
    depth = args.depth
    if depth < 0 and depth.isdigit():
        print("Invalid depth - please enter a non-negative integer.")
        return
    # crawler settings
    settings = get_project_settings()
    settings.set('DEPTH_LIMIT', depth)
    if args.log.upper() in ['DEBUG','INFO','WARNING','ERROR','CRITICAL']:
        settings.set('LOG_ENABLED', True)
        settings.set('LOG_LEVEL', args.log.upper())
    elif args.log.upper() == 'NONE':
        settings.set('LOG_ENABLED', False)
    else:
        raise ValueError(f"Invalid log level: {args.log}. Use NONE, DEBUG, INFO, WARNING, ERROR, or CRITICAL.")
    if args.url is None:
        init_menu(args, spider_class, include, exclude)
    else:
        start_urls = [u.strip() for u in args.url.split(',') if helpers.validate_and_normalize_url(u.strip())]
        if not start_urls:
            print("Invalid URL - please enter a valid URL starting with http:// or https://")
            return
        process_crawl(
            settings, 
            spider_class, 
            start_urls, 
            args.tag,
            args.attr,
            args.ctag,
            include,
            exclude,
            args.auto,
            args.output,
            args.crawl,
            )

if __name__ == '__main__':
    main()