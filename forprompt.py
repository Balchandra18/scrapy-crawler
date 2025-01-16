import logging
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import re
import requests
from bs4 import BeautifulSoup
from azure.storage.blob import BlobServiceClient

# Configure structured logging for PromptFlow
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]  # Output logs to console for PromptFlow
)

app = FastAPI()

# Define request and response models for structured inputs/outputs
class ScrapeRequest(BaseModel):
    urls: list[str]

class ScrapeResponse(BaseModel):
    status: str
    message: str
    details: list[dict]

# Azure Blob Storage setup
AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING", "")
CONTAINER_NAME = os.getenv("CONTAINER_NAME", "")
if not AZURE_CONNECTION_STRING or not CONTAINER_NAME:
    logging.error("Azure connection string or container name is not set.")

blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)

# Helper functions
def get_year_from_url(url):
    match = re.search(r"/(\d{4})-\d{5}", url)
    return match.group(1) if match else "unknown_year"

def get_case_number_from_url(url):
    match = re.search(r"(\d{4}-\d{5})", url)
    return match.group(1) if match else "unknown_case"

def download_and_upload_document(document_url, year, case_number, document_name):
    try:
        logging.info(f"Downloading document: {document_url}")
        response = requests.get(document_url, stream=True)
        response.raise_for_status()

        blob_client = container_client.get_blob_client(blob=f"{year}/{case_number}/{document_name}")
        blob_client.upload_blob(response.content, overwrite=True)
        logging.info(f"Uploaded to Azure Blob Storage: {year}/{case_number}/{document_name}")
        return {"document_url": document_url, "status": "uploaded", "path": f"{year}/{case_number}/{document_name}"}
    except Exception as e:
        logging.error(f"Error processing document {document_url}: {e}")
        return {"document_url": document_url, "status": "error", "error": str(e)}

def scrape_case_documents(url):
    year = get_year_from_url(url)
    case_number = get_case_number_from_url(url)
    results = []

    try:
        logging.info(f"Scraping URL: {url}")
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        document_links = soup.find_all('a', href=re.compile(r'\.(pdf|docx|txt|xls)$'))

        for link in document_links:
            document_url = link['href']
            document_name = link.text.strip() or document_url.split('/')[-1]
            full_document_url = requests.compat.urljoin(url, document_url)
            result = download_and_upload_document(full_document_url, year, case_number, document_name)
            results.append(result)

        return results
    except Exception as e:
        logging.error(f"Error scraping {url}: {e}")
        raise HTTPException(status_code=500, detail=f"Error scraping {url}: {e}")

# FastAPI endpoint
@app.post("/scrape", response_model=ScrapeResponse)
def scrape(request: ScrapeRequest):
    overall_results = []
    for url in request.urls:
        try:
            results = scrape_case_documents(url)
            overall_results.extend(results)
        except Exception as e:
            logging.error(f"Error processing URL {url}: {e}")
            overall_results.append({"url": url, "status": "error", "error": str(e)})

    return {
        "status": "completed",
        "message": "Scraping completed with some results.",
        "details": overall_results
    }

