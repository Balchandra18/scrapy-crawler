from fastapi import FastAPI
from pydantic import BaseModel
from crawler.case_scraper import scrape_case_documents
from crawler.docket_scraper import scrape_docket_documents

app = FastAPI()

class ScrapeRequest(BaseModel):
    urls: list[str]

@app.post("/scrape/case")
def scrape_case_endpoint(request: ScrapeRequest):
    for url in request.urls:
        scrape_case_documents(url)
    return {"status": "success", "message": "Case scraping completed."}

@app.post("/scrape/docket")
def scrape_docket_endpoint(request: ScrapeRequest):
    for url in request.urls:
        scrape_docket_documents(url)
    return {"status": "success", "message": "Docket scraping completed."}
