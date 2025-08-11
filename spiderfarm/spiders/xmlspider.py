# -*- coding: utf-8 -*-
# spiderfarm/spiderfarm/spiders/xmlspider.py
import scrapy
from scrapy.spiders import XMLFeedSpider
from scrapy import signals
from urllib.parse import urlparse
from collections import defaultdict
import helpers

class XMLSpider(scrapy.Spider):
    name = 'xmlspider'
    handle_httpstatus_list = [301, 302, 403, 404, 429]

    def __init__(self, start_urls=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [start_urls] if isinstance(start_urls, str) else (start_urls or [])
        self.scraped_data = []
        self.url_seen = set()

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signals.spider_closed)
        return spider

    def parse(self, response):
        urls = response.xpath('//*[local-name()="url"]/*[local-name()="loc"]/text()').getall()
        count = 0
        for loc in urls:
            loc = helpers.validate_and_normalize_url(loc)
            if loc and loc not in self.url_seen:
                self.url_seen.add(loc)
                yield scrapy.Request(loc, callback=self.parse_status, headers={'Referer': response.url})
                count+=1
                if count % 250 == 0:
                    self.logger.info("PROCESSED %d <url> nodes...",count)

    def parse_status(self, response):
        self.scraped_data.append({'url': response.url, 'status': response.status})

    def spider_closed(self, spider):
        if not self.scraped_data:
            self.logger.info("No data scraped.")
            return
        headers = ['url', 'status']
        table_data = [[r['url'], r['status']] for r in self.scraped_data]
        helpers.data_handling_options(
            table_data,
            headers,
            auto_view=self.settings.getbool('AUTO_VIEW', False),
            auto_save=self.settings.getbool('AUTO_SAVE', False),
            output_filename=self.settings.get('OUTPUT_FILENAME'),
            seed_url=self.start_urls[0] if self.start_urls else None,
            spider_name=self.name,
        )