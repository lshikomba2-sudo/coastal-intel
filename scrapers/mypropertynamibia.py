import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import random
from datetime import datetime

DB_PATH = "database/properties.db"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.myproperty.com.na"
}

SEARCHES = [
    {"area": "Swakopmund", "type": "for-sale",
     "url": "https://www.myproperty.com.na/en-na/for-sale/erongo/swakopmund"},
    {"area": "Swakopmund", "type": "to-rent",
     "url": "https://www.myproperty.com.na/en-na/to-rent/erongo/swakopmund"},
    {"area": "Walvis Bay", "type": "for-sale",
     "url": "https://www.myproperty.com.na/en-na/for-sale/erongo/walvis-bay"},
    {"area": "Walvis Bay", "type": "to-rent",
     "url": "https://www.myproperty.com.na/en-na/to-rent/erongo/walvis-bay"},
    {"area": "Langstrand", "type": "for-sale",
     "url": "https://www.myproperty.com.na/en-na/for-sale/erongo/langstrand"},
    {"area": "Windhoek", "type": "for-sale",
     "url": "https://www.myproperty.com.na/en-na/for-sale/khomas/windhoek"},
    {"area": "Windhoek", "type": "to-rent",
     "url": "https://www.myproperty.com.na/en-na/to-rent/khomas/windhoek"},
]

def init_db():
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
    conn.commit()
    conn.close()

def scrape(search):
    print(f"Scraping MyProperty: {search['area']} {search['type']}...")
    try:
        r = requests.get(search["url"], headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"  Failed: {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    listings = []

    cards = (
        soup.find_all("div", class_=lambda x: x and "listing" in str(x).lower()) or
        soup.find_all("article") or
        soup.find_all("div", class_=lambda x: x and "property" in str(x).lower()) or
        soup.find_all("li", class_=lambda x: x and "result" in str(x).lower())
    )

    print(f"  Found {len(cards)} cards on page")

    for card in cards[:25]:
        try:
            title_tag = card.find(["h2","h3","h4","h1"])
            title = title_tag.text.strip() if title_tag else ""
            if not title:
                continue

            price_text = ""
            for tag in card.find_all(
                string=lambda t: t and ("N$" in str(t) or 
                                        "NAD" in str(t) or 
                                        "price" in str(t).lower())):
                price_text = str(tag)
                break

            if not price_text:
                price_tag = card.find(
                    class_=lambda x: x and "price" in str(x).lower())
                price_text = price_tag.text.strip() if price_tag else "0"

            price = float("".join(
                c for c in price_text 
                if c.isdigit() or c == ".") or 0)

            bed_tag = card.find(
                string=lambda t: t and "bed" in str(t).lower())
            beds = 0
            if bed_tag:
                import re
                bed_match = re.search(r'(\d+)', str(bed_tag))
                beds = int(bed_match.group(1)) if bed_match else 0

            link = card.find("a", href=True)
            url = link["href"] if link else ""
            if url and not url.startswith("http"):
                url = "https://www.myproperty.com.na" + url

            if price > 0:
                listings.append({
                    "title": title[:200],
                    "price": price,
                    "location": search["area"],
                    "bedrooms": beds,
                    "bathrooms": 0,
                    "size_m2": 0,
                    "price_per_m2": 0,
                    "listing_type": search["type"],
                    "url": url,
                    "source": "myproperty.com.na",
                    "date_scraped": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
        except Exception as e:
            continue

    print(f"  Extracted {len(listings)} listings with prices")
    return listings

def save(listings):
    if not listings:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    saved = 0
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
        saved += c.rowcount
    conn.commit()
    conn.close()
    print(f"Saved {saved} new listings.")

def run():
    init_db()
    all_listings = []
    for s in SEARCHES:
        listings = scrape(s)
        all_listings.extend(listings)
        time.sleep(random.uniform(2, 5))
    save(all_listings)
    if all_listings:
        print(f"\nMyProperty total: {len(all_listings)} listings")
        from collections import Counter
        areas = Counter(l["location"] for l in all_listings)
        for area, count in areas.most_common():
            prices = [l["price"] for l in all_listings 
                      if l["location"] == area and l["price"] > 0]
            avg = sum(prices)/len(prices) if prices else 0
            print(f"  {area}: {count} listings | avg N${avg:,.0f}")
    return all_listings

if __name__ == "__main__":
    run()
