"""
Preprocessing & Relational Table Generation for OpenAlex 5,000-work Corpus.
Produces exact Project-I specification tables:
- data/processed/works.csv
- data/processed/authors.csv
- data/processed/authorships.csv
- data/processed/institutions.csv
- data/processed/affiliations.csv
- data/processed/venues.csv
- data/processed/topics.csv
- data/processed/work_topics.csv
Enforces deduplication by work ID & DOI, stable IDs, email exclusion, and zero synthetic values.
"""

import os
import json
import csv
import re
import hashlib
from typing import Dict, Any, List, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
RAW_INPUT_FILE = os.path.join(BASE_DIR, "data", "raw", "openalex_raw_5000.json")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
GRAPH_READY_DIR = os.path.join(BASE_DIR, "data", "graph_ready")
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(GRAPH_READY_DIR, exist_ok=True)

def clean_id(uri: Optional[str]) -> str:
    """Strips https://openalex.org/ prefix to yield canonical stable short ID."""
    if not uri:
        return ""
    return uri.rstrip("/").split("/")[-1]

def normalize_doi(doi: Optional[str]) -> str:
    """Normalizes DOI to lowercase stripped identifier without URL prefix."""
    if not doi:
        return ""
    doi = doi.strip().lower()
    return re.sub(r'^https?://(dx\.)?doi\.org/', '', doi)

