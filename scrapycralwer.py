import scrapy
from azure.storage.blob import BlobServiceClient
from twisted.internet import reactor

class DocketScraper(scrapy.Spider):
    name = "docket_scraper"

    start_urls = [
        "<URL_1>",  # Replace with your first URL
        "<URL_2>",  # Replace with your second URL
        "<URL_3>"   # Replace with your third URL
    ]

    # Azure Blob Storage configuration
    azure_connection_string = "<AZURE_CONNECTION_STRING>"  # Replace with your Azure connection string
    container_name = "<CONTAINER_NAME>"  # Replace with your Azure container name

    def parse(self, response):
        docket_number = self.get_docket_number_from_url(response.url)  # Extract docket number from URL
        
        for document_link in response.xpath("//a[contains(@href, '.pdf') or contains(@href, '.docx')]"):
            document_name = document_link.xpath("text()").get()
            document_url = response.urljoin(document_link.xpath("@href").get())

            yield scrapy.Request(
                url=document_url,
                callback=self.download_and_upload_document,
                cb_kwargs={
                    "folder_name": docket_number,
                    "document_name": document_name,
                },
            )

    def get_docket_number_from_url(self, url):
        import re
        match = re.search(r"DocketNumber=([A-Za-z0-9-]+)", url)
        return match.group(1) if match else "unknown_docket"

    def download_and_upload_document(self, response, folder_name, document_name):
        content_type = response.headers.get('Content-Type', b'').decode('utf-8')
        file_extension = document_name.split('.')[-1].lower()

        if content_type in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"] or file_extension in ["pdf", "docx"]:
            try:
                blob_service_client = BlobServiceClient.from_connection_string(self.azure_connection_string)
                blob_client = blob_service_client.get_blob_client(
                    container=self.container_name, 
                    blob=f"{folder_name}/{document_name}"
                )

                blob_client.upload_blob(response.body, overwrite=True)
                self.logger.info(f"Uploaded {document_name} to folder {folder_name} in Azure Blob Storage.")
            except Exception as e:
                self.logger.error(f"Failed to upload {document_name} to Azure Blob Storage: {e}")
        else:
            self.logger.warning(f"Unsupported file type for {document_name}. Skipping.")

if _name_ == "_main_":
    from scrapy.crawler import CrawlerProcess
    from twisted.internet.asyncioreactor import install

    install()  # Use AsyncioSelectorReactor for signal handling

    process = CrawlerProcess()
    process.crawl(DocketScraper)
    process.start()
