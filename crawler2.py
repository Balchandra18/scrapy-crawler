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

def get_year_from_url(url):
    """Extract year from the URL (e.g., 2014, 2016)."""
    match = re.search(r"/(\d{4})-\d{5}", url)
    return match.group(1) if match else "unknown_year"

def get_case_number_from_url(url):
    """Extract case number from the URL."""
    match = re.search(r"(\d{4}-\d{5})", url)
    return match.group(1) if match else "unknown_case"

def download_and_upload_document(document_url, year, case_number, document_name):
    """Download a document and upload it to Azure Blob Storage."""
    try:
        # Download the document
        response = requests.get(document_url, stream=True)
        response.raise_for_status()

        # Create folder structure: <Year>/<CaseNumber>/<DocumentName>
        blob_client = container_client.get_blob_client(blob=f"{year}/{case_number}/{document_name}")
        blob_client.upload_blob(response.content, overwrite=True)
        print(f"Uploaded {document_name} to {year}/{case_number} in Azure Blob Storage.")
    except Exception as e:
        print(f"Failed to process {document_url}: {e}")

def scrape_case_documents(url):
    """Scrape the webpage for document links and upload them."""
    year = get_year_from_url(url)
    case_number = get_case_number_from_url(url)
    
    try:
        # Fetch the webpage content
        response = requests.get(url)
        response.raise_for_status()

        # Parse the webpage
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all links with .pdf or .docx (or any other document types you want)
        document_links = soup.find_all('a', href=re.compile(r'\.(pdf|docx|txt|xls)$'))

        for link in document_links:
            document_url = link['href']
            document_name = link.text.strip() or document_url.split('/')[-1]
            full_document_url = requests.compat.urljoin(url, document_url)

            # Download and upload each document
            download_and_upload_document(full_document_url, year, case_number, document_name)
    except Exception as e:
        print(f"Error while scraping {url}: {e}")

if _name_ == "_main_":
    # List of URLs to scrape for different years
    urls = [
        # URLs for 2014
        "https://psc.ky.gov/Case/ViewCaseFilings/2014-00371",
        "https://psc.ky.gov/Case/ViewCaseFilings/2014-00371/Post",
        "https://psc.ky.gov/Case/ViewCaseFilings/2014-00372",
        "https://psc.ky.gov/Case/ViewCaseFilings/2014-00371/Post",

        # URLs for 2016
        "https://psc.ky.gov/Case/ViewCaseFilings/2016-00370",
        "https://psc.ky.gov/Case/ViewCaseFilings/2016-00371/Post",
        "https://psc.ky.gov/Case/ViewCaseFilings/2016-00371",
        "https://psc.ky.gov/Case/ViewCaseFilings/2016-00371/Post"
    ]

    # Process each URL
    for url in urls:
        scrape_case_documents(url)
