import schedule
import time
import subprocess
import sys
from datetime import datetime
from scrapers.mypropertynamibia import run as run_mypropertynam
from scrapers.namibian_classifieds import run as run_namibian

def run_scraper():
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Running Exokino scraper...")
    result = subprocess.run(
        [sys.executable, "scrapers/property24.py"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.stderr:
        print(f"Errors: {result.stderr}")
    run_mypropertynam()
    run_namibian()
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Scrape complete.")

schedule.every().sunday.at("06:00").do(run_scraper)
schedule.every().day.at("06:00").do(run_scraper)

print("Exokino scheduler running...")
print("Scraper will run daily at 06:00")
print("Press Ctrl+C to stop\n")

run_scraper()

while True:
    schedule.run_pending()
    time.sleep(60)
