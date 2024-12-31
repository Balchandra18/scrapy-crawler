import scrapy
import os

class FilingsSpider(scrapy.Spider):
    name = 'multi_filings'

    def start_requests(self):
        url = os.getenv('TARGET_URL')
        docket_selector = os.getenv('DOCKET_SELECTOR')
        doc_link_selector = os.getenv('DOCUMENT_LINK_SELECTOR')

        yield scrapy.Request(
            url=url,
            callback=self.parse_dockets,
            cb_kwargs={'docket_selector': docket_selector, 
                       'doc_link_selector': doc_link_selector}
        )

    def parse_dockets(self, response, docket_selector, doc_link_selector):
        dockets = response.css(docket_selector).getall()
        for docket in dockets:
            docket_url = response.urljoin(docket)
            yield scrapy.Request(
                url=docket_url,
                callback=self.parse_documents,
                cb_kwargs={'doc_link_selector': doc_link_selector}
            )

    def parse_documents(self, response, doc_link_selector):
        for link in response.css(doc_link_selector).re(r'.*\.(pdf|docx|xlsx)'):
            yield {'file_url': response.urljoin(link)}
