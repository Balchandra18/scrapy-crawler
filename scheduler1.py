from fastapi import FastAPI
from pydantic import BaseModel
import os
import re
import requests
from bs4 import BeautifulSoup
from azure.storage.blob import BlobServiceClient
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Initialize FastAPI
app = FastAPI()

# Azure Key Vault setup
VAULT_URL = os.getenv("AZURE_KEYVAULT_URL")
credential = DefaultAzureCredential()
secret_client = SecretClient(vault_url=VAULT_URL, credential=credential)

# Fetch secrets from Key Vault
AZURE_CONNECTION_STRING = secret_client.get_secret("AzureConnectionString").value
CONTAINER_NAME = secret_client.get_secret("ContainerName").value

# Initialize Azure Blob Storage client
blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)

class ScrapeRequest(BaseModel):
    urls: list[str]

def get_year_from_url(url):
    match = re.search(r"/(\d{4})-\d{5}", url)
    return match.group(1) if match else "unknown_year"

def get_case_number_from_url(url):
    match = re.search(r"(\d{4}-\d{5})", url)
    return match.group(1) if match else "unknown_case"

def download_and_upload_document(document_url, year, case_number, document_name):
    try:
        response = requests.get(document_url, stream=True)
        response.raise_for_status()

        blob_client = container_client.get_blob_client(blob=f"{year}/{case_number}/{document_name}")
        blob_client.upload_blob(response.content, overwrite=True)
        print(f"Uploaded {document_name} to {year}/{case_number} in Azure Blob Storage.")
    except Exception as e:
        print(f"Failed to process {document_url}: {e}")

def scrape_case_documents(url):
    year = get_year_from_url(url)
    case_number = get_case_number_from_url(url)

    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        document_links = soup.find_all('a', href=re.compile(r'\.(pdf|docx|txt|xls)$'))

        for link in document_links:
            document_url = link['href']
            document_name = link.text.strip() or document_url.split('/')[-1]
            full_document_url = requests.compat.urljoin(url, document_url)
            download_and_upload_document(full_document_url, year, case_number, document_name)
    except Exception as e:
        print(f"Error while scraping {url}: {e}")

@app.post("/scrape")
def scrape(request: ScrapeRequest):
    for url in request.urls:
        scrape_case_documents(url)
    return {"status": "success", "message": "Scraping completed."}

# Scheduler setup
scheduler = BackgroundScheduler()

def scheduled_scraping_job():
    urls = ["<URL_1>", "<URL_2>"]  # Replace with your target URLs
    for url in urls:
        scrape_case_documents(url)

scheduler.add_job(scheduled_scraping_job, CronTrigger(hour=0, minute=0))
scheduler.start()

@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown()
