"""
Co-Authorship Network Builder for OpenAlex 5,000-work Corpus.
Computes Newman-weighted collaboration edges from data/processed/authorships.csv:
- Correctly handles single-author papers (produces 0 co-authorship edges).
- Deduplicates duplicate author occurrences on the same work.
- Guarantees undirected unique edge pairs (u < v).
- Generates data/processed/coauthorship_edges.csv and coauthorship_nodes.csv.
"""

import os
import csv
from collections import defaultdict
from typing import Dict, Any, List, Set, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

def build_coauthorship_network():
    print("=" * 80)
    print("BUILDING NEWMAN-WEIGHTED CO-AUTHORSHIP NETWORK")
    print(f"Directory: {PROCESSED_DIR}")
    print("=" * 80)

    # 1. Load Authorships & Works
    authorships_path = os.path.join(PROCESSED_DIR, "authorships.csv")
    works_path = os.path.join(PROCESSED_DIR, "works.csv")
    authors_path = os.path.join(PROCESSED_DIR, "authors.csv")

    with open(authors_path, "r", encoding="utf-8") as f:
        authors_rows = list(csv.DictReader(f))
    author_name_map = {r["author_id"]: r["name"] for r in authors_rows}

    with open(works_path, "r", encoding="utf-8") as f:
        works_rows = list(csv.DictReader(f))
    work_year_map = {r["paper_id"]: int(r["publication_year"]) for r in works_rows if r["publication_year"].isdigit()}

    with open(authorships_path, "r", encoding="utf-8") as f:
        authorships_rows = list(csv.DictReader(f))

    print(f"Loaded {len(authors_rows):,} authors, {len(works_rows):,} works, {len(authorships_rows):,} authorships.")

    # Group authors by paper, deduplicating author occurrences per paper
    paper_authors = defaultdict(set)
    for row in authorships_rows:
        pid = row["paper_id"]
        aid = row["author_id"]
        paper_authors[pid].add(aid)

    # Co-authorship accumulation
    pair_weights = defaultdict(float)
    pair_counts = defaultdict(int)
    pair_years = defaultdict(set)
    single_author_papers = 0
    multi_author_papers = 0

    for pid, authors_set in paper_authors.items():
        authors = sorted(list(authors_set))
        n_authors = len(authors)
        if n_authors < 2:
            single_author_papers += 1
            continue
        
        multi_author_papers += 1
        weight_inc = 1.0 / (n_authors - 1)
        pyear = work_year_map.get(pid)

        for i in range(n_authors):
            for j in range(i + 1, n_authors):
                u, v = authors[i], authors[j]
                pair_weights[(u, v)] += weight_inc
                pair_counts[(u, v)] += 1
                if pyear:
                    pair_years[(u, v)].add(pyear)

    print(f"\n[Paper Authorship Breakdown]")
    print(f"  - Multi-Author Papers (produce edges): {multi_author_papers:,}")
    print(f"  - Single-Author Papers (zero edges):   {single_author_papers:,}")
    print(f"  - Unique Co-Author Pairs (u < v):     {len(pair_weights):,}")

    # Build coauthorship edges list
    edges_data = []
    active_authors = set()

    for (u, v), w in pair_weights.items():
        active_authors.add(u)
        active_authors.add(v)
        years_list = sorted(list(pair_years[(u, v)]))
        edges_data.append({
            "author_id_1": u,
            "author_id_2": v,
            "weight": round(w, 5),
            "papers_count": pair_counts[(u, v)],
            "first_year": years_list[0] if years_list else "",
            "last_year": years_list[-1] if years_list else ""
        })

    # Build coauthorship nodes list (active authors)
    nodes_data = []
    for aid in sorted(list(active_authors)):
        nodes_data.append({
            "author_id": aid,
            "name": author_name_map.get(aid, "Unknown"),
            "is_active_coauthor": "true"
        })

    # Add isolated authors (single-author only)
    isolated_authors = set(author_name_map.keys()) - active_authors
    for aid in sorted(list(isolated_authors)):
        nodes_data.append({
            "author_id": aid,
            "name": author_name_map.get(aid, "Unknown"),
            "is_active_coauthor": "false"
        })

    # Write CSVs
    edges_out = os.path.join(PROCESSED_DIR, "coauthorship_edges.csv")
    with open(edges_out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["author_id_1", "author_id_2", "weight", "papers_count", "first_year", "last_year"])
        writer.writeheader()
        writer.writerows(edges_data)

    nodes_out = os.path.join(PROCESSED_DIR, "coauthorship_nodes.csv")
    with open(nodes_out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["author_id", "name", "is_active_coauthor"])
        writer.writeheader()
        writer.writerows(nodes_data)

    print(f"\n[Success] Wrote {len(edges_data):,} edges to: {edges_out}")
    print(f"[Success] Wrote {len(nodes_data):,} nodes ({len(active_authors):,} active, {len(isolated_authors):,} isolated) to: {nodes_out}")

    return edges_data, nodes_data

if __name__ == "__main__":
    build_coauthorship_network()
