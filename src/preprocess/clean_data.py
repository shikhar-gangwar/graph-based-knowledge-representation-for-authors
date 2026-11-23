"""
Data Preprocessing & Normalization Module for Scholarly Knowledge Graph
Cleans bibliographic records, reconstructs inverted abstracts, normalizes DOIs,
deduplicates entries, and extracts structured entities.
"""

import os
import json
import re
from typing import Dict, Any, List, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
RAW_DATA_PATH = os.path.join(BASE_DIR, "data", "raw", "openalex_raw.json")
DBLP_RAW_PATH = os.path.join(BASE_DIR, "data", "raw", "dblp_raw.json")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

def reconstruct_abstract(inverted_index: Optional[Dict[str, List[int]]]) -> str:
    """
    Reconstructs continuous text abstract from OpenAlex's inverted index representation.
    """
    if not inverted_index or not isinstance(inverted_index, dict):
        return ""
    
    word_positions = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    
    word_positions.sort(key=lambda x: x[0])
    return " ".join([word for _, word in word_positions]).strip()

def clean_text(text: Optional[str]) -> str:
    """Cleans whitespace, linebreaks, and non-printable characters."""
    if not text:
        return ""
    text = re.sub(r'[\r\n\t]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def normalize_doi(doi: Optional[str]) -> str:
    """Normalizes DOI string by removing URL prefixes and standardizing to lowercase."""
    if not doi:
        return ""
    doi = doi.strip().lower()
    doi = re.sub(r'^https?://(dx\.)?doi\.org/', '', doi)
    return doi

def clean_id(full_uri: Optional[str]) -> str:
    """Extracts short canonical ID from OpenAlex URI (e.g., https://openalex.org/W1234 -> W1234)."""
    if not full_uri:
        return ""
    return full_uri.rstrip("/").split("/")[-1]

def process_corpus():
    """
    Parses raw OpenAlex data, extracts normalized entity tables, and handles deduplication.
    """
    print(f"[Preprocessing] Reading raw data from: {RAW_DATA_PATH}")
    if not os.path.exists(RAW_DATA_PATH):
        raise FileNotFoundError(f"Raw data file not found at {RAW_DATA_PATH}. Run harvest first.")
        
    with open(RAW_DATA_PATH, "r", encoding="utf-8") as f:
        raw_works = json.load(f)
        
    print(f"[Preprocessing] Processing {len(raw_works)} raw publications...")

    publications = {}
    authors = {}
    institutions = {}
    venues = {}
    topics = {}
    
    # Relationships
    authored_links = []
    affiliated_links = []
    published_in_links = []
    has_topic_links = []
    citation_links = []

    seen_dois = set()
    
    for work in raw_works:
        work_id = clean_id(work.get("id"))
        if not work_id:
            continue
            
        raw_doi = work.get("doi")
        doi = normalize_doi(raw_doi)
        
        # Deduplication check
        if doi:
            if doi in seen_dois:
                continue
            seen_dois.add(doi)
            
        title = clean_text(work.get("title"))
        if not title:
            continue
            
        pub_year = work.get("publication_year")
        citation_count = work.get("cited_by_count", 0)
        abstract = reconstruct_abstract(work.get("abstract_inverted_index"))
        pub_type = work.get("type", "article")

        # 1. Publication Record
        publications[work_id] = {
            "paper_id": work_id,
            "doi": doi,
            "title": title,
            "publication_year": pub_year,
            "citation_count": citation_count,
            "abstract": abstract[:1000] if abstract else "",  # store compact abstract
            "type": pub_type
        }

        # 2. Venues / Sources
        primary_loc = work.get("primary_location") or {}
        source = primary_loc.get("source") or {}
        venue_id = clean_id(source.get("id"))
        if venue_id:
            if venue_id not in venues:
                venues[venue_id] = {
                    "venue_id": venue_id,
                    "name": clean_text(source.get("display_name", "Unknown Venue")),
                    "type": source.get("type", "journal"),
                    "issn": source.get("issn_l", "")
                }
            published_in_links.append({
                "paper_id": work_id,
                "venue_id": venue_id
            })

        # 3. Authorships & Institutions
        authorships = work.get("authorships") or []
        for pos, authorship in enumerate(authorships):
            author_data = authorship.get("author") or {}
            author_id = clean_id(author_data.get("id"))
            if not author_id:
                continue
                
            author_name = clean_text(author_data.get("display_name"))
            orcid = clean_text(author_data.get("orcid", ""))
            
            if author_id not in authors:
                authors[author_id] = {
                    "author_id": author_id,
                    "name": author_name,
                    "orcid": orcid
                }
            
            authored_links.append({
                "author_id": author_id,
                "paper_id": work_id,
                "author_position": pos + 1,
                "is_corresponding": authorship.get("is_corresponding", False)
            })

            # Affiliations for this author
            institutions_list = authorship.get("institutions") or []
            for inst in institutions_list:
                inst_id = clean_id(inst.get("id"))
                if not inst_id:
                    continue
                if inst_id not in institutions:
                    institutions[inst_id] = {
                        "institution_id": inst_id,
                        "name": clean_text(inst.get("display_name", "Unknown Institution")),
                        "country_code": inst.get("country_code", ""),
                        "ror": inst.get("ror", "")
                    }
                affiliated_links.append({
                    "author_id": author_id,
                    "institution_id": inst_id,
                    "paper_id": work_id
                })

        # 4. Topics & Concepts
        topics_list = work.get("topics") or []
        for t in topics_list:
            topic_id = clean_id(t.get("id"))
            if not topic_id:
                continue
            if topic_id not in topics:
                topics[topic_id] = {
                    "topic_id": topic_id,
                    "name": clean_text(t.get("display_name")),
                    "subfield": clean_text(t.get("subfield", {}).get("display_name", "")),
                    "field": clean_text(t.get("field", {}).get("display_name", "")),
                    "domain": clean_text(t.get("domain", {}).get("display_name", ""))
                }
            has_topic_links.append({
                "paper_id": work_id,
                "topic_id": topic_id,
                "score": round(float(t.get("score", 0.0)), 4)
            })

        # 5. Citations (Internal network links)
        ref_works = work.get("referenced_works") or []
        for ref_id_full in ref_works:
            ref_id = clean_id(ref_id_full)
            citation_links.append({
                "source_paper_id": work_id,
                "target_paper_id": ref_id
            })

    # Summary Statistics
    print("\n--- Extracted Corpus Summary ---")
    print(f"Total Publications: {len(publications)}")
    print(f"Total Unique Authors: {len(authors)}")
    print(f"Total Unique Institutions: {len(institutions)}")
    print(f"Total Unique Venues: {len(venues)}")
    print(f"Total Unique Topics: {len(topics)}")
    print(f"Total Authored Edges: {len(authored_links)}")
    print(f"Total Affiliated Edges: {len(affiliated_links)}")
    print(f"Total Published_In Edges: {len(published_in_links)}")
    print(f"Total Has_Topic Edges: {len(has_topic_links)}")
    print(f"Total Citation Edges: {len(citation_links)}")

    # Save to intermediate JSON files in processed dir
    output_files = {
        "publications.json": list(publications.values()),
        "authors.json": list(authors.values()),
        "institutions.json": list(institutions.values()),
        "venues.json": list(venues.values()),
        "topics.json": list(topics.values()),
        "authored_links.json": authored_links,
        "affiliated_links.json": affiliated_links,
        "published_in_links.json": published_in_links,
        "has_topic_links.json": has_topic_links,
        "citation_links.json": citation_links
    }

    for fname, data in output_files.items():
        fpath = os.path.join(PROCESSED_DIR, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    print(f"[Preprocessing] Successfully saved intermediate processed tables to: {PROCESSED_DIR}")

if __name__ == "__main__":
    process_corpus()
