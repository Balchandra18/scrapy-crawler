from apscheduler.schedulers.background import BackgroundScheduler
from ky_scraper import scrape_ky_case_documents
from pa_scraper import scrape_pa_documents
from ri_scraper import scrape_ri_documents

scheduler = BackgroundScheduler()

# Configure tasks
@scheduler.scheduled_job('cron', hour='0', minute='0')
def daily_ky_scraper():
    # Replace with your URLs
    urls = ["https://example.com/ky-case"]
    for url in urls:
        scrape_ky_case_documents(url)

@scheduler.scheduled_job('cron', hour='0', minute='0')
def daily_pa_scraper():
    urls = ["https://example.com/pa-docket"]
    for url in urls:
        scrape_pa_documents(url)

@scheduler.scheduled_job('cron', hour='0', minute='0')
def daily_ri_scraper():
    urls = ["https://example.com/ri-docket"]
    for url in urls:
        scrape_ri_documents(url)

scheduler.start()
