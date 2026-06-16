import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import random
from datetime import datetime

DB_PATH = "database/properties.db"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

SEARCHES = [
    {"area": "Swakopmund", 
     "url": "https://www.namibian.com.na/classifieds/property/for-sale/swakopmund"},
    {"area": "Walvis Bay",
     "url": "https://www.namibian.com.na/classifieds/property/for-sale/walvis-bay"},
    {"area": "Windhoek",
     "url": "https://www.namibian.com.na/classifieds/property/for-sale/windhoek"},
    {"area": "Swakopmund",
     "url": "https://www.namibian.com.na/classifieds/property/to-rent/swakopmund"},
    {"area": "Windhoek",
     "url": "https://www.namibian.com.na/classifieds/property/to-rent/windhoek"},
]

def scrape(search):
    print(f"Scraping Namibian Classifieds: {search['area']}...")
    try:
        r = requests.get(search["url"], headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"  Failed: {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    listings = []
    
    cards = (soup.find_all("div", class_="classified-item") or
             soup.find_all("div", class_="ad-item") or
             soup.find_all("div", class_=lambda x: x and "classif" in str(x).lower()) or
             soup.find_all("li", class_=lambda x: x and "item" in str(x).lower()))

    for card in cards[:20]:
        try:
            title = card.find(["h2","h3","h4","a"])
            title = title.text.strip() if title else "Unknown"
            
            price_tag = card.find(
                string=lambda t: t and "N$" in str(t))
            if not price_tag:
                price_tag = card.find(
                    class_=lambda x: x and "price" in str(x).lower())
            
            price_text = price_tag.text.strip() if hasattr(price_tag, "text") else str(price_tag or "0")
            price = float("".join(c for c in price_text if c.isdigit() or c == ".") or 0)
            
            link = card.find("a", href=True)
            url = link["href"] if link else ""
            if url and not url.startswith("http"):
                url = "https://www.namibian.com.na" + url

            if price > 0 and title != "Unknown":
                listings.append({
                    "title": title[:200],
                    "price": price,
                    "location": search["area"],
                    "bedrooms": 0,
                    "bathrooms": 0,
                    "size_m2": 0,
                    "price_per_m2": 0,
                    "listing_type": "for-sale" if "for-sale" in search["url"] else "to-rent",
                    "url": url,
                    "source": "namibian-classifieds",
                    "date_scraped": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
        except:
            continue

    print(f"  Found {len(listings)} listings")
    return listings

def save(listings):
    if not listings:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS listings_expanded (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT, price REAL, location TEXT,
            bedrooms INTEGER, bathrooms INTEGER,
            size_m2 REAL, price_per_m2 REAL,
            listing_type TEXT, url TEXT,
            source TEXT, date_scraped TEXT
        )
    """)
    for l in listings:
        c.execute("""
            INSERT INTO listings_expanded
            (title, price, location, bedrooms, bathrooms,
             size_m2, price_per_m2, listing_type, url, source, date_scraped)
            SELECT ?,?,?,?,?,?,?,?,?,?,?
            WHERE NOT EXISTS (
                SELECT 1 FROM listings_expanded
                WHERE url=? AND date_scraped LIKE ?
            )
        """, (l["title"], l["price"], l["location"], l["bedrooms"],
              l["bathrooms"], l["size_m2"], l["price_per_m2"],
              l["listing_type"], l["url"], l["source"], l["date_scraped"],
              l["url"], l["date_scraped"][:10]+"%"))
    conn.commit()
    conn.close()
    print(f"Saved {len(listings)} listings.")

def run():
    all_listings = []
    for s in SEARCHES:
        listings = scrape(s)
        all_listings.extend(listings)
        time.sleep(random.uniform(2, 4))
    save(all_listings)
    return all_listings

if __name__ == "__main__":
    results = run()
    print(f"\nTotal: {len(results)} from Namibian Classifieds")
