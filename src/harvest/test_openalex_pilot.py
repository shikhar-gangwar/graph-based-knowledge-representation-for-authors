"""
Pilot verification script for OpenAlex Works API.
Fetches 100 high-impact AI/ML publications (2016-2025) under Subfield 1702 (Artificial Intelligence).
Audits relevance, field coverage, author identifiers, institutions, and topics.
"""

import os
import json
import urllib.request
from typing import Dict, Any, List

PILOT_URL = (
    "https://api.openalex.org/works"
    "?filter=primary_topic.subfield.id:1702,publication_year:2016-2025,type:article|conference-paper,is_retracted:false,is_paratext:false"
    "&sort=cited_by_count:desc"
    "&per-page=100"
)
USER_AGENT = "ResearchKG-AcademicBot/1.0 (mailto:academic.researcher@university.edu)"

def fetch_and_audit_pilot():
    print(f"Fetching 100-work pilot from OpenAlex: {PILOT_URL}")
    req = urllib.request.Request(PILOT_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    results = data.get("results", [])
    print(f"Retrieved {len(results)} pilot works.")

    # Field audit
    has_doi = sum(1 for w in results if w.get("doi"))
    has_abstract = sum(1 for w in results if w.get("abstract_inverted_index"))
    has_venue = sum(1 for w in results if (w.get("primary_location") or {}).get("source"))
    has_institutions = 0
    total_authorships = 0
    authors_with_id = 0

    for w in results:
        authorships = w.get("authorships") or []
        for a in authorships:
            total_authorships += 1
            if (a.get("author") or {}).get("id"):
                authors_with_id += 1
            if a.get("institutions"):
                has_institutions += 1

    print("\n--- Field Coverage (N=100 Pilot) ---")
    print(f"  DOIs Present:             {has_doi}/100 ({has_doi}%)")
    print(f"  Abstract Inverted Index:  {has_abstract}/100 ({has_abstract}%)")
    print(f"  Venue (Source) Present:   {has_venue}/100 ({has_venue}%)")
    print(f"  Total Authorships:        {total_authorships}")
    print(f"  Authors with Stable ID:   {authors_with_id}/{total_authorships} ({authors_with_id/total_authorships*100:.1f}%)")
    print(f"  Affiliations with Inst:   {has_institutions}/{total_authorships} ({has_institutions/total_authorships*100:.1f}%)")

    print("\n--- Top 10 High-Impact AI/ML Publications in Pilot ---")
    for i, w in enumerate(results[:10], 1):
        title = w.get("title") or "N/A"
        year = w.get("publication_year")
        cites = w.get("cited_by_count", 0)
        ptopic = (w.get("primary_topic") or {}).get("display_name", "N/A")
        print(f"[{i:02d}] {title[:70]}... ({year} | Cites: {cites:,} | Topic: {ptopic})")

if __name__ == "__main__":
    fetch_and_audit_pilot()
