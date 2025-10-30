# -*- coding: utf-8 -*-
# spiderfarm/spiders/feedspider.py
import scrapy
import gzip
import io
import xml.etree.ElementTree as ET
from scrapy import signals
from urllib.parse import urlparse
import helpers


class FeedSpider(scrapy.Spider):
    name = "feedspider"
    handle_httpstatus_list = [301, 302, 403, 404, 429]

    def __init__(self, start_urls=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [start_urls] if isinstance(start_urls, str) else (start_urls or [])
        self.scraped_data = []
        self.item_count = 0
        self.allowed_domains = []
        if self.start_urls:
            parsed = urlparse(self.start_urls[0])
            domain = parsed.netloc
            self.allowed_domains = [domain]
            if domain.startswith('www.'):
                self.allowed_domains.append(domain.replace('www.', ''))

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(FeedSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signals.spider_closed)
        return spider

    def parse_feed(self, xml_text):
        """Parse the XML feed content (string)."""
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            self.logger.error(f"XML parsing error: {e}")
            return
        # namespace handling (Google feeds use g:)
        nsmap = {"g": "http://base.google.com/ns/1.0"}
        # locate all <item> nodes under <rss><channel>
        items = root.findall(".//item", nsmap)
        for item in items:
            row = {}
            for child in item:
                tag_name = child.tag
                # strip namespace prefixes ({http://base.google.com/ns/1.0}mpn -> mpn)
                if "}" in tag_name:
                    tag_name = tag_name.split("}", 1)[1]
                if tag_name == "additional_image_link":
                    continue
                text = helpers.clean_value(self, value=child.text if child.text is not None else "")
                row[tag_name] = text

            if row:
                self.scraped_data.append(row)
                self.item_count += 1
                if self.item_count % 250 == 0:
                    self.logger.info("Processed %d <item> entries so far", self.item_count)

    def parse(self, response):
        """Handles feed retrieval, decompression (if needed), and XML parsing."""
        self.logger.info("Fetching feed from %s", response.url)
        content = response.body
        if response.url.endswith(".gz") or response.headers.get("Content-Encoding") == b"gzip":
            self.logger.info("Detected gzip-compressed feed, decompressing...")
            try:
                with gzip.GzipFile(fileobj=io.BytesIO(content)) as gz:
                    content = gz.read()
            except Exception as e:
                self.logger.error(f"Failed to decompress feed: {e}")
                return
        xml_text = content.decode("utf-8", errors="ignore")
        self.parse_feed(xml_text)

    def spider_closed(self, spider):
        if not self.scraped_data:
            self.logger.info("No items extracted from feed.")
            return
        # build headers from first item keys
        headers = list(self.scraped_data[0].keys())
        table_data = [[row.get(h, "") for h in headers] for row in self.scraped_data]
        auto_view = self.settings.getbool("AUTO_VIEW", False)
        auto_save = self.settings.getbool("AUTO_SAVE", False)
        output_filename = self.settings.get("OUTPUT_FILENAME")
        helpers.data_handling_options(
            table_data,
            headers,
            auto_view=auto_view,
            auto_save=auto_save,
            output_filename=output_filename,
            seed_url=self.start_urls[0] if self.start_urls else None,
            spider_name=self.name,
        )
        self.logger.info("FeedSpider finished: %d items extracted.\n", self.item_count)
