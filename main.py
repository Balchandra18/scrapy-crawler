import os
import re
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from azure.storage.blob import BlobServiceClient

# Environment variables
AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("CONTAINER_NAME")

# Initialize Azure Blob Storage client
blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)

app = FastAPI()

def get_docket_number_from_url(url):
    match = re.search(r"DocketNumber=([A-Za-z0-9-]+)", url)
    return match.group(1) if match else "unknown_docket"

def download_and_upload_document(document_url, folder_name, document_name):
    try:
        response = requests.get(document_url, stream=True)
        response.raise_for_status()
        blob_client = container_client.get_blob_client(blob=f"{folder_name}/{document_name}")
        blob_client.upload_blob(response.content, overwrite=True)
        return f"Uploaded {document_name} to {folder_name}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scrape")
async def scrape_documents(url: str):
    docket_number = get_docket_number_from_url(url)
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        document_links = soup.find_all('a', href=re.compile(r'\.(pdf|docx)$'))
        results = []
        for link in document_links:
            document_url = requests.compat.urljoin(url, link['href'])
            document_name = link.text.strip() or document_url.split('/')[-1]
            result = download_and_upload_document(document_url, docket_number, document_name)
            results.append(result)
        return {"message": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error while scraping {url}: {e}")
