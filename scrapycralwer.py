import scrapy
from azure.storage.blob import BlobServiceClient


class DocketScraper(scrapy.Spider):
    name = "docket_scraper"

    # Start URL with docket number
    start_urls = [
        "https://www.fgb.com"
    ]

    # Azure Blob Storage configuration
    azure_connection_string = "<AZURE_CONNECTION_STRING>"  # Replace with your Azure connection string
    container_name = "<CONTAINER_NAME>"  # Replace with your Azure container name

    def parse(self, response):
        # Locate all clickable document links on the page
        document_links = response.xpath(
            "//a[contains(@href, '.pdf') or contains(@href, '.docx')]"
        )

        for document_link in document_links:
            document_name = document_link.xpath("text()").get()
            document_url = response.urljoin(document_link.xpath("@href").get())

            yield scrapy.Request(
                url=document_url,
                callback=self.download_and_upload_document,
                cb_kwargs={"document_name": document_name},
            )

    def download_and_upload_document(self, response, document_name):
        # Determine file type based on Content-Type or file extension
        file_extension = document_name.split('.')[-1].lower()

        if file_extension in ["pdf", "docx"]:
            try:
                # Connect to Azure Blob Storage
                blob_service_client = BlobServiceClient.from_connection_string(
                    self.azure_connection_string
                )
                blob_client = blob_service_client.get_blob_client(
                    container=self.container_name, blob=document_name
                )

                # Upload the document content directly to Azure Blob Storage
                blob_client.upload_blob(response.body, overwrite=True)
                self.logger.info(f"Uploaded {document_name} to Azure Blob Storage.")
            except Exception as e:
                self.logger.error(f"Failed to upload {document_name} to Azure Blob Storage: {e}")
        else:
            self.logger.warning(f"Unsupported file type for {document_name}. Skipping.")
