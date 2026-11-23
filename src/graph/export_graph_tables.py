"""
Graph Export Module for Neo4j Knowledge Graph
Transforms processed entities into standardized CSV tables for Neo4j bulk ingestion.
Computes Newman's weighted co-authorship projections and resolves internal citation subgraphs.
"""

import os
import json
import csv
from collections import defaultdict
from typing import Dict, Any, List

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
GRAPH_READY_DIR = os.path.join(BASE_DIR, "data", "graph_ready")
os.makedirs(GRAPH_READY_DIR, exist_ok=True)

def load_json(filename: str):
    path = os.path.join(PROCESSED_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_csv(data: List[Dict[str, Any]], fieldnames: List[str], filename: str):
    path = os.path.join(GRAPH_READY_DIR, filename)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(data)
    print(f"[Export] Wrote {len(data)} rows to: {filename}")

def build_coauthorship_network(authored_links: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Computes weighted co-authorship edges between authors using Newman's formula:
    Weight(u, v) = sum_{p in P(u,v)} (1 / (|Authors(p)| - 1))
    """
    paper_to_authors = defaultdict(list)
    for link in authored_links:
        aid = link.get("author_id") or link.get(":START_ID(Author)")
        pid = link.get("paper_id") or link.get(":END_ID(Publication)")
        if aid and pid:
            paper_to_authors[pid].append(aid)

    pair_weights = defaultdict(float)
    pair_counts = defaultdict(int)

    for paper_id, authors in paper_to_authors.items():
        unique_authors = sorted(list(set(authors)))
        n_authors = len(unique_authors)
        if n_authors < 2:
            continue
            
        weight_increment = 1.0 / (n_authors - 1)
        for i in range(n_authors):
            for j in range(i + 1, n_authors):
                u, v = unique_authors[i], unique_authors[j]
                pair_weights[(u, v)] += weight_increment
                pair_counts[(u, v)] += 1

    coauthored_edges = []
    for (u, v), weight in pair_weights.items():
        coauthored_edges.append({
            ":START_ID(Author)": u,
            ":END_ID(Author)": v,
            "weight:float": round(weight, 4),
            "papers_count:int": pair_counts[(u, v)]
        })

    return coauthored_edges

def export_all():
    print("[Export] Starting graph table generation for Neo4j...")
    
    # Load processed entities
    publications = load_json("publications.json")
    canonical_authors = load_json("canonical_authors.json")
    institutions = load_json("institutions.json")
    venues = load_json("venues.json")
    topics = load_json("enriched_topics.json")
    
    authored_links = load_json("disambiguated_authored_links.json")
    affiliated_links = load_json("disambiguated_affiliated_links.json")
    published_in_links = load_json("published_in_links.json")
    has_topic_links = load_json("enriched_has_topic_links.json")
    citation_links = load_json("citation_links.json")

    # Set of valid paper IDs for internal referential integrity
    valid_paper_ids = {p["paper_id"] for p in publications}
    valid_author_ids = {a["author_id"] for a in canonical_authors}
    valid_institution_ids = {i["institution_id"] for i in institutions}
    valid_venue_ids = {v["venue_id"] for v in venues}
    valid_topic_ids = {t["topic_id"] for t in topics}

    # 1. Nodes: Publications
    node_pubs = []
    for p in publications:
        node_pubs.append({
            "paper_id:ID(Publication)": p["paper_id"],
            "doi": p.get("doi", ""),
            "title": p.get("title", ""),
            "publication_year:int": p.get("publication_year") or 0,
            "citation_count:int": p.get("citation_count") or 0,
            "type": p.get("type", "article"),
            "abstract": p.get("abstract", "")[:500]  # compact abstract for Neo4j node storage
        })
    write_csv(node_pubs, ["paper_id:ID(Publication)", "doi", "title", "publication_year:int", "citation_count:int", "type", "abstract"], "nodes_publication.csv")

    # 2. Nodes: Authors
    node_authors = []
    for a in canonical_authors:
        node_authors.append({
            "author_id:ID(Author)": a["author_id"],
            "name": a.get("name", ""),
            "orcid": a.get("orcid", ""),
            "merged_count:int": a.get("merged_count", 1)
        })
    write_csv(node_authors, ["author_id:ID(Author)", "name", "orcid", "merged_count:int"], "nodes_author.csv")

    # 3. Nodes: Institutions
    node_insts = []
    for i in institutions:
        node_insts.append({
            "institution_id:ID(Institution)": i["institution_id"],
            "name": i.get("name", ""),
            "country_code": i.get("country_code", ""),
            "ror": i.get("ror", "")
        })
    write_csv(node_insts, ["institution_id:ID(Institution)", "name", "country_code", "ror"], "nodes_institution.csv")

    # 4. Nodes: Venues
    node_venues = []
    for v in venues:
        node_venues.append({
            "venue_id:ID(Venue)": v["venue_id"],
            "name": v.get("name", ""),
            "type": v.get("type", "journal"),
            "issn": v.get("issn", "")
        })
    write_csv(node_venues, ["venue_id:ID(Venue)", "name", "type", "issn"], "nodes_venue.csv")

    # 5. Nodes: Topics
    node_topics = []
    seen_topic_ids = set()
    for t in topics:
        tid = t["topic_id"]
        if tid in seen_topic_ids:
            continue
        seen_topic_ids.add(tid)
        node_topics.append({
            "topic_id:ID(Topic)": tid,
            "name": t.get("name", ""),
            "subfield": t.get("subfield", ""),
            "field": t.get("field", ""),
            "domain": t.get("domain", "")
        })
    write_csv(node_topics, ["topic_id:ID(Topic)", "name", "subfield", "field", "domain"], "nodes_topic.csv")

    # 6. Edges: AUTHORED
    edge_authored = []
    seen_authored = set()
    for link in authored_links:
        aid = link["author_id"]
        pid = link["paper_id"]
        if aid in valid_author_ids and pid in valid_paper_ids:
            key = (aid, pid)
            if key not in seen_authored:
                seen_authored.add(key)
                edge_authored.append({
                    ":START_ID(Author)": aid,
                    ":END_ID(Publication)": pid,
                    "author_position:int": link["author_position"],
                    "is_corresponding:boolean": str(link["is_corresponding"]).lower()
                })
    write_csv(edge_authored, [":START_ID(Author)", ":END_ID(Publication)", "author_position:int", "is_corresponding:boolean"], "edges_authored.csv")

    # 7. Edges: AFFILIATED_WITH
    edge_affil = []
    seen_affil = set()
    for link in affiliated_links:
        aid = link["author_id"]
        iid = link["institution_id"]
        if aid in valid_author_ids and iid in valid_institution_ids:
            key = (aid, iid)
            if key not in seen_affil:
                seen_affil.add(key)
                edge_affil.append({
                    ":START_ID(Author)": aid,
                    ":END_ID(Institution)": iid
                })
    write_csv(edge_affil, [":START_ID(Author)", ":END_ID(Institution)"], "edges_affiliated_with.csv")

    # 8. Edges: PUBLISHED_IN
    edge_pubin = []
    seen_pubin = set()
    for link in published_in_links:
        pid = link["paper_id"]
        vid = link["venue_id"]
        if pid in valid_paper_ids and vid in valid_venue_ids:
            key = (pid, vid)
            if key not in seen_pubin:
                seen_pubin.add(key)
                edge_pubin.append({
                    ":START_ID(Publication)": pid,
                    ":END_ID(Venue)": vid
                })
    write_csv(edge_pubin, [":START_ID(Publication)", ":END_ID(Venue)"], "edges_published_in.csv")

    # 9. Edges: HAS_TOPIC
    edge_topic = []
    seen_topic_edges = set()
    for link in has_topic_links:
        pid = link["paper_id"]
        tid = link["topic_id"]
        if pid in valid_paper_ids and tid in valid_topic_ids:
            key = (pid, tid)
            if key not in seen_topic_edges:
                seen_topic_edges.add(key)
                edge_topic.append({
                    ":START_ID(Publication)": pid,
                    ":END_ID(Topic)": tid,
                    "score:float": link.get("score", 1.0)
                })
    write_csv(edge_topic, [":START_ID(Publication)", ":END_ID(Topic)", "score:float"], "edges_has_topic.csv")

    # 10. Edges: CITES (Internal Network Citations)
    edge_cites = []
    seen_cites = set()
    for link in citation_links:
        src = link["source_paper_id"]
        tgt = link["target_paper_id"]
        # Only retain citation links where target is also within our harvested corpus
        if src in valid_paper_ids and tgt in valid_paper_ids:
            key = (src, tgt)
            if key not in seen_cites:
                seen_cites.add(key)
                edge_cites.append({
                    ":START_ID(Publication)": src,
                    ":END_ID(Publication)": tgt
                })
    write_csv(edge_cites, [":START_ID(Publication)", ":END_ID(Publication)"], "edges_cites.csv")

    # 11. Edges: CO_AUTHORED_WITH (Weighted Projections)
    edge_coauth = build_coauthorship_network(edge_authored)
    write_csv(edge_coauth, [":START_ID(Author)", ":END_ID(Author)", "weight:float", "papers_count:int"], "edges_co_authored_with.csv")

    print("[Export] All graph tables successfully generated in data/graph_ready/.")

if __name__ == "__main__":
    export_all()
