"""
Pilot Validation and Missingness Inspection Script
Analyzes the 100-record D3 pilot dataset:
- Evaluates field completeness and missingness rates.
- Manually inspects a sample for domain relevance and false positives/negatives.
- Audits author linkages, unique authors, and venues.
"""

import os
import json
from typing import Dict, Any, List

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
PILOT_PATH = os.path.join(BASE_DIR, "data", "raw", "d3_raw_snapshot_100.json")

def inspect_pilot():
    print("=" * 70)
    print("D3 PILOT DATASET AUDIT & FIELD COMPLETENESS REPORT (N=100)")
    print("=" * 70)

    with open(PILOT_PATH, "r", encoding="utf-8") as f:
        records: List[Dict[str, Any]] = json.load(f)

    total = len(records)
    print(f"Total Pilot Records Loaded: {total}")

    # Field presence tracking
    fields = {
        "corpusid": 0,
        "title": 0,
        "abstract": 0,
        "year": 0,
        "venue": 0,
        "citationcount": 0,
        "referencecount": 0,
        "doi": 0,
        "dblp_key": 0,
        "authors_present": 0,
        "cso_topics_present": 0
    }

    total_authors = 0
    authors_with_id = 0
    unique_author_ids = set()
    unique_venues = set()
    years = []
    
    author_counts_per_paper = []

    for r in records:
        if r.get("corpusid") is not None: fields["corpusid"] += 1
        if r.get("title"): fields["title"] += 1
        if r.get("abstract"): fields["abstract"] += 1
        if r.get("year"): 
            fields["year"] += 1
            years.append(r["year"])
        if r.get("venue"): 
            fields["venue"] += 1
            unique_venues.add(r["venue"])
        if r.get("citationcount") is not None: fields["citationcount"] += 1
        if r.get("referencecount") is not None: fields["referencecount"] += 1

        ext_ids = r.get("externalids") or {}
        if ext_ids.get("DOI"): fields["doi"] += 1
        if ext_ids.get("DBLP"): fields["dblp_key"] += 1

        authors = r.get("authors") or []
        if authors:
            fields["authors_present"] += 1
            author_counts_per_paper.append(len(authors))
            for a in authors:
                total_authors += 1
                aid = a.get("authorId")
                if aid and aid != "None" and aid != "":
                    authors_with_id += 1
                    unique_author_ids.add(aid)

        cso = set((r.get("cso_enhanced") or []) + (r.get("cso_semantic") or []))
        if cso: fields["cso_topics_present"] += 1

    print("\n--- Field Completeness & Missingness Rates ---")
    for field, count in fields.items():
        completeness = (count / total) * 100
        missingness = 100 - completeness
        print(f"  {field:<20}: {count:>3}/{total} ({completeness:>5.1f}% present | {missingness:>5.1f}% missing)")

    print("\n--- Author & Network Characteristics ---")
    print(f"  Total Authorship Occurrences: {total_authors}")
    print(f"  Authors with Valid authorId: {authors_with_id} ({(authors_with_id/total_authors)*100:.1f}%)")
    print(f"  Unique Author IDs in Pilot:  {len(unique_author_ids)}")
    print(f"  Unique Venues in Pilot:      {len(unique_venues)}")
    print(f"  Average Authors per Paper:   {sum(author_counts_per_paper)/len(author_counts_per_paper):.2f}")
    print(f"  Publication Year Range:      {min(years)} - {max(years)}")

    print("\n--- Qualitative Relevance Sample (First 5 Papers) ---")
    for i, r in enumerate(records[:5], 1):
        cso = list(set((r.get("cso_enhanced") or []) + (r.get("cso_semantic") or [])))[:4]
        print(f"\n[Paper {i}] CorpusID: {r.get('corpusid')}")
        print(f"  Title:   {r.get('title')}")
        print(f"  Year:    {r.get('year')} | Venue: {r.get('venue', 'N/A')}")
        print(f"  Authors: {', '.join([a.get('name') for a in r.get('authors')[:3]])} (Total: {len(r.get('authors'))})")
        print(f"  Topics:  {cso}")
        print(f"  Abstract Snippet: {r.get('abstract', '')[:140]}...")

if __name__ == "__main__":
    inspect_pilot()
