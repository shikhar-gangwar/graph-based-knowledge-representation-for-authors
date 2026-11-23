"""
Data Harvesting Module for Scholarly Knowledge Graph
Collects bibliographic metadata from OpenAlex and DBLP APIs.
Target domain: Graph Neural Networks & Knowledge Graphs in AI (2020-2025).
"""

import os
import json
import time
import urllib.request
import urllib.parse
from typing import Dict, Any, List

RAW_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "raw")
os.makedirs(RAW_DATA_DIR, exist_ok=True)

USER_AGENT = "ResearchKG-AcademicBot/1.0 (mailto:academic.researcher@university.edu)"

def fetch_openalex_corpus(query: str = "graph neural network knowledge graph", 
                         from_year: int = 2020, 
                         to_year: int = 2025, 
                         target_count: int = 500) -> List[Dict[str, Any]]:
    """
    Fetches scholarly publications from OpenAlex API with pagination.
    Retrieves full author, institution, topic, venue, and citation metadata.
    """
    print(f"[OpenAlex] Starting harvest for query: '{query}' ({from_year}-{to_year}), target: {target_count} papers...")
    base_url = "https://api.openalex.org/works"
    
    # Filter for years and publication types (articles, book chapters, conference papers)
    filters = f"publication_year:{from_year}-{to_year},type:article|book-chapter"
    
    works = []
    page = 1
    per_page = 100
    
    while len(works) < target_count:
        params = {
            "search": query,
            "filter": filters,
            "per-page": per_page,
            "page": page,
            "sort": "cited_by_count:desc"  # Prioritize impactful anchor papers with rich citation links
        }
        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                results = data.get("results", [])
                if not results:
                    print("[OpenAlex] No more results returned.")
                    break
                works.extend(results)
                print(f"[OpenAlex] Retrieved page {page}: {len(results)} works (Total accumulated: {len(works)})")
                
                # Check pagination bounds
                meta = data.get("meta", {})
                if page * per_page >= meta.get("count", 0):
                    break
                page += 1
                time.sleep(0.3)  # Polite API crawling interval
        except Exception as e:
            print(f"[OpenAlex] Error on page {page}: {e}")
            break

    # Truncate to target_count
    works = works[:target_count]
    output_path = os.path.join(RAW_DATA_DIR, "openalex_raw.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(works, f, indent=2)
    print(f"[OpenAlex] Saved {len(works)} raw records to: {output_path}")
    return works

def fetch_dblp_corpus(query: str = "graph neural networks", target_count: int = 100) -> List[Dict[str, Any]]:
    """
    Fetches computer science publication records from DBLP Search API.
    Used for multi-source validation and cross-referencing.
    """
    print(f"[DBLP] Starting harvest for query: '{query}', target: {target_count} papers...")
    base_url = "https://dblp.org/search/publ/api"
    
    params = {
        "q": query,
        "format": "json",
        "h": min(target_count, 100),
        "f": 0
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            hits = data.get("result", {}).get("hits", {}).get("hit", [])
            output_path = os.path.join(RAW_DATA_DIR, "dblp_raw.json")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(hits, f, indent=2)
            print(f"[DBLP] Saved {len(hits)} raw records to: {output_path}")
            return hits
    except Exception as e:
        print(f"[DBLP] Error fetching DBLP data: {e}")
        return []

if __name__ == "__main__":
    print("=" * 60)
    print("Executing Multi-Source Bibliographic Data Harvesting...")
    print("=" * 60)
    # Collect 500 high-impact papers from OpenAlex (creates a substantial network of ~1,500-3,000 authors)
    openalex_records = fetch_openalex_corpus(target_count=500)
    # Collect 100 records from DBLP for computer science venue/author cross-validation
    dblp_records = fetch_dblp_corpus(target_count=100)
    print(f"\nHarvesting Complete! Total OpenAlex: {len(openalex_records)}, DBLP: {len(dblp_records)}")
