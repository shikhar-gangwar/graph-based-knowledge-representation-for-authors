"""
NLP Entity Extraction & Author Name Disambiguation (AND) Module
Performs multi-signal author disambiguation (ORCID, name similarity, co-authorship overlap, affiliation)
and extracts scientific keywords/topics using TF-IDF n-gram modeling.
"""

import os
import json
import re
from collections import defaultdict
from typing import Dict, Any, List, Set, Tuple
from rapidfuzz import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

def load_json(filename: str):
    path = os.path.join(PROCESSED_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data: Any, filename: str):
    path = os.path.join(PROCESSED_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def normalize_author_name(name: str) -> str:
    """Normalizes author name for blocking: removes punctuation, lowers case, trims."""
    if not name:
        return ""
    name = re.sub(r'[^\w\s]', '', name.lower())
    return re.sub(r'\s+', ' ', name).strip()

def get_name_blocking_key(name: str) -> str:
    """
    Generates a phonetic/token blocking key: Last name + first initial.
    e.g. 'Jure Leskovec' -> 'leskovec_j'
    """
    tokens = normalize_author_name(name).split()
    if not tokens:
        return "unknown"
    if len(tokens) == 1:
        return tokens[0]
    last_name = tokens[-1]
    first_initial = tokens[0][0]
    return f"{last_name}_{first_initial}"

def disambiguate_authors(authors: List[Dict[str, Any]], 
                         authored_links: List[Dict[str, Any]], 
                         affiliated_links: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, str], Dict[str, Any]]:
    """
    Multi-signal Author Name Disambiguation (AND):
    1. Direct ORCID identity mapping.
    2. Name Blocking by (last_name + first_initial).
    3. Pairwise verification within blocks using Fuzzy Name Matching + Co-author overlap + Affiliation overlap.
    """
    print("[AND] Performing Author Name Disambiguation...")
    
    # Build author lookup
    author_by_id = {a["author_id"]: a for a in authors}
    
    # Build author-paper index
    author_papers = defaultdict(set)
    paper_authors = defaultdict(set)
    for link in authored_links:
        aid = link["author_id"]
        pid = link["paper_id"]
        author_papers[aid].add(pid)
        paper_authors[pid].add(aid)
        
    # Build co-author index
    author_coauthors = defaultdict(set)
    for aid, papers in author_papers.items():
        for pid in papers:
            for co_aid in paper_authors[pid]:
                if co_aid != aid:
                    author_coauthors[aid].add(co_aid)
                    
    # Build author-institution index
    author_institutions = defaultdict(set)
    for link in affiliated_links:
        aid = link["author_id"]
        iid = link["institution_id"]
        author_institutions[aid].add(iid)

    # 1. ORCID clustering
    orcid_clusters = defaultdict(list)
    for aid, author in author_by_id.items():
        orcid = author.get("orcid")
        if orcid:
            orcid_clusters[orcid].append(aid)

    # 2. Blocking by surname + first initial
    blocks = defaultdict(list)
    for aid, author in author_by_id.items():
        key = get_name_blocking_key(author.get("name", ""))
        blocks[key].append(aid)

    author_to_canonical = {}
    disambiguation_merges = 0
    
    # Process within blocks
    for block_key, aids in blocks.items():
        if len(aids) == 1:
            author_to_canonical[aids[0]] = aids[0]
            continue
            
        # Group within block using disjoint-set / greedy clustering
        clusters = [] # list of sets of aids
        for aid in aids:
            assigned = False
            a_name = normalize_author_name(author_by_id[aid]["name"])
            a_orcid = author_by_id[aid].get("orcid")
            a_coauth = author_coauthors[aid]
            a_insts = author_institutions[aid]
            
            for cluster in clusters:
                # Compare aid against representative in cluster
                rep = next(iter(cluster))
                rep_name = normalize_author_name(author_by_id[rep]["name"])
                rep_orcid = author_by_id[rep].get("orcid")
                rep_coauth = author_coauthors[rep]
                rep_insts = author_institutions[rep]
                
                # Condition A: Identical ORCID
                if a_orcid and rep_orcid and a_orcid == rep_orcid:
                    cluster.add(aid)
                    assigned = True
                    break
                    
                # Condition B: High name similarity + (shared co-authors OR shared institution)
                name_sim = fuzz.token_sort_ratio(a_name, rep_name)
                shared_coauthors = len(a_coauth.intersection(rep_coauth))
                shared_institutions = len(a_insts.intersection(rep_insts))
                
                if name_sim >= 90 and (shared_coauthors >= 1 or shared_institutions >= 1):
                    cluster.add(aid)
                    assigned = True
                    disambiguation_merges += 1
                    break
                    
            if not assigned:
                clusters.append({aid})
                
        for cluster in clusters:
            canonical_id = sorted(list(cluster))[0]
            for member in cluster:
                author_to_canonical[member] = canonical_id

    # Create canonical author entities
    canonical_authors = {}
    for aid, author in author_by_id.items():
        canon_id = author_to_canonical[aid]
        if canon_id not in canonical_authors:
            canonical_authors[canon_id] = {
                "author_id": canon_id,
                "name": author["name"],
                "orcid": author.get("orcid", ""),
                "merged_count": 1
            }
        else:
            canonical_authors[canon_id]["merged_count"] += 1
            # Preserve orcid if representative was missing it
            if not canonical_authors[canon_id]["orcid"] and author.get("orcid"):
                canonical_authors[canon_id]["orcid"] = author["orcid"]

    stats = {
        "raw_author_count": len(authors),
        "canonical_author_count": len(canonical_authors),
        "disambiguation_merges": disambiguation_merges,
        "total_blocks_analyzed": len(blocks)
    }
    print(f"[AND] Disambiguation Complete: {len(authors)} raw entities resolved to {len(canonical_authors)} canonical authors.")
    return list(canonical_authors.values()), author_to_canonical, stats

