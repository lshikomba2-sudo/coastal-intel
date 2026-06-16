import requests
from bs4 import BeautifulSoup
import sqlite3
import time
from datetime import datetime

DB_PATH = "database/properties.db"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
}

URLS = [
    {
        "name": "Aucor Namibia - All",
        "url": "https://aucornamibia.com/"
    },
    {
        "name": "Aucor - Namibia Property",
        "url": "https://aucor.com/auctions/region/national/region/namibia"
    },
]

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS auction_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            price REAL,
            reserve_price REAL,
            location TEXT,
            auction_date TEXT,
            property_type TEXT,
            url TEXT,
            source TEXT,
            is_repo INTEGER DEFAULT 0,
            date_scraped TEXT
        )
    """)
    conn.commit()
    conn.close()

def scrape_aucor(source):
    print(f"Scraping: {source['name']}...")
    try:
        r = requests.get(source["url"], headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"  Failed: {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    listings = []
    import re

    cards = (
        soup.find_all("div", class_=lambda x: x and "auction" in str(x).lower()) or
        soup.find_all("div", class_=lambda x: x and "lot" in str(x).lower()) or
        soup.find_all("article") or
        soup.find_all("div", class_=lambda x: x and "item" in str(x).lower())
    )

    print(f"  Found {len(cards)} cards")

    for card in cards[:30]:
        try:
            title_tag = card.find(["h2","h3","h4","h1","strong"])
            title = title_tag.text.strip() if title_tag else ""
            if not title or len(title) < 5:
                continue

            desc_tag = card.find("p")
            description = desc_tag.text.strip()[:300] if desc_tag else ""

            price_text = card.get_text()
            price_match = re.search(
                r'R\s*([\d\s,]+(?:\.\d+)?)', price_text)
            price = 0
            if price_match:
                price = float(
                    price_match.group(1).replace(" ","").replace(",",""))

            date_tag = card.find(
                string=lambda t: t and any(
                    m in str(t) for m in 
                    ["Jan","Feb","Mar","Apr","May","Jun",
                     "Jul","Aug","Sep","Oct","Nov","Dec","2026","2025"]))
            auction_date = str(date_tag).strip() if date_tag else ""

            link = card.find("a", href=True)
            url = link["href"] if link else source["url"]
            if url and not url.startswith("http"):
                url = "https://aucor.com" + url

            namibia_keywords = [
                "namibia","windhoek","swakopmund","walvis",
                "langstrand","henties","rehoboth","oshakati",
                "rundu","otjiwarongo"
            ]
            text_lower = (title + description).lower()
            is_namibia = any(k in text_lower for k in namibia_keywords)

            location = "Namibia"
            for kw in namibia_keywords[1:]:
                if kw in text_lower:
                    location = kw.title()
                    break

            is_repo = int(any(k in text_lower for k in
                ["repossessed","repo","bank mandate",
                 "executor","liquidation","insolvent"]))

            prop_keywords = [
                "house","flat","apartment","complex","farm",
                "plot","erf","commercial","industrial"
            ]
            property_type = "Property"
            for kw in prop_keywords:
                if kw in text_lower:
                    property_type = kw.title()
                    break

            listings.append({
                "title": title[:200],
                "description": description,
                "price": price,
                "reserve_price": 0,
                "location": location,
                "auction_date": auction_date,
                "property_type": property_type,
                "url": url,
                "source": source["name"],
                "is_repo": is_repo,
                "date_scraped": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
        except Exception as e:
            continue

    print(f"  Extracted {len(listings)} auction items")
    return listings

def save(listings):
    if not listings:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    saved = 0
    for l in listings:
        c.execute("""
            INSERT INTO auction_listings
            (title, description, price, reserve_price, location,
             auction_date, property_type, url, source, is_repo, date_scraped)
            SELECT ?,?,?,?,?,?,?,?,?,?,?
            WHERE NOT EXISTS (
                SELECT 1 FROM auction_listings 
                WHERE url=? AND title=?
            )
        """, (l["title"], l["description"], l["price"],
              l["reserve_price"], l["location"], l["auction_date"],
              l["property_type"], l["url"], l["source"],
              l["is_repo"], l["date_scraped"],
              l["url"], l["title"]))
        saved += c.rowcount
    conn.commit()
    conn.close()
    print(f"Saved {saved} new auction listings.")

def print_summary():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    print("\n--- AUCOR NAMIBIA SUMMARY ---")
    c.execute("""
        SELECT location, COUNT(*), SUM(is_repo),
        property_type
        FROM auction_listings
        GROUP BY location, property_type
        ORDER BY COUNT(*) DESC
    """)
    for r in c.fetchall():
        print(f"  {r[0]} | {r[1]} lots | "
              f"{r[2]} repo | {r[3]}")
    conn.close()

def run():
    init_db()
    all_listings = []
    for source in URLS:
        listings = scrape_aucor(source)
        all_listings.extend(listings)
        time.sleep(3)
    save(all_listings)
    print_summary()
    return all_listings

if __name__ == "__main__":
    run()
