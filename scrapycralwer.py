import os
import re
import requests
from bs4 import BeautifulSoup
from azure.storage.blob import BlobServiceClient

# Azure Blob Storage configuration
AZURE_CONNECTION_STRING = "<AZURE_CONNECTION_STRING>"  # Replace with your Azure connection string
CONTAINER_NAME = "<CONTAINER_NAME>"  # Replace with your Azure container name

# Initialize Azure Blob Storage client
blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)

def get_docket_number_from_url(url):
    """Extract docket number from the URL."""
    match = re.search(r"DocketNumber=([A-Za-z0-9-]+)", url)
    return match.group(1) if match else "unknown_docket"

def download_and_upload_document(document_url, folder_name, document_name):
    """Download a document and upload it to Azure Blob Storage."""
    try:
        # Download the document
        response = requests.get(document_url, stream=True)
        response.raise_for_status()

        # Upload the document to Azure Blob Storage
        blob_client = container_client.get_blob_client(blob=f"{folder_name}/{document_name}")
        blob_client.upload_blob(response.content, overwrite=True)
        print(f"Uploaded {document_name} to folder {folder_name} in Azure Blob Storage.")
    except Exception as e:
        print(f"Failed to process {document_url}: {e}")

def scrape_documents(url):
    """Scrape the webpage for document links and upload them."""
    docket_number = get_docket_number_from_url(url)
    
    try:
        # Fetch the webpage content
        response = requests.get(url)
        response.raise_for_status()

        # Parse the webpage
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all links with .pdf or .docx
        document_links = soup.find_all('a', href=re.compile(r'\.(pdf|docx)$'))
        
        for link in document_links:
            document_url = link['href']
            document_name = link.text.strip() or document_url.split('/')[-1]
            full_document_url = requests.compat.urljoin(url, document_url)

            # Download and upload each document
            download_and_upload_document(full_document_url, docket_number, document_name)
    except Exception as e:
        print(f"Error while scraping {url}: {e}")

if _name_ == "_main_":
    # List of URLs to scrape
    urls = [
        "https://www.abc.com"
    ]

    # Process each URL
    for url in urls:
        scrape_documents(url)
