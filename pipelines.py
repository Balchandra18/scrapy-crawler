import os
from azure.storage.blob import BlobServiceClient
from azure.mgmt.security import SecurityCenter
from azure.mgmt.security.models import SecurityAssessment
from azure.identity import DefaultAzureCredential

class AzureDefenderPipeline:
    def __init__(self, blob_service_url, filtered_container, quarantine_container):
        self.blob_service_client = BlobServiceClient.from_connection_string(blob_service_url)
        self.filtered_container = filtered_container
        self.quarantine_container = quarantine_container
        self.security_client = SecurityCenter(credential=DefaultAzureCredential())

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            blob_service_url=crawler.settings.get('AZURE_BLOB_CONNECTION_STRING'),
            filtered_container=crawler.settings.get('FILTERED_CONTAINER'),
            quarantine_container=crawler.settings.get('QUARANTINE_CONTAINER'),
        )

    def scan_file_with_azure_defender(self, file_path):
        # Simulate Azure Defender scan (mocked here)
        # Replace with real Defender API integration for file scanning
        if 'bad' in file_path:  # Assume files with "bad" are malicious
            return False
        return True

    def upload_to_blob(self, container_name, file_path, file_name):
        blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=file_name)
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        return blob_client.url

    def process_item(self, item, spider):
        file_path = item['file_path']
        file_name = item['file_name']
        
        # Scan with Azure Defender
        is_clean = self.scan_file_with_azure_defender(file_path)
        
        if is_clean:
            # Upload to filtered container
            self.upload_to_blob(self.filtered_container, file_path, file_name)
            spider.log(f"Uploaded clean file: {file_name}")
        else:
            # Upload to quarantine container
            self.upload_to_blob(self.quarantine_container, file_path, file_name)
            spider.log(f"Uploaded malicious file to quarantine: {file_name}")
        
        # Clean up local files
        os.remove(file_path)
        return item
