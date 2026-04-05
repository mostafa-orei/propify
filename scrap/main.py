import requests
import json
import time
import random
import csv
import os
from typing import List, Dict, Any
import re

# ========================= CONFIGURATION =========================
DELAY = 1.0                    # Base delay between requests
MAX_RETRIES = 2                # Increased slightly for reliability
MAX_PAGES_PER_BOROUGH = 42     # ← New: Maximum 42 pages per borough
SAVE_JSON_FINAL = True
OUTPUT_CSV = "rightmove_properties_all_boroughs.csv"
PAGE_SIZE = 24

# ========================= LOCATIONS =========================
# Replace with your actual 32 boroughs
LOCATIONS: dict[str, str] = {
    "Barking and Dagenham": "REGION^61400",      # London Borough of Barking and Dagenham
    "Barnet": "REGION^93929",                    # London Borough of Barnet
    "Bexley": "REGION^93932",                    # London Borough of Bexley
    "Brent": "REGION^93935",                     # London Borough of Brent
    "Bromley": "REGION^93938",                   # London Borough of Bromley
    "Camden": "REGION^93941",                    # London Borough of Camden
    "Croydon": "REGION^93944",                   # London Borough of Croydon
    "Ealing": "REGION^93947",                    # London Borough of Ealing
    "Enfield": "REGION^93950",                   # London Borough of Enfield
    "Greenwich": "REGION^61226",                 # Royal Borough of Greenwich
    "Hackney": "REGION^93953",                   # London Borough of Hackney
    "Hammersmith and Fulham": "REGION^61407",    # London Borough of Hammersmith and Fulham
    "Haringey": "REGION^61227",                  # London Borough of Haringey
    "Harrow": "REGION^93956",                    # London Borough of Harrow
    "Havering": "REGION^61228",                  # London Borough of Havering
    "Hillingdon": "REGION^93959",                # London Borough of Hillingdon
    "Hounslow": "REGION^93962",                  # London Borough of Hounslow
    "Islington": "REGION^93965",                 # London Borough of Islington
    "Kensington and Chelsea": "REGION^61229",    # Royal Borough of Kensington and Chelsea
    "Kingston upon Thames": "REGION^93968",      # Royal Borough of Kingston upon Thames
    "Lambeth": "REGION^93971",                   # London Borough of Lambeth
    "Lewisham": "REGION^61413",                  # London Borough of Lewisham
    "Merton": "REGION^61414",                    # London Borough of Merton
    "Newham": "REGION^61231",                    # London Borough of Newham
    "Redbridge": "REGION^61537",                 # London Borough of Redbridge
    "Richmond upon Thames": "REGION^61415",      # London Borough of Richmond upon Thames
    "Southwark": "REGION^61518",                 # London Borough of Southwark
    "Sutton": "REGION^93974",                    # London Borough of Sutton
    "Tower Hamlets": "REGION^61417",             # London Borough of Tower Hamlets
    "Waltham Forest": "REGION^61232",            # London Borough of Waltham Forest
    "Wandsworth": "REGION^93977",                # London Borough of Wandsworth
    "Westminster": "REGION^87539"                # City of Westminster
}

CHANNEL = "BUY"
SORT_TYPE = 6
TRANSACTION_TYPE = "BUY"

# ========================= HEADERS =========================
COOKIE_STRING = """permuserid=260328SGKG24S36EHY35M6PV2WZR2GVT; TS01ec61d1=012f990cd31d04fcd02bcbd3e771257a2911d340a664d6200e864497d3c886ad2a7792d9345b8a60b53dd973116725c4b1c4f1e474; ..."""  # ← Put full cookies here

headers = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "permuserid": "260328SGKG24S36EHY35M6PV2WZR2GVT",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "Cookie": COOKIE_STRING
}

