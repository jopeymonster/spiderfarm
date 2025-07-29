# spiderfarm/spiderfarm/spiders/linkspider.py
import scrapy
from collections import defaultdict
from urllib.parse import urljoin, urlparse
import helpers

class LinkSpider(scrapy.Spider):
    name = 'linkspider'
    custom_settings = {} # custom settings for later use
    
    def __init__(self, start_url=None, tag='a', attr='href', ctag=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [start_url]
        self.tag = tag
        self.attr = attr
        self.ctag = ctag
        self.url_seen = defaultdict(set)  # url -> set of sources
    
    def parse(self, response):
        url = response.url
        source = response.request.headers.get('Referer', b'[entry]').decode()
        if source in self.url_seen[url]:
            self.logger.info(f"Duplicate {url} from same source {source} — Skipping")
            return
        self.url_seen[url].add(source)
        self.logger.info(f"Processing: {url} / source: {source}")
        # page info extraction
        yield {
            'url': url,
            'status': response.status,
            'title': response.xpath('//title/text()').get(default='').strip(),
            'meta_description': response.xpath("//meta[@name='description']/@content").get(default='').strip(),
            'canonical': response.xpath("//link[@rel='canonical']/@href").get(default='').strip(),
            'source': source
        }
        # scoped container tag handling
        if self.ctag:
            container_xpath = helpers.get_container_xpath(self)
            elements = response.xpath(f'{container_xpath}//{self.tag}[@{self.attr}]')
        else:
            elements = response.xpath(f'//{self.tag}[@{self.attr}]')
        # targeted links extraction
        for element in elements:
            link = element.attrib.get(self.attr)
            if not link:
                continue
            absolute_url = urljoin(response.url, link)
            normalized_url = helpers.validate_and_normalize_url(absolute_url)
            if not normalized_url: # skip invalid or non-http(s) URLs
                continue
            if source in self.url_seen[normalized_url]:
                continue
            yield response.follow(normalized_url, callback=self.parse, headers={'Referer': url})