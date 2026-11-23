"""
Deterministic Year-Stratified Harvester for OpenAlex Works API
Target: 5,000 unique AI/ML research publications (2016-2025, 500 per year).
Filter: Subfield 1702 (Artificial Intelligence), non-retracted, non-paratext.
"""

import os
import json
import time
import urllib.request
import urllib.parse
from typing import Dict, Any, List

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
os.makedirs(DATA_RAW_DIR, exist_ok=True)

USER_AGENT = "ResearchKG-AcademicBot/1.0 (mailto:academic.researcher@university.edu; Project Title 34 Research)"
BASE_URL = "https://api.openalex.org/works"

YEARS = list(range(2016, 2026)) # 2016 through 2025 inclusive
TARGET_PER_YEAR = 500
PAGE_SIZE = 100

def harvest_stratified_openalex_corpus() -> List[Dict[str, Any]]:
    print("=" * 80)
    print("COLLECTING YEAR-STRATIFIED OPENALEX AI/ML CORPUS (2016-2025)")
    print(f"Target: {TARGET_PER_YEAR} works/year x {len(YEARS)} years = {TARGET_PER_YEAR * len(YEARS)} works")
    print(f"Primary Filter: primary_topic.subfield.id:1702 (Artificial Intelligence)")
    print("=" * 80)

    all_harvested_works = []
    harvest_log = []

    for year in YEARS:
        year_works = []
        page = 1
        pages_needed = TARGET_PER_YEAR // PAGE_SIZE
        
        filter_str = (
            f"primary_topic.subfield.id:1702,"
            f"publication_year:{year},"
            f"type:article|conference-paper|book-chapter,"
            f"is_retracted:false,"
            f"is_paratext:false"
        )
        
        print(f"\n[Harvest Year {year}] Target: {TARGET_PER_YEAR} works (5 pages of 100)...")

        while len(year_works) < TARGET_PER_YEAR and page <= pages_needed:
            params = {
                "filter": filter_str,
                "sort": "cited_by_count:desc",
                "per-page": PAGE_SIZE,
                "page": page
            }
            url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
            
            try:
                req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=25) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
                    results = payload.get("results", [])
                    if not results:
                        print(f"  Page {page}: No further records returned.")
                        break
                    year_works.extend(results)
                    print(f"  Year {year} | Page {page}/{pages_needed}: Fetched {len(results)} works (Year Total: {len(year_works)})")
                
                page += 1
                time.sleep(0.12) # Polite API rate limiting
            except Exception as e:
                print(f"  Error fetching year {year}, page {page}: {e}")
                time.sleep(1.0)
                # Retry once
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                    with urllib.request.urlopen(req, timeout=30) as resp:
                        payload = json.loads(resp.read().decode("utf-8"))
                        results = payload.get("results", [])
                        year_works.extend(results)
                    page += 1
                except Exception as retry_err:
                    print(f"  Retry failed for year {year}, page {page}: {retry_err}")
                    break

        all_harvested_works.extend(year_works)
        harvest_log.append({
            "year": year,
            "target": TARGET_PER_YEAR,
            "collected": len(year_works),
            "filter": filter_str
        })

    # Save raw snapshot
    output_raw_file = os.path.join(DATA_RAW_DIR, "openalex_raw_5000.json")
    print(f"\n[Raw Storage] Saving {len(all_harvested_works)} raw records to: {output_raw_file}...")
    with open(output_raw_file, "w", encoding="utf-8") as f:
        json.dump(all_harvested_works, f, indent=2)

    # Save harvest log
    log_file = os.path.join(DATA_RAW_DIR, "openalex_collection_log.json")
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(harvest_log, f, indent=2)

    print(f"[Done] Total Harvested Works: {len(all_harvested_works)}")
    return all_harvested_works

if __name__ == "__main__":
    harvest_stratified_openalex_corpus()