# ========================= HELPERS =========================
def clean_text(text: str) -> str:
    """
    Clean text fields (summary and displayAddress) for safe CSV saving.
    - Removes extra whitespace and newlines
    - Replaces commas with semicolons (to prevent CSV column breaking)
    - Strips leading/trailing spaces
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Replace newlines and multiple spaces with single space
    cleaned = re.sub(r'\s+', ' ', text)
    
    # Replace commas with semicolon to avoid breaking CSV columns
    cleaned = cleaned.replace(',', ';')
    
    # Remove any remaining problematic characters (optional but safe)
    # cleaned = re.sub(r'["\']', '', cleaned)  # uncomment if you want to remove quotes too
    
    return cleaned.strip()

def parse_display_size(size_str: str) -> int | None:
    if not size_str or not isinstance(size_str, str):
        return None
    cleaned = size_str.replace(" sq. ft.", "").replace("sq ft", "").replace(",", "").strip()
    try:
        return int(float(cleaned))
    except ValueError:
        return None


def append_to_csv(properties: List[Dict], csv_file: str):
    if not properties:
        return

    keys = ["id", "borough", "bedrooms", "bathrooms", "summary", "displayAddress",
            "latitude", "longitude", "updateDate", "price_amount", "displaySize_sqft", "property_sub_type"]

    file_exists = os.path.isfile(csv_file)

    with open(csv_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        if not file_exists:
            writer.writeheader()
        writer.writerows(properties)

    print(f"   💾 Appended {len(properties)} properties")


# ========================= MAIN SCRAPER =========================
def scrape_rightmove():
    session = requests.Session()
    session.headers.update(headers)

    total_properties = 0
    print(f"🚀 Starting Rightmove scraper for {len(LOCATIONS)} boroughs (max {MAX_PAGES_PER_BOROUGH} pages each)\n")

    for borough_name, location_id in LOCATIONS.items():
        print(f"\n🏠 Starting borough: {borough_name} (ID: {location_id})")
        
        index = 0
        page = 0
        borough_count = 0
        consecutive_errors = 0

        while page < MAX_PAGES_PER_BOROUGH:
            params = {
                "locationIdentifier": location_id,
                "channel": CHANNEL,
                "index": str(index),
                "sortType": str(SORT_TYPE),
                "transactionType": TRANSACTION_TYPE
            }

            for attempt in range(MAX_RETRIES):
                try:
                    print(f"   📄 Page {page + 1}/{MAX_PAGES_PER_BOROUGH} (index={index})...")
                    
                    resp = session.get(
                        "https://www.rightmove.co.uk/api/property-search/listing/search",
                        params=params,
                        timeout=15
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    properties_raw = data.get("properties", [])

                    if not properties_raw:
                        print(f"   ✅ No more properties found in {borough_name}")
                        break  # Exit borough loop

                    # Extract properties
                    extracted_batch = []
                    for prop in properties_raw:
                        extracted = {
                            "id": prop.get("id"),
                            "borough": borough_name,
                            "bedrooms": prop.get("bedrooms"),
                            "bathrooms": prop.get("bathrooms"),
                            "summary": clean_text(prop.get("summary")),
                            "displayAddress": clean_text(prop.get("displayAddress")),
                            "latitude": prop.get("location", {}).get("latitude"),
                            "longitude": prop.get("location", {}).get("longitude"),
                            "updateDate": prop.get("updateDate"),
                            "price_amount": prop.get("price", {}).get("amount"),
                            "displaySize_sqft": parse_display_size(prop.get("displaySize")),
                            "property_sub_type": prop.get("propertySubType"),
                        }
                        extracted_batch.append(extracted)

                    # Save to CSV
                    append_to_csv(extracted_batch, OUTPUT_CSV)

                    borough_count += len(extracted_batch)
                    total_properties += len(extracted_batch)

                    print(f"   ✅ Saved {len(extracted_batch)} properties | "
                          f"Borough: {borough_count} | Total: {total_properties}")

                    # Check if last page
                    if len(properties_raw) < PAGE_SIZE:
                        print(f"   ✅ Reached the last page for {borough_name}")
                        index += PAGE_SIZE
                        page += 1
                        break

                    # Prepare next page
                    index += PAGE_SIZE
                    page += 1
                    consecutive_errors = 0

                    # Polite delay
                    sleep_time = DELAY + random.uniform(0.4, 1.3)
                    print(f"   ⏳ Waiting {sleep_time:.2f}s...\n")
                    time.sleep(sleep_time)
                    break  # Success - go to next page

                except requests.exceptions.RequestException as e:
                    print(f"   ❌ Request error (attempt {attempt+1}/{MAX_RETRIES}): {e}")
                    consecutive_errors += 1
                    
                    if attempt == MAX_RETRIES - 1:
                        print(f"   ⚠️  Max retries reached for page {page + 1} in {borough_name}")
                        break
                    time.sleep(6 * (attempt + 1))  # backoff

                except Exception as e:
                    print(f"   ❌ Unexpected error in {borough_name}: {e}")
                    consecutive_errors += 1
                    if consecutive_errors >= 3:
                        print(f"   🛑 Too many errors in {borough_name}. Moving to next borough.")
                        break
                    time.sleep(8)

            else:
                # Inner for loop completed without break → max retries failed
                print(f"   🛑 Failed to fetch page after {MAX_RETRIES} attempts. Skipping to next borough.")
                break

            if consecutive_errors >= 3:
                break

        print(f"   📊 Finished {borough_name}: {borough_count} properties scraped "
              f"({page + 1} pages attempted)\n")

    # Final summary
    print("=" * 60)
    print(f"🎉 SCRAPING COMPLETED FOR ALL BOROUGHS!")
    print(f"   Total properties saved: {total_properties}")
    print(f"   Output file: {OUTPUT_CSV}")
    print("=" * 60)

    if SAVE_JSON_FINAL and total_properties > 0:
        print("💾 Saving full JSON (this may take a moment)...")
        # Note: all_properties list removed to save memory with 32 boroughs × 42 pages

    return total_properties


if __name__ == "__main__":
    scrape_rightmove()