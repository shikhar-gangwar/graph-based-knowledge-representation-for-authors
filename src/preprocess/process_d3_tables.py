"""
D3 Data Transformation and Graph Table Generator
Parses raw D3 snapshot JSON and creates clean, deduplicated, relational CSV tables:
- works.csv
- authors.csv
- authorships.csv
- venues.csv
- topics.csv
- work_topics.csv
- coauthorship_edges.csv (Newman-weighted)
Tracks row counts before and after every cleaning step.
"""

import os
import json
import csv
import re
import hashlib
from collections import defaultdict
from typing import Dict, Any, List, Set, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
RAW_SNAPSHOT = os.path.join(BASE_DIR, "data", "raw", "d3_raw_snapshot_1000.json")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
GRAPH_READY_DIR = os.path.join(BASE_DIR, "data", "graph_ready")
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(GRAPH_READY_DIR, exist_ok=True)

def generate_venue_id(venue_name: str) -> str:
    """Generates deterministic clean ID for a venue."""
    cleaned = re.sub(r'[^a-zA-Z0-9]', '_', venue_name.strip().lower())
    cleaned = re.sub(r'_+', '_', cleaned).strip('_')
    if len(cleaned) > 40:
        cleaned = cleaned[:32] + "_" + hashlib.md5(venue_name.encode('utf-8')).hexdigest()[:6]
    return f"V_{cleaned}" if cleaned else "V_unknown"

def generate_topic_id(topic_name: str) -> str:
    """Generates deterministic clean ID for a CSO concept."""
    cleaned = re.sub(r'[^a-zA-Z0-9]', '_', topic_name.strip().lower())
    cleaned = re.sub(r'_+', '_', cleaned).strip('_')
    return f"T_{cleaned}"

