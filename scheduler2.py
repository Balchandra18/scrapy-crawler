from apscheduler.schedulers.background import BackgroundScheduler
from crawler.case_scraper import scrape_case_documents
from crawler.docket_scraper import scrape_docket_documents

def scheduled_task():
    # Add your URLs here
    case_urls = ["<CASE_URL_1>", "<CASE_URL_2>"]
    docket_urls = ["<DOCKET_URL_1>", "<DOCKET_URL_2>"]

    for url in case_urls:
        scrape_case_documents(url)
    
    for url in docket_urls:
        scrape_docket_documents(url)

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_task, "interval", days=1)
    scheduler.start()
    
    try:
        # Keep the script running
        while True:
            pass
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
