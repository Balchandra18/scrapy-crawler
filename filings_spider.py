import scrapy
import json
import os
from urllib.parse import urljoin

class FilingsSpider(scrapy.Spider):
    name = 'multi_docs'

    def start_requests(self):
        # Load websites configuration
        with open('websites.json', 'r') as f:
            websites = json.load(f)

        for site in websites:
            yield scrapy.Request(
                url=site['url'],
                callback=self.parse_dockets,
                cb_kwargs={'docket_selector': site['docket_selector'], 
                           'document_link_selector': site['document_link_selector']}
            )

    def parse_dockets(self, response, docket_selector, document_link_selector):
        # Extract docket numbers
        dockets = response.css(docket_selector).getall()
        self.log(f"Found dockets: {dockets}")

        for docket in dockets:
            docket_url = urljoin(response.url, docket)  # Assuming docket forms part of the URL
            yield scrapy.Request(
                url=docket_url,
                callback=self.parse_documents,
                cb_kwargs={'document_link_selector': document_link_selector}
            )

    def parse_documents(self, response, document_link_selector):
        # Extract document links for the docket
        for link in response.css(document_link_selector).re(r'.*\.(pdf|docx|xlsx)'):
            absolute_url = response.urljoin(link)
            yield scrapy.Request(absolute_url, callback=self.download_file)

    def download_file(self, response):
        file_name = response.url.split('/')[-1]
        local_path = f"downloads/{file_name}"

        # Save the file locally
        os.makedirs('downloads', exist_ok=True)
        with open(local_path, 'wb') as f:
            f.write(response.body)
        
        self.log(f"Downloaded file: {file_name}")

        # Pass to pipeline for scanning and uploading
        yield {
            'file_path': local_path,
            'file_name': file_name,
        }