def extract_nlp_keywords(publications: List[Dict[str, Any]], top_k: int = 5) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Extracts key scientific terms from titles and abstracts using TF-IDF n-gram vectorization.
    Generates new keyword entities and publication-to-keyword edges.
    """
    print("[NLP] Extracting scientific terms & keywords using TF-IDF...")
    corpus = []
    paper_ids = []
    
    for pub in publications:
        text = f"{pub.get('title', '')} {pub.get('abstract', '')}".strip()
        if len(text) > 10:
            corpus.append(text)
            paper_ids.append(pub["paper_id"])

    # Vectorize with unigram and bigrams, stripping English stop words
    vectorizer = TfidfVectorizer(
        max_df=0.6,
        min_df=3,
        ngram_range=(1, 2),
        stop_words="english",
        max_features=1500
    )
    
    tfidf_matrix = vectorizer.fit_transform(corpus)
    feature_names = vectorizer.get_feature_names_out()
    
    extracted_keywords = {}
    has_keyword_links = []
    
    for i, paper_id in enumerate(paper_ids):
        row = tfidf_matrix.getrow(i).toarray().flatten()
        top_indices = row.argsort()[::-1][:top_k]
        
        for idx in top_indices:
            score = float(row[idx])
            if score > 0.15:
                kw_text = feature_names[idx].title()
                kw_id = f"KW_{re.sub(r'[^a-zA-Z0-9]', '_', kw_text.lower())}"
                
                if kw_id not in extracted_keywords:
                    extracted_keywords[kw_id] = {
                        "topic_id": kw_id,
                        "name": kw_text,
                        "subfield": "NLP-Extracted Keyword",
                        "field": "Computer Science",
                        "domain": "Machine Learning"
                    }
                    
                has_keyword_links.append({
                    "paper_id": paper_id,
                    "topic_id": kw_id,
                    "score": round(score, 4)
                })

    print(f"[NLP] Extracted {len(extracted_keywords)} unique keywords and {len(has_keyword_links)} links.")
    return list(extracted_keywords.values()), has_keyword_links

def run_disambiguation_and_extraction():
    authors = load_json("authors.json")
    authored_links = load_json("authored_links.json")
    affiliated_links = load_json("affiliated_links.json")
    publications = load_json("publications.json")
    existing_topics = load_json("topics.json")
    existing_topic_links = load_json("has_topic_links.json")

    # 1. Author Disambiguation
    canonical_authors, author_mapping, and_stats = disambiguate_authors(authors, authored_links, affiliated_links)
    
    # Remap authored and affiliated links to canonical author IDs
    updated_authored_links = []
    for link in authored_links:
        updated_authored_links.append({
            "author_id": author_mapping[link["author_id"]],
            "paper_id": link["paper_id"],
            "author_position": link["author_position"],
            "is_corresponding": link["is_corresponding"]
        })
        
    updated_affiliated_links = []
    for link in affiliated_links:
        updated_affiliated_links.append({
            "author_id": author_mapping[link["author_id"]],
            "institution_id": link["institution_id"],
            "paper_id": link["paper_id"]
        })

    # 2. NLP Keyword Extraction
    nlp_keywords, nlp_topic_links = extract_nlp_keywords(publications)

    # Merge existing topics with NLP keywords
    all_topics = existing_topics + nlp_keywords
    all_has_topic_links = existing_topic_links + nlp_topic_links

    # Save disambiguated & enriched artifacts
    save_json(canonical_authors, "canonical_authors.json")
    save_json(updated_authored_links, "disambiguated_authored_links.json")
    save_json(updated_affiliated_links, "disambiguated_affiliated_links.json")
    save_json(all_topics, "enriched_topics.json")
    save_json(all_has_topic_links, "enriched_has_topic_links.json")
    save_json(and_stats, "and_evaluation_stats.json")

    print("[Pipeline] Entity Extraction & Disambiguation successfully completed.")

if __name__ == "__main__":
    run_disambiguation_and_extraction()
