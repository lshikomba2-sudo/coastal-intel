import requests
from bs4 import BeautifulSoup
import sqlite3
import pandas as pd
from datetime import datetime
import time
import random

DB_PATH = "database/properties.db"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

BASE_URL = "https://www.property24.co.na"

COASTAL_AREAS = [
    {"name": "swakopmund", "slug": "swakopmund-c2263"},
    {"name": "walvis-bay",  "slug": "walvis-bay-c2264"},
    {"name": "henties-bay", "slug": "henties-bay-c2359"},
    {"name": "langstrand",  "slug": "langstrand-s15676"},
]

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            price REAL,
            location TEXT,
            bedrooms INTEGER,
            bathrooms INTEGER,
            size_m2 REAL,
            price_per_m2 REAL,
            listing_type TEXT,
            url TEXT,
            date_scraped TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("Database ready.")

def scrape_area(area, listing_type="to-rent"):
    type_slug = "property-to-rent-in" if listing_type == "to-rent" else "property-for-sale-in"
    url = f"{BASE_URL}/{type_slug}-{area['slug']}"
    print(f"Scraping {listing_type} in {area['name']}... URL: {url}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Could not reach {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    listings = []

    cards = soup.find_all("div", class_="p24_regularTile")

    if not cards:
        print(f"No listings found for {area['name']} - site structure may have changed.")
        return []

    for card in cards:
        try:
            title = card.find("span", class_="p24_title")
            title = title.text.strip() if title else "N/A"

            price_tag = card.find("span", class_="p24_price")
            price_text = price_tag.text.strip() if price_tag else "0"
            price = float("".join(filter(str.isdigit, price_text))) if price_text else 0

            location_tag = card.find("span", class_="p24_location")
            location = location_tag.text.strip() if location_tag else area['name']

            beds_tag = card.find("span", class_="p24_featureDetails", attrs={"title": "Bedrooms"})
            beds = int(beds_tag.text.strip()) if beds_tag else 0

            baths_tag = card.find("span", class_="p24_featureDetails", attrs={"title": "Bathrooms"})
            baths = float(baths_tag.text.strip()) if baths_tag else 0

            size_tag = card.find("span", class_="p24_featureDetails", attrs={"title": "Floor Size"})
            size_text = size_tag.text.strip() if size_tag else "0"
            size_text_clean = ''.join(c for c in size_text if c.isdigit() or c == '.')
            size = float(size_text_clean) if size_text_clean else 0

            price_per_m2 = round(price / size, 2) if size > 0 else 0

            link_tag = card.find("a", href=True)
            url_full = "https://www.property24.com" + link_tag["href"] if link_tag else ""

            listings.append({
                "title": title,
                "price": price,
                "location": location,
                "bedrooms": beds,
                "bathrooms": baths,
                "size_m2": size,
                "price_per_m2": price_per_m2,
                "listing_type": listing_type,
                "url": url_full,
                "date_scraped": datetime.now().strftime("%Y-%m-%d %H:%M")
            })

        except Exception as e:
            print(f"Skipped a card due to error: {e}")
            continue

    print(f"Found {len(listings)} listings in {area['name']}")
    return listings

def save_to_db(listings):
    if not listings:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for l in listings:
        c.execute("""
            INSERT INTO listings 
                (title, price, location, bedrooms, bathrooms, 
                 size_m2, price_per_m2, listing_type, url, date_scraped)
            SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM listings 
                WHERE url = ? AND date_scraped LIKE ?
            )
        """, (
            l["title"], l["price"], l["location"], l["bedrooms"],
            l["bathrooms"], l["size_m2"], l["price_per_m2"],
            l["listing_type"], l["url"], l["date_scraped"],
            l["url"], l["date_scraped"][:10] + "%"
        ))
    conn.commit()
    conn.close()
    print(f"Saved {len(listings)} listings to database.")

def run_scraper():
    init_db()
    all_listings = []

    for area in COASTAL_AREAS:
        for listing_type in ["to-rent", "for-sale"]:
            listings = scrape_area(area, listing_type)
            all_listings.extend(listings)
            time.sleep(random.uniform(2, 4))

    save_to_db(all_listings)

    if all_listings:
        df = pd.DataFrame(all_listings)
        print("\n--- SUMMARY ---")
        print(f"Total listings scraped: {len(df)}")
        print(f"Areas covered: {df['location'].nunique()}")
        print(f"Avg rental price: N${df[df['listing_type']=='to-rent']['price'].mean():,.0f}")
        print(f"Avg sale price: N${df[df['listing_type']=='for-sale']['price'].mean():,.0f}")
        print("---------------\n")

if __name__ == "__main__":
    run_scraper()