# spiderfarm/spiderfarm/spiders/linkspider.py
import scrapy
from scrapy import signals
from collections import defaultdict
from urllib.parse import urljoin, urlparse
import helpers

class LinkSpider(scrapy.Spider):
    name = 'linkspider'
    custom_settings = {}
    handle_httpstatus_list = [404]
    
    def __init__(self, start_url=None, tag='a', attr='href', ctag=None, include=None, exclude=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [start_url]
        self.tag = tag
        self.attr = attr
        self.ctag = ctag
        self.url_seen = defaultdict(set)  # url -> set of sources
        self.scraped_data = [] # list to store scraped data
        if start_url:
            parsed = urlparse(start_url)
            domain = parsed.netloc
            self.allowed_domains = [domain]
            if domain.startswith('www.'):
                self.allowed_domains.append(domain.replace('www.', ''))
        self.NON_HTML_EXTENSIONS = (
        '.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.pdf', '.doc', 
        '.docx', '.xls', '.xlsx', '.js', '.css', '.ico', '.zip', '.rar', 
        '.exe', '.mp4', '.mp3', '.avi', '.mov', '.wmv'
        )
        self.include = include or []
        self.exclude = exclude or []
    
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(LinkSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signals.spider_closed)
        return spider

    def parse(self, response):
        url = response.url
        source = response.request.headers.get('Referer', b'[seed]').decode()
        if source in self.url_seen[url]:
            self.logger.debug(f"SKIPPED: Duplicate {url} from same source {source}")
            return
        self.url_seen[url].add(source)
        self.logger.info(f"DISCOVERED: {url} / source: {source}")
        # page info extraction
        page_info = {
            'url': url,
            'status': response.status,
            'title': response.xpath('//title/text()').get(default='').strip(),
            'meta_description': response.xpath("//meta[@name='description']/@content").get(default='').strip(),
            'canonical': response.xpath("//link[@rel='canonical']/@href").get(default='').strip(),
            'source': source
        }
        self.scraped_data.append(page_info)
        yield page_info
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
            link_lower = link.lower()
            # include filter
            if self.include and not any(s in link_lower for s in self.include):
                self.logger.debug(f"SKIPPED: {link} from {url} - Not included in filter '{self.include}'")
                continue
            #exclude filter
            if self.exclude and not any(s in link_lower for s in self.exclude):
                self.logger.debug(f"SKIPPED: {link} from {url} - Excluded by filter '{self.exclude}'")
                continue
            # resolve and normalize url
            absolute_url = urljoin(response.url, link)
            normalized_url = helpers.validate_and_normalize_url(absolute_url)
            # skip invalid or non-https urls
            if not normalized_url:
                self.logger.debug(f"SKIPPED: {link} from {url} - Invalid or non-HTTPS URL")
                continue
            # skip non-HTML resources
            if any(normalized_url.lower().endswith(ext) for ext in self.NON_HTML_EXTENSIONS):
                self.logger.debug(f"SKIPPED: {normalized_url} - Non-HTML resource")
                continue
            # check domain scope
            parsed_url = urlparse(normalized_url)
            if self.allowed_domains:
                if parsed_url.netloc not in self.allowed_domains:
                    self.logger.debug(f"SKIPPED: {normalized_url} - Not within domain scope")
                    continue
            # skip duplicates
            if source in self.url_seen[normalized_url]:
                continue
            try:
                yield response.follow(
                    normalized_url, 
                    callback=self.parse, 
                    headers={'Referer': url}
                    )
            except Exception as e:
                self.logger.error(f"SKIPPED: {normalized_url} - Malformed URL or error: {str(e)}")

    def spider_closed(self, spider):
        """
        Called when the spider is closed and crawl is complete.
        Converts scraped data to table format for processing.
        """
        if not self.scraped_data:
            self.logger.info("No data scraped.")
            return
        headers = ['url','status','title','meta_description','canonical_link','source_page']
        table_data = [[
            page_data.get("url",""),
            page_data.get("status",""),
            page_data.get("title",""),
            page_data.get("meta_description",""),
            page_data.get("canonical",""),
            page_data.get("source",""),
        ] for page_data in self.scraped_data]
        auto_view = self.settings.getbool('AUTO_VIEW',False)
        auto_save = self.settings.getbool('AUTO_SAVE',False)
        output_filename = self.settings.get('OUTPUT_FILENAME')
        helpers.data_handling_options(
            table_data, 
            headers, 
            auto_view=auto_view, 
            auto_save=auto_save,
            output_filename=output_filename,
            seed_url=self.start_urls[0] if self.start_urls else None
        )