def process_d3_corpus():
    print("=" * 70)
    print("TRANSFORMING D3 SNAPSHOT INTO RELATIONAL AND GRAPH TABLES")
    print(f"Input Snapshot: {RAW_SNAPSHOT}")
    print("=" * 70)

    if not os.path.exists(RAW_SNAPSHOT):
        raise FileNotFoundError(f"Snapshot not found: {RAW_SNAPSHOT}")

    with open(RAW_SNAPSHOT, "r", encoding="utf-8") as f:
        records: List[Dict[str, Any]] = json.load(f)

    raw_works_count = len(records)
    print(f"Raw Input Records Count: {raw_works_count}")

    works = {}
    authors = {}
    venues = {}
    topics = {}
    authorships = []
    work_topics = []

    seen_dois = set()
    seen_corpusids = set()
    duplicate_works = 0

    raw_authorship_events = 0
    raw_topic_assignments = 0

    for r in records:
        corpusid = r.get("corpusid")
        if corpusid is None:
            continue
        corpusid_str = str(corpusid)

        # Deduplication by corpusid or DOI
        ext_ids = r.get("externalids") or {}
        doi = ext_ids.get("DOI") or ""
        doi_clean = doi.strip().lower()

        if corpusid_str in seen_corpusids or (doi_clean and doi_clean in seen_dois):
            duplicate_works += 1
            continue

        seen_corpusids.add(corpusid_str)
        if doi_clean:
            seen_dois.add(doi_clean)

        title = (r.get("title") or "").strip()
        abstract = (r.get("abstract") or "").strip()
        year = r.get("year")
        venue_str = (r.get("venue") or "").strip()
        cit_count = r.get("citationcount", 0)
        ref_count = r.get("referencecount", 0)
        dblp_key = ext_ids.get("DBLP") or ""

        # 1. Venue Table
        venue_id = "V_unknown"
        if venue_str:
            venue_id = generate_venue_id(venue_str)
            if venue_id not in venues:
                venues[venue_id] = {
                    "venue_id": venue_id,
                    "name": venue_str
                }

        # 2. Works Table
        works[corpusid_str] = {
            "paper_id": corpusid_str,
            "doi": doi_clean,
            "dblp_key": dblp_key,
            "title": title,
            "year": year,
            "venue_id": venue_id,
            "citation_count": cit_count,
            "reference_count": ref_count,
            "abstract": abstract[:1000] # compact abstract
        }

        # 3. Authors & Authorships
        paper_authors = r.get("authors") or []
        for pos, a in enumerate(paper_authors):
            raw_authorship_events += 1
            aid = str(a.get("authorId") or "").strip()
            name = (a.get("name") or "").strip()
            if not name:
                continue

            # Deterministic ID assignment if authorId missing from source
            if not aid or aid == "None":
                aid = "A_anon_" + hashlib.md5(f"{name}_{venue_id}_{corpusid_str}".encode('utf-8')).hexdigest()[:10]

            if aid not in authors:
                authors[aid] = {
                    "author_id": aid,
                    "name": name
                }

            authorships.append({
                "author_id": aid,
                "paper_id": corpusid_str,
                "author_position": pos + 1
            })

        # 4. Topics & Work_Topics
        cso_all = set((r.get("cso_enhanced") or []) + (r.get("cso_semantic") or []))
        for t_name in cso_all:
            raw_topic_assignments += 1
            t_str = str(t_name).strip()
            if not t_str:
                continue
            tid = generate_topic_id(t_str)
            if tid not in topics:
                topics[tid] = {
                    "topic_id": tid,
                    "name": t_str.title()
                }
            work_topics.append({
                "paper_id": corpusid_str,
                "topic_id": tid
            })

    # 5. Compute Weighted Co-Authorship Edges (Newman Formula)
    print("\n[Topology] Computing Newman weighted co-authorship projection...")
    paper_to_authors = defaultdict(list)
    for link in authorships:
        paper_to_authors[link["paper_id"]].append(link["author_id"])

    pair_weights = defaultdict(float)
    pair_counts = defaultdict(int)

    for pid, a_list in paper_to_authors.items():
        unique_a = sorted(list(set(a_list)))
        n = len(unique_a)
        if n < 2:
            continue
        inc = 1.0 / (n - 1)
        for i in range(n):
            for j in range(i + 1, n):
                u, v = unique_a[i], unique_a[j]
                pair_weights[(u, v)] += inc
                pair_counts[(u, v)] += 1

    coauthorship_edges = []
    for (u, v), w in pair_weights.items():
        coauthorship_edges.append({
            "author_id_1": u,
            "author_id_2": v,
            "weight": round(w, 4),
            "papers_count": pair_counts[(u, v)]
        })

    # Cleaning and Filtering Summary Report
    print("\n--- Data Pipeline Transformations & Record Counts ---")
    print(f"  Raw Works Inspected:       {raw_works_count:>6}")
    print(f"  Duplicate Works Removed:   {duplicate_works:>6}")
    print(f"  Final Cleaned Works:       {len(works):>6}")
    print(f"  Unique Authors Discovered: {len(authors):>6}")
    print(f"  Unique Venues Discovered:  {len(venues):>6}")
    print(f"  Unique CSO Topics:         {len(topics):>6}")
    print(f"  Total Authorship Edges:    {len(authorships):>6} (from {raw_authorship_events} raw events)")
    print(f"  Total Work-Topic Edges:    {len(work_topics):>6} (from {raw_topic_assignments} raw events)")
    print(f"  Co-authorship Network Edges:{len(coauthorship_edges):>6}")

    # Write tables to processed and graph_ready
    tables = [
        ("works.csv", list(works.values()), ["paper_id", "doi", "dblp_key", "title", "year", "venue_id", "citation_count", "reference_count", "abstract"]),
        ("authors.csv", list(authors.values()), ["author_id", "name"]),
        ("venues.csv", list(venues.values()), ["venue_id", "name"]),
        ("topics.csv", list(topics.values()), ["topic_id", "name"]),
        ("authorships.csv", authorships, ["author_id", "paper_id", "author_position"]),
        ("work_topics.csv", work_topics, ["paper_id", "topic_id"]),
        ("coauthorship_edges.csv", coauthorship_edges, ["author_id_1", "author_id_2", "weight", "papers_count"])
    ]

    for fname, data, headers in tables:
        # Write to processed
        p_path = os.path.join(PROCESSED_DIR, fname)
        with open(p_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
            
        # Write to graph_ready
        g_path = os.path.join(GRAPH_READY_DIR, fname)
        with open(g_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)

    print(f"\n[Success] All relational and graph tables successfully created in data/processed/ and data/graph_ready/.")

if __name__ == "__main__":
    process_d3_corpus()
