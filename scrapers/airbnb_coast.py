import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import random
from datetime import datetime

DB_PATH = "database/properties.db"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

COASTAL_SEARCHES = [
    {
        "area": "Swakopmund",
        "url": "https://www.airbnb.com/s/Swakopmund--Namibia/homes?adults=2&price_min=0"
    },
    {
        "area": "Walvis Bay",
        "url": "https://www.airbnb.com/s/Walvis-Bay--Namibia/homes?adults=2&price_min=0"
    },
    {
        "area": "Langstrand",
        "url": "https://www.airbnb.com/s/Langstrand--Namibia/homes?adults=2&price_min=0"
    },
    {
        "area": "Henties Bay",
        "url": "https://www.airbnb.com/s/Henties-Bay--Namibia/homes?adults=2&price_min=0"
    },
]

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS airbnb_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area TEXT,
            title TEXT,
            price_per_night REAL,
            currency TEXT,
            rating REAL,
            reviews INTEGER,
            property_type TEXT,
            url TEXT,
            date_scraped TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("Airbnb table ready.")

def scrape_area(area, url):
    print(f"Scraping Airbnb: {area}...")
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Could not reach Airbnb for {area}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    listings = []

    cards = soup.find_all("div", attrs={"data-testid": "card-container"})
    
    if not cards:
        cards = soup.find_all("div", class_=lambda x: x and "listing" in x.lower())

    if not cards:
        import json, re
        scripts = soup.find_all("script", type="application/json")
        for script in scripts:
            try:
                data = json.loads(script.string)
                text = json.dumps(data)
                prices = re.findall(r'"price":\s*\{[^}]*"amount":\s*(\d+)', text)
                if prices:
                    print(f"  Found {len(prices)} price points in page data for {area}")
                    for p in prices[:20]:
                        listings.append({
                            "area": area,
                            "title": f"Airbnb {area}",
                            "price_per_night": float(p),
                            "currency": "NAD",
                            "rating": 0,
                            "reviews": 0,
                            "property_type": "Unknown",
                            "url": url,
                            "date_scraped": datetime.now().strftime("%Y-%m-%d")
                        })
                    break
            except:
                continue

    print(f"  Found {len(listings)} listings for {area}")
    return listings

def save_to_db(listings):
    if not listings:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for l in listings:
        c.execute("""
            INSERT INTO airbnb_listings 
            (area, title, price_per_night, currency, rating, reviews, 
             property_type, url, date_scraped)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (l["area"], l["title"], l["price_per_night"], l["currency"],
              l["rating"], l["reviews"], l["property_type"], l["url"], l["date_scraped"]))
    conn.commit()
    conn.close()
    print(f"Saved {len(listings)} Airbnb listings.")

def print_summary():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT area, COUNT(*) as listings, 
        ROUND(AVG(price_per_night),0) as avg_price,
        ROUND(MIN(price_per_night),0) as min_price,
        ROUND(MAX(price_per_night),0) as max_price
        FROM airbnb_listings
        WHERE price_per_night > 0
        GROUP BY area
    """)
    rows = c.fetchall()
    if rows:
        print("\n--- AIRBNB COASTAL SUMMARY ---")
        for r in rows:
            print(f"{r[0]}: {r[1]} listings | avg N${r[2]}/night | range N${r[3]}-N${r[4]}")
    else:
        print("\nNo Airbnb price data captured yet.")
    conn.close()

def run():
    init_db()
    all_listings = []
    for search in COASTAL_SEARCHES:
        listings = scrape_area(search["area"], search["url"])
        all_listings.extend(listings)
        time.sleep(random.uniform(3, 6))
    save_to_db(all_listings)
    print_summary()

if __name__ == "__main__":
    run()
