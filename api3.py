from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
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

app = FastAPI()

class ScrapeRequest(BaseModel):
    urls: list[str]

def get_docket_number_from_url(url):
    """Extract docket number from the URL."""
    match = re.search(r"docket/(\d+)", url)
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
    results = {"url": url, "docket_number": docket_number, "documents": []}

    try:
        # Ensure the folder exists in the Azure container
        folder_name = docket_number
        container_client.get_blob_client(blob=f"{folder_name}/").upload_blob(b"", overwrite=True)

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
            download_and_upload_document(full_document_url, folder_name, document_name)
            results["documents"].append({"name": document_name, "url": full_document_url})
    except Exception as e:
        print(f"Error while scraping {url}: {e}")
        raise HTTPException(status_code=500, detail=f"Error while scraping {url}: {e}")

    return results

@app.post("/scrape")
async def scrape_endpoint(request: ScrapeRequest):
    """API endpoint to scrape documents from a list of URLs."""
    results = []
    for url in request.urls:
        try:
            print(f"Processing URL: {url}")
            result = scrape_documents(url)
            results.append(result)
        except Exception as e:
            results.append({"url": url, "error": str(e)})
    return {"results": results}
