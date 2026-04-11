import requests
import sqlite3
import json
from datetime import datetime

BASE_URL = "https://nhis.org.na/api/public"

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Referer": "https://nhis.org.na/land-use/explore"
}

DB_PATH = "database/properties.db"

ALL_REGIONS = [
    {"name": "Erongo",       "regionId": "62765382-e0ef-4fdd-88a5-2e177bf5f939"},
    {"name": "Hardap",       "regionId": "1af4601b-d3b4-429e-951e-06047b9c1441"},
    {"name": "Kavango East", "regionId": "8acfaaaa-4b38-4044-9e32-a62eb50bc849"},
    {"name": "Kavango West", "regionId": "61dbe0ad-d83b-430b-876e-cc8d5ab85ebc"},
    {"name": "//Kharas",     "regionId": "dc208e01-e6de-424a-b055-a8542fb822ae"},
    {"name": "Khomas",       "regionId": "6925ad29-8434-4f61-b173-a4e56b63581b"},
    {"name": "Kunene",       "regionId": "cb310dad-9605-4663-a063-528899503c6b"},
    {"name": "Ohangwena",    "regionId": "e890b6f5-8e74-46f6-b739-c52df0fd2e8b"},
    {"name": "Omaheke",      "regionId": "7346fd93-178a-470e-8b9e-e3e244da5e09"},
    {"name": "Omusati",      "regionId": "c32fab5a-03d5-424d-b9d1-e1b3915207f4"},
    {"name": "Oshana",       "regionId": "51d7cb25-9cb1-4693-a7d3-94800540cfb8"},
    {"name": "Oshikoto",     "regionId": "44164dfb-24aa-4fab-adb3-c7e50fea970a"},
    {"name": "Otjozondjupa", "regionId": "74967832-4a1f-431c-a65e-ebbab539627c"},
    {"name": "Zambezi",      "regionId": "8f373894-1b09-4f72-9d51-8acd2af335ba"},
]

ERONGO_LOCAL_AUTHORITIES = [
    {"name": "Swakopmund",    "id": "c386046a-9393-4037-bbeb-90f240368e9e"},
    {"name": "Walvis Bay",    "id": "bc6f4c05-7d9c-42a1-b889-be61c160d880"},
    {"name": "Hentiesbay",   "id": "b78636ad-01c7-4358-8994-7c21d506bb0e"},
    {"name": "Usakos",        "id": "63400075-3b8d-4fc8-9d30-ab777ba2a0ca"},
    {"name": "Karibib",       "id": "fd64a769-326b-420e-be8d-be6566f72ee8"},
    {"name": "Arandis",       "id": "5fc9cb1e-e1b0-4eaf-895d-7701ae54bc3b"},
    {"name": "Omaruru",       "id": "a72ba5ad-9e8e-45bd-a520-08abb7994f9e"},
]

def get_local_authorities(region_id):
    url = f"{BASE_URL}/local_authority_areas?regionId={region_id}"
    r = requests.get(url, headers=HEADERS, timeout=10)
    if r.status_code == 200:
        return r.json()
    return []

def explore_endpoints(local_authority_id, name):
    print(f"\nExploring endpoints for {name}...")
    endpoints = [
        f"/land-use?localAuthorityAreaId={local_authority_id}",
        f"/land-use/parcels?localAuthorityAreaId={local_authority_id}",
        f"/housing-stock?localAuthorityAreaId={local_authority_id}",
        f"/housing-stock/units?localAuthorityAreaId={local_authority_id}",
        f"/informal-settlements?localAuthorityAreaId={local_authority_id}",
        f"/informal-settlements/list?localAuthorityAreaId={local_authority_id}",
        f"/statistics?localAuthorityAreaId={local_authority_id}",
        f"/summary?localAuthorityAreaId={local_authority_id}",
    ]
    for ep in endpoints:
        url = BASE_URL + ep
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            print(f"  {r.status_code} - {ep.split('?')[0]}")
            if r.status_code == 200:
                data = r.json()
                if data and data != {"API": "Namibia Housing Information System API", 
                                     "Copyright": "@Namibia Housing Information System 2023",
                                     "Version": "1.0.0", "mode": "public-only"}:
                    print(f"    >>> DATA FOUND: {str(data)[:200]}")
        except Exception as e:
            print(f"  ERROR - {ep}: {e}")

if __name__ == "__main__":
    print("Sampling all live endpoints for Swakopmund...\n")
    swakop_id = "c386046a-9393-4037-bbeb-90f240368e9e"
    
    endpoints = [
        f"/land-use?localAuthorityAreaId={swakop_id}",
        f"/land-use/parcels?localAuthorityAreaId={swakop_id}",
        f"/housing-stock?localAuthorityAreaId={swakop_id}",
        f"/housing-stock/units?localAuthorityAreaId={swakop_id}",
        f"/informal-settlements?localAuthorityAreaId={swakop_id}",
        f"/informal-settlements/list?localAuthorityAreaId={swakop_id}",
        f"/statistics?localAuthorityAreaId={swakop_id}",
        f"/summary?localAuthorityAreaId={swakop_id}",
    ]
    
    for ep in endpoints:
        url = BASE_URL + ep
        r = requests.get(url, headers=HEADERS, timeout=10)
        data = r.json()
        print(f"{'='*60}")
        print(f"ENDPOINT: {ep.split('?')[0]}")
        print(f"TYPE: {type(data).__name__}")
        if isinstance(data, list):
            print(f"RECORDS: {len(data)}")
            if len(data) > 0:
                print(f"FIRST RECORD KEYS: {list(data[0].keys()) if isinstance(data[0], dict) else data[0]}")
                print(f"SAMPLE: {json.dumps(data[0], indent=2)[:400]}")
        elif isinstance(data, dict):
            print(f"KEYS: {list(data.keys())}")
            print(f"SAMPLE: {json.dumps(data, indent=2)[:400]}")
        print()
