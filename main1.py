main.py:

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
from kypuc_scrape import *

# Initialize FastAPI
app = FastAPI()

class ScrapeRequest(BaseModel):
    urls: list[str]

@app.post("/scrape")
def scrape(request: ScrapeRequest):
    for url in request.urls:
        scrape_case_documents(url)
    return {"status": "success", "message": "Scraping completed."}

# Scheduler setup
scheduler = BackgroundScheduler()

def scheduled_scraping_job():
    # Define the URLs to scrape
    urls = ["<URL_1>", "<URL_2>"]  # Replace with your target URLs
    for url in urls:
        scrape_case_documents(url)

# Add a daily schedule (e.g., run at 12:00 AM daily)
scheduler.add_job(scheduled_scraping_job, CronTrigger(hour=0, minute=0))
scheduler.start()

@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown()
