import sqlite3
from datetime import datetime
import re

DB_PATH = "database/properties.db"

def parse_listing(raw_text, area="Unknown"):
    price_match = re.search(
        r'N\$\s*([\d,]+(?:\.\d+)?(?:\s*[mk](?:illion)?)?)', 
        raw_text, re.IGNORECASE)
    
    price = 0
    if price_match:
        price_str = price_match.group(1).replace(",","").strip()
        if "m" in price_str.lower():
            price = float(re.sub(r'[^\d.]','',price_str)) * 1000000
        elif "k" in price_str.lower():
            price = float(re.sub(r'[^\d.]','',price_str)) * 1000
        else:
            price = float(re.sub(r'[^\d.]','',price_str) or 0)

    bed_match = re.search(r'(\d+)\s*(?:bed|bedroom|br)', 
                           raw_text, re.IGNORECASE)
    beds = int(bed_match.group(1)) if bed_match else 0

    listing_type = "to-rent"
    if any(w in raw_text.lower() for w in 
           ["for sale","selling","sale price","asking"]):
        listing_type = "for-sale"

    area_match = re.search(
        r'\b(Swakopmund|Walvis Bay|Langstrand|Henties Bay|Windhoek|'
        r'Rundu|Oshakati|Rehoboth|Otjiwarongo)\b',
        raw_text, re.IGNORECASE)
    if area_match:
        area = area_match.group(0)

    distress_keywords = [
        "urgent","repossessed","bank mandate","price reduced",
        "negotiable","nÃ©gociable","relocating","emigrating"
    ]
    multi_keywords = [
        "block of flats","multiple units","complex",
        "townhouse park","back rooms","units"
    ]
    
    is_distressed = any(k in raw_text.lower() for k in distress_keywords)
    is_multi = any(k in raw_text.lower() for k in multi_keywords)

    return {
        "title": raw_text[:150].replace("\n"," "),
        "price": price,
        "location": area,
        "bedrooms": beds,
        "bathrooms": 0,
        "size_m2": 0,
        "price_per_m2": 0,
        "listing_type": listing_type,
        "url": "facebook-marketplace",
        "source": "facebook-manual",
        "is_distressed": is_distressed,
        "is_multi_unit": is_multi,
        "raw_text": raw_text,
        "date_scraped": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

def save_listing(listing):
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
    c.execute("""
        CREATE TABLE IF NOT EXISTS facebook_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT, price REAL, location TEXT,
            bedrooms INTEGER, listing_type TEXT,
            is_distressed INTEGER, is_multi_unit INTEGER,
            raw_text TEXT, date_scraped TEXT
        )
    """)
    c.execute("""
        INSERT INTO facebook_listings
        (title, price, location, bedrooms, listing_type,
         is_distressed, is_multi_unit, raw_text, date_scraped)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (listing["title"], listing["price"], listing["location"],
          listing["bedrooms"], listing["listing_type"],
          int(listing["is_distressed"]), int(listing["is_multi_unit"]),
          listing["raw_text"], listing["date_scraped"]))
    
    if listing["price"] > 0:
        c.execute("""
            INSERT INTO listings_expanded
            (title, price, location, bedrooms, bathrooms,
             size_m2, price_per_m2, listing_type, url, source, date_scraped)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (listing["title"], listing["price"], listing["location"],
              listing["bedrooms"], 0, 0, 0, listing["listing_type"],
              listing["url"], listing["source"], listing["date_scraped"]))
    
    conn.commit()
    conn.close()
    print(f"Saved: {listing['location']} | N${listing['price']:,.0f} | "
          f"{'DISTRESSED' if listing['is_distressed'] else ''} "
          f"{'MULTI-UNIT' if listing['is_multi_unit'] else ''}")

def add_facebook_listing():
    print("FACEBOOK LISTING PARSER")
    print("Paste listing text below. Press Enter twice when done:")
    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    
    raw_text = "\n".join(lines[:-1])
    if not raw_text.strip():
        print("No text entered.")
        return
    
    listing = parse_listing(raw_text)
    print(f"\nParsed:")
    print(f"  Location: {listing['location']}")
    print(f"  Price: N${listing['price']:,.0f}")
    print(f"  Beds: {listing['bedrooms']}")
    print(f"  Type: {listing['listing_type']}")
    print(f"  Distressed: {listing['is_distressed']}")
    print(f"  Multi-unit: {listing['is_multi_unit']}")
    
    confirm = input("\nSave this listing? (y/n): ")
    if confirm.lower() == "y":
        save_listing(listing)

def summary():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("""
            SELECT location, COUNT(*), 
            SUM(is_distressed), SUM(is_multi_unit)
            FROM facebook_listings GROUP BY location
        """)
        rows = c.fetchall()
        print("\nFACEBOOK LISTINGS SUMMARY:")
        for r in rows:
            print(f"  {r[0]}: {r[1]} listings | "
                  f"{r[2]} distressed | {r[3]} multi-unit")
    except:
        print("No Facebook listings yet.")
    conn.close()

if __name__ == "__main__":
    print("1. Add new listing")
    print("2. Show summary")
    choice = input("Choice: ")
    if choice == "1":
        add_facebook_listing()
    else:
        summary()