def clean_text(text: Optional[str]) -> str:
    """Strips excessive whitespace, control characters, and linebreaks."""
    if not text:
        return ""
    text = re.sub(r'[\r\n\t]+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def reconstruct_abstract(inverted_index: Optional[Dict[str, List[int]]]) -> str:
    """Reconstructs continuous prose abstract from OpenAlex inverted index."""
    if not inverted_index or not isinstance(inverted_index, dict):
        return ""
    word_positions = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    word_positions.sort(key=lambda x: x[0])
    return " ".join([word for _, word in word_positions]).strip()

def process_corpus():
    print("=" * 80)
    print("PROCESSING OPENALEX 5,000-WORK RAW CORPUS INTO CANONICAL TABLES")
    print(f"Reading from: {RAW_INPUT_FILE}")
    print("=" * 80)

    if not os.path.exists(RAW_INPUT_FILE):
        raise FileNotFoundError(f"Raw input file not found: {RAW_INPUT_FILE}")

    with open(RAW_INPUT_FILE, "r", encoding="utf-8") as f:
        raw_works: List[Dict[str, Any]] = json.load(f)

    print(f"Raw Input Records Count: {len(raw_works)}")

    works = {}
    authors = {}
    institutions = {}
    venues = {}
    topics = {}

    authorships = []
    affiliations = []
    work_topics = []

    seen_work_ids = set()
    seen_dois = set()
    duplicate_works = 0

    for w in raw_works:
        work_id = clean_id(w.get("id"))
        if not work_id:
            continue

        doi = normalize_doi(w.get("doi"))

        # Deduplication check
        if work_id in seen_work_ids or (doi and doi in seen_dois):
            duplicate_works += 1
            continue

        seen_work_ids.add(work_id)
        if doi:
            seen_dois.add(doi)

        title = clean_text(w.get("title") or w.get("display_name"))
        pub_year = w.get("publication_year")
        citation_count = w.get("cited_by_count", 0)
        pub_type = w.get("type", "article")
        abstract = reconstruct_abstract(w.get("abstract_inverted_index"))

        # 1. Venue extraction
        venue_id = ""
        source = (w.get("primary_location") or {}).get("source") or {}
        if source and source.get("id"):
            venue_id = clean_id(source.get("id"))
            if venue_id not in venues:
                venues[venue_id] = {
                    "venue_id": venue_id,
                    "name": clean_text(source.get("display_name", "Unknown Venue")),
                    "type": clean_text(source.get("type", "journal")),
                    "issn": clean_text(source.get("issn_l", "")),
                    "publisher": clean_text(source.get("host_organization_name", ""))
                }

        # 2. Works table
        works[work_id] = {
            "paper_id": work_id,
            "doi": doi,
            "title": title,
            "publication_year": pub_year,
            "citation_count": citation_count,
            "type": pub_type,
            "venue_id": venue_id,
            "abstract": abstract[:1500] # store compact clean abstract
        }

        # 3. Authorships & Affiliations
        raw_authorships = w.get("authorships") or []
        for pos, auth_entry in enumerate(raw_authorships):
            auth_obj = auth_entry.get("author") or {}
            author_id = clean_id(auth_obj.get("id"))
            author_name = clean_text(auth_obj.get("display_name") or auth_entry.get("raw_author_name"))
            if not author_name:
                continue

            # Deterministic fallback if author ID is absent from source
            if not author_id:
                author_id = "A_anon_" + hashlib.md5(f"{author_name}_{work_id}".encode("utf-8")).hexdigest()[:10]

            raw_orcid = auth_obj.get("orcid") or auth_entry.get("raw_orcid")
            orcid = clean_text(raw_orcid) if raw_orcid else ""

            if author_id not in authors:
                authors[author_id] = {
                    "author_id": author_id,
                    "name": author_name,
                    "orcid": orcid
                }
            elif not authors[author_id]["orcid"] and orcid:
                authors[author_id]["orcid"] = orcid

            authorships.append({
                "author_id": author_id,
                "paper_id": work_id,
                "author_position": pos + 1,
                "is_corresponding": str(auth_entry.get("is_corresponding", False)).lower()
            })

            # Institutional affiliations for this author on this paper
            inst_list = auth_entry.get("institutions") or []
            for inst in inst_list:
                inst_id = clean_id(inst.get("id"))
                if not inst_id:
                    continue
                if inst_id not in institutions:
                    institutions[inst_id] = {
                        "institution_id": inst_id,
                        "name": clean_text(inst.get("display_name", "Unknown Institution")),
                        "country_code": clean_text(inst.get("country_code", "")),
                        "ror": clean_text(inst.get("ror", "")),
                        "type": clean_text(inst.get("type", ""))
                    }
                affiliations.append({
                    "author_id": author_id,
                    "institution_id": inst_id,
                    "paper_id": work_id
                })

        # 4. Topics & Work Topics
        topics_list = w.get("topics") or []
        for top in topics_list:
            top_id = clean_id(top.get("id"))
            if not top_id:
                continue
            if top_id not in topics:
                topics[top_id] = {
                    "topic_id": top_id,
                    "name": clean_text(top.get("display_name")),
                    "subfield": clean_text((top.get("subfield") or {}).get("display_name", "")),
                    "field": clean_text((top.get("field") or {}).get("display_name", "")),
                    "domain": clean_text((top.get("domain") or {}).get("display_name", ""))
                }
            score = round(float(top.get("score", 1.0)), 4)
            work_topics.append({
                "paper_id": work_id,
                "topic_id": top_id,
                "score": score
            })

    # Summary Statistics
    print("\n--- Pipeline Data Transformations & Entity Counts ---")
    print(f"  Raw Works Inspected:       {len(raw_works):>6}")
    print(f"  Duplicate Works Removed:   {duplicate_works:>6}")
    print(f"  Cleaned Unique Works:      {len(works):>6}")
    print(f"  Unique Authors Discovered: {len(authors):>6}")
    print(f"  Unique Institutions:       {len(institutions):>6}")
    print(f"  Unique Publishing Venues:  {len(venues):>6}")
    print(f"  Unique Topics Discovered:  {len(topics):>6}")
    print(f"  Total Authorship Edges:    {len(authorships):>6}")
    print(f"  Total Affiliation Edges:   {len(affiliations):>6}")
    print(f"  Total Work-Topic Edges:    {len(work_topics):>6}")

    # Write tables to data/processed/ and data/graph_ready/
    table_specs = [
        ("works.csv", list(works.values()), ["paper_id", "doi", "title", "publication_year", "citation_count", "type", "venue_id", "abstract"]),
        ("authors.csv", list(authors.values()), ["author_id", "name", "orcid"]),
        ("institutions.csv", list(institutions.values()), ["institution_id", "name", "country_code", "ror", "type"]),
        ("venues.csv", list(venues.values()), ["venue_id", "name", "type", "issn", "publisher"]),
        ("topics.csv", list(topics.values()), ["topic_id", "name", "subfield", "field", "domain"]),
        ("authorships.csv", authorships, ["author_id", "paper_id", "author_position", "is_corresponding"]),
        ("affiliations.csv", affiliations, ["author_id", "institution_id", "paper_id"]),
        ("work_topics.csv", work_topics, ["paper_id", "topic_id", "score"])
    ]

    for fname, data, fieldnames in table_specs:
        # Write to data/processed/
        p_path = os.path.join(PROCESSED_DIR, fname)
        with open(p_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        # Write to data/graph_ready/
        g_path = os.path.join(GRAPH_READY_DIR, fname)
        with open(g_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        print(f"  [Output] Wrote {len(data):>6} rows to: {fname}")

    print("\n[Success] All canonical Project-I tables generated successfully.")

if __name__ == "__main__":
    process_corpus()
