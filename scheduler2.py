# scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import schedule
import time

def run_scrapers():
    # Example: Replace with calls to API endpoints
    import requests
    urls_ky = ["http://127.0.0.1:8000/kyscrape", {"urls": ["<KY URLs>"]}]
    requests.post(*urls_ky)

    urls_pa = ["http://127.0.0.1:8000/pascrape", {"urls": ["<PA URLs>"]}]
    requests.post(*urls_pa)

    urls_ri = ["http://127.0.0.1:8000/riscrape", {"urls": ["<RI URLs>"]}]
    requests.post(*urls_ri)

scheduler = BackgroundScheduler()
scheduler.add_job(run_scrapers, 'interval', hours=24)
scheduler.start()

app = FastAPI()

@app.get("/health")
def health_check():
    return JSONResponse(content={"status": "running"})

while True:
    time.sleep(1)
