# -*- coding: utf-8 -*-
# spiderfarm/spiderfarm/spiders/schemaspider.py
import scrapy
from scrapy import signals
import json
from urllib.parse import urlparse, urljoin
from collections import defaultdict
import helpers

TARGET_TYPES = {'Offer','Product','ProductGroup','SomeProducts','IndividualProduct','ProductCollection','ItemList','ListItem'}
GTIN_FIELDS = {'gtin','gtin8','gtin12','gtin13','gtin14'}

class SchemaSpider(scrapy.Spider):
    name = 'schemaspider'
    custom_settings = {}
    handle_httpstatus_list = [404,429]

    def __init__(self, start_urls=None, tag='a', attr='href', 
                 ctag=None, include=None, exclude=None, crawl_enabled=False, 
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [start_urls] if isinstance(start_urls, str) else start_urls or []
        parsed_domain = urlparse(self.start_urls[0])
        self.allowed_domains = [parsed_domain.netloc.replace('www.','')]
        self.tag = tag
        self.attr = attr
        self.ctag = ctag
        self.include = include or []
        self.exclude = exclude or []
        self.visited_urls = set()
        self.processed_json_ids = set()
        self.results = []
        self.crawl_enabled = crawl_enabled
        if self.start_urls:
            parsed_domain = urlparse(self.start_urls[0])
            self.allowed_domains = [parsed_domain.netloc.replace('www.','')]
        else:
            self.allowed_domains = []

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(SchemaSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signals.spider_closed)
        return spider

    def parse(self, response):
        current_url = response.url
        if current_url in self.visited_urls:
            return
        self.visited_urls.add(current_url)
        self.logger.info(f"PROCESSING: {current_url}")
        # extract
        scripts = response.xpath('//script[@type="application/ld+json"]/text()').getall()
        self.logger.info(f"EXTRACTING: {len(scripts)} valid JSON blocks")
        for block in scripts:
            try:
                data = json.loads(block)
                if isinstance(data, list):
                    for entry in data:
                        self.extract_target_data(entry, current_url)
                else:
                    self.extract_target_data(data, current_url)
            except json.JSONDecodeError:
                self.logger.warning("Invalid JSON block skipped.")
                continue
        # crawl if enabled
        if self.crawl_enabled:
            if self.ctag:
                container_xpath = helpers.get_container_xpath(self)
                elements = response.xpath(f'{container_xpath}//{self.tag}[@{self.attr}]')
            else:
                elements = response.xpath(f'//{self.tag}[@{self.attr}]')
            for el in elements:
                href = el.attrib.get(self.attr)
                if not href:
                    continue
                absolute_url = urljoin(current_url, href)
                normalized_url = helpers.validate_and_normalize_url(absolute_url)
                if not normalized_url:
                    continue
                if not self.is_valid_link(normalized_url):
                    continue
                yield scrapy.Request(normalized_url, callback=self.parse)

    def extract_target_data(self, obj, source_url):
        if '@type' not in obj:
            return
        types = obj['@type']
        if isinstance(types, str):
            types = [types]
        if not any(t in TARGET_TYPES for t in types):
            self.logger.debug(f"SKIPPING: {types} not in target schema types.")
            return
        # extract ItemList and ListItems
        if "ItemList" in types and "itemListElement" in obj:
            self.logger.debug(f"PROCESSING ItemList with nested ListItems from {source_url}")
            self.results.append({
                'name': obj.get('name',''),
                'url': obj.get('url',source_url),
                'price': '',
                'gtin': '',
                'source': source_url,
                'type': 'ItemList'
            })
            for item in obj['itemListElement']:
                if isinstance(item,dict):
                    item_type=item.get('@type','')
                    if item_type == 'ListItem':
                        self.results.append({
                            'name': item.get('name',''),
                            'url': item.get('url',source_url),
                            'price': '',
                            'gtin': '',
                            'source': source_url,
                            'type': 'ListItem'
                        })
            return
        # extract ProductGroup
        if "ProductGroup" in types:
            self.logger.debug(f"PROCESSING ProductGroup from {source_url}")
            name = obj.get("name","")
            url = obj.get("url",source_url)
            gtin = self.extract_gtin(obj)
            offer = obj.get("offers",{})
            if isinstance(offer,dict) and offer.get("itemCondition") == "https://schema.org/NewCondition":
                self.results.append({
                    "name": name,
                    "url": offer.get("url",url),
                    "price": offer.get("price",''),
                    "gtin": gtin,
                    "source": source_url,
                    "type": "ProductGroup",
                })
            # evaluate and process variants/Products
            for variant in obj.get("hasVariant", []):
                if not isinstance(variant,dict):
                    continue
                if variant.get("@type") != "Product":
                    continue
                variant_name = variant.get("name", "")
                variant_gtin = self.extract_gtin(variant)
                variant_offer = variant.get("offers",{})
                if isinstance(variant_offer,dict) and variant_offer.get("itemCondition") == "https://schema.org/NewCondition":
                    self.results.append({
                        "name": variant_name,
                        "url": variant_offer.get("url",url),
                        "price": variant_offer.get("price",''),
                        "gtin": variant_gtin,
                        "source": source_url,
                        "type": "Product",
                    })
            return
        # prevent re-processing
        json_id = self.get_unique_id(obj)
        if json_id in self.processed_json_ids:
            return
        self.processed_json_ids.add(json_id)
        # product/offer fallback handling
        name = obj.get('name','')
        url = obj.get('url', source_url)
        price = self.extract_price(obj)
        gtin = self.extract_gtin(obj)
        if name or gtin:
            self.results.append({
                'name': name,
                'url': url,
                'price': price,
                'gtin': gtin,
                'source': source_url,
                'type': ','.join(types)
            })

    def extract_price(self, obj):
        if 'offers' in obj:
            offers = obj['offers']
            if isinstance(offers,list):
                for offer in offers:
                    if isinstance(offer,dict) and 'price' in offer:
                        return offer.get('price')
            elif isinstance(offers,dict):
                return offers.get('price')
        return obj.get('price', '')

    def extract_gtin(self, obj):
        for field in GTIN_FIELDS:
            if field in obj:
                return obj[field]
        return ''

    def get_unique_id(self, obj):
        # uid gen for dup catalog
        parts = [
            obj.get('name','').strip().lower(),
            self.extract_gtin(obj) or '',
            obj.get('url','').strip().lower()
        ]
        return '|'.join(parts)

    def is_valid_link(self, url):
        parsed = urlparse(url)
        if parsed.scheme not in ('http','https'):
            return False
        base_domain = parsed.netloc.replace('www.','')
        if not any(base_domain.endswith(allowed) for allowed in self.allowed_domains):
            return False
        path = parsed.path.lower()
        if any(path.endswith(ext) for ext in helpers.NON_HTML_EXTENSIONS):
            return False
        url_lower = url.lower()
        if self.include and not any(s in url_lower for s in self.include):
            return False
        if self.exclude and any(s in url_lower for s in self.exclude):
            return False
        if url in self.visited_urls:
            return False
        return True

    def spider_closed(self, reason):
        if not self.results:
            self.logger.info("No schema data extracted.")
            return
        headers = ['name','url','price','gtin','source','type']
        table_data = [[
            r.get('name',''),
            r.get('url',''),
            r.get('price',''),
            r.get('gtin',''),
            r.get('source',''),
            r.get('type','')
        ] for r in self.results]
        auto_view = self.settings.getbool('AUTO_VIEW',False)
        auto_save = self.settings.getbool('AUTO_SAVE',False)
        output_filename = self.settings.get('OUTPUT_FILENAME')
        helpers.data_handling_options(
            table_data,
            headers,
            auto_view=auto_view,
            auto_save=auto_save,
            output_filename=output_filename,
            seed_url=self.start_urls[0] if self.start_urls else None,
            spider_name=self.name
        )
