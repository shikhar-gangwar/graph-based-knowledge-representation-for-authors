"""
Scholarly Knowledge Graph: Research Collaboration Workbench & Recommender Prototype.
Academic Project Title 34: Graph-Based Knowledge Graph for Research Collaboration Analysis.

Provides:
- Clean academic analytics dashboard (light background, deep navy text, blue accents, orange for recommendations).
- SVG Force-Directed Co-Authorship & Recommendation Network Graph with automatic bounding-box fitting.
- Responsive split-pane layout: prominent graph canvas + structured researcher dossier & recommendations.
- Publication-quality empirical figures & analytics tab with interactive lightbox.
- High-precision author search with exact and prefix ranking across 22,185 researchers.
- Ego-network extraction with Newman collaboration weights and triadic closure.
- Prospective collaborator recommendation engine (Hybrid model: 40% Adamic-Adar + 60% Topic Cosine).
"""

import os
import sys
import csv
import json
import math
from collections import defaultdict, Counter
from typing import Optional, List, Dict

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
import uvicorn

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
FIGURES_DIR = os.path.join(BASE_DIR, "docs", "figures")

app = FastAPI(
    title="Scholarly Collaboration Knowledge Graph",
    description="Interactive Scientific Workbench for Academic Project Title 34",
    version="2.3.0"
)

# -----------------------------------------------------------------------------
# In-Memory Graph and Metadata Store
# -----------------------------------------------------------------------------
authors_map: Dict[str, Dict] = {}          # author_id -> {name, orcid}
works_map: Dict[str, Dict] = {}            # paper_id -> {title, year, venue_id, citation_count}
institutions_map: Dict[str, Dict] = {}     # institution_id -> {name, country_code, ror}
venues_map: Dict[str, Dict] = {}           # venue_id -> {name}
topics_map: Dict[str, Dict] = {}           # topic_id -> {name, subfield}

author_papers = defaultdict(list)          # author_id -> [paper_id]
paper_authors = defaultdict(list)          # paper_id -> [author_id]
paper_topics = defaultdict(list)           # paper_id -> [topic_id]
author_institutions = defaultdict(set)     # author_id -> set of institution_ids

coauthors = defaultdict(dict)              # u -> {v: {'weight': float, 'papers_count': int}}
author_topic_counter = defaultdict(Counter)# u -> Counter(topic_id)
author_topic_norms: Dict[str, float] = {}  # u -> L2 norm of topic vector

communities_summary: List[Dict] = []
global_stats: Dict = {}

def load_data():
    global communities_summary, global_stats
    print("[Dashboard] Loading processed datasets into memory...")

    # 1. Load entities
    with open(os.path.join(PROCESSED_DIR, "authors.csv"), "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            authors_map[r["author_id"]] = {
                "author_id": r["author_id"],
                "name": r["name"],
                "orcid": r.get("orcid", "")
            }

    with open(os.path.join(PROCESSED_DIR, "works.csv"), "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            works_map[r["paper_id"]] = {
                "paper_id": r["paper_id"],
                "title": r["title"],
                "publication_year": int(r["publication_year"]) if r["publication_year"].isdigit() else None,
                "venue_id": r["venue_id"],
                "citation_count": int(r["citation_count"]) if r["citation_count"].isdigit() else 0
            }

    with open(os.path.join(PROCESSED_DIR, "institutions.csv"), "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            institutions_map[r["institution_id"]] = {
                "institution_id": r["institution_id"],
                "name": r["name"],
                "country_code": r["country_code"],
                "ror": r["ror"]
            }

    with open(os.path.join(PROCESSED_DIR, "venues.csv"), "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            venues_map[r["venue_id"]] = {"name": r["name"]}

    with open(os.path.join(PROCESSED_DIR, "topics.csv"), "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            topics_map[r["topic_id"]] = {"name": r["name"], "subfield": r.get("subfield", "")}

    # 2. Load edges
    with open(os.path.join(PROCESSED_DIR, "authorships.csv"), "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            author_papers[r["author_id"]].append(r["paper_id"])
            paper_authors[r["paper_id"]].append(r["author_id"])

    with open(os.path.join(PROCESSED_DIR, "affiliations.csv"), "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            author_institutions[r["author_id"]].add(r["institution_id"])

    with open(os.path.join(PROCESSED_DIR, "work_topics.csv"), "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            paper_topics[r["paper_id"]].append(r["topic_id"])

    # 3. Build co-authorship adjacency
    with open(os.path.join(PROCESSED_DIR, "coauthorship_edges.csv"), "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            u, v = r["author_id_1"], r["author_id_2"]
            w = float(r["weight"])
            cnt = int(r["papers_count"])
            coauthors[u][v] = {"weight": w, "papers_count": cnt}
            coauthors[v][u] = {"weight": w, "papers_count": cnt}

    # 4. Build topic vectors and norms
    for aid, pids in author_papers.items():
        for pid in pids:
            for tid in paper_topics[pid]:
                author_topic_counter[aid][tid] += 1
        sq_sum = sum(c * c for c in author_topic_counter[aid].values())
        author_topic_norms[aid] = math.sqrt(sq_sum) if sq_sum > 0 else 1.0

    # 5. Load community and graph results
    results_path = os.path.join(PROCESSED_DIR, "project_ii_results.json")
    if os.path.exists(results_path):
        with open(results_path, "r", encoding="utf-8") as f:
            p2 = json.load(f)
            global_stats = p2.get("network_topology", {})
            communities_summary = p2.get("top_communities", [])
    
    print(f"[Dashboard] Initialized with {len(authors_map):,} authors, {len(works_map):,} works, {len(coauthors):,} connected nodes.")

load_data()

# -----------------------------------------------------------------------------
# Recommendation & Similarity Helpers
# -----------------------------------------------------------------------------
def compute_topic_cosine(u: str, v: str) -> float:
    tc_u = author_topic_counter.get(u)
    tc_v = author_topic_counter.get(v)
    if not tc_u or not tc_v:
        return 0.0
    if len(tc_u) > len(tc_v):
        tc_u, tc_v = tc_v, tc_u
    dot = sum(cnt * tc_v.get(tid, 0) for tid, cnt in tc_u.items())
    return dot / (author_topic_norms[u] * author_topic_norms[v])

def recommend_collaborators(query_author_id: str, top_k: int = 5):
    if query_author_id not in authors_map:
        raise HTTPException(status_code=404, detail="Author not found")

    existing_coauthors = set(coauthors.get(query_author_id, {}).keys())
    forbidden = existing_coauthors.union({query_author_id})

    candidate_scores = {}
    q_nbrs = coauthors.get(query_author_id, {})

    for nbr, nbr_meta in q_nbrs.items():
        nbr_nbrs = coauthors.get(nbr, {})
        deg_nbr = len(nbr_nbrs)
        inv_log_deg = 1.0 / math.log(max(deg_nbr, 2))
        for cand, cand_meta in nbr_nbrs.items():
            if cand in forbidden:
                continue
            if cand not in candidate_scores:
                candidate_scores[cand] = {
                    "adamic_adar": 0.0,
                    "common_nbrs": set(),
                    "topic_sim": 0.0
                }
            candidate_scores[cand]["adamic_adar"] += inv_log_deg
            candidate_scores[cand]["common_nbrs"].add(nbr)

    q_topics = set(author_topic_counter.get(query_author_id, {}).keys())
    if len(candidate_scores) < 20 and q_topics:
        top_tids = [t for t, _ in author_topic_counter[query_author_id].most_common(2)]
        for other_aid, other_t in author_topic_counter.items():
            if other_aid in forbidden or other_aid in candidate_scores:
                continue
            if any(t in other_t for t in top_tids):
                candidate_scores[other_aid] = {
                    "adamic_adar": 0.0,
                    "common_nbrs": set(),
                    "topic_sim": 0.0
                }
            if len(candidate_scores) >= 50:
                break

    if not candidate_scores:
        return []

    max_aa = max((c["adamic_adar"] for c in candidate_scores.values()), default=1.0)
    if max_aa == 0:
        max_aa = 1.0

    scored_list = []
    for cand, meta in candidate_scores.items():
        meta["topic_sim"] = compute_topic_cosine(query_author_id, cand)
        norm_aa = meta["adamic_adar"] / max_aa
        hybrid_score = 0.40 * norm_aa + 0.60 * meta["topic_sim"]

        shared_tids = list(q_topics.intersection(set(author_topic_counter.get(cand, {}).keys())))
        shared_topic_names = [topics_map.get(t, {}).get("name", t) for t in shared_tids[:3]]
        common_nbr_names = [authors_map.get(a, {}).get("name", a) for a in list(meta["common_nbrs"])[:3]]

        if meta["common_nbrs"] and shared_topic_names:
            rationale = f"Shares {len(meta['common_nbrs'])} mutual co-author(s) and strong alignment in {shared_topic_names[0]}."
        elif meta["common_nbrs"]:
            rationale = f"Connected via mutual collaborator(s): {', '.join(common_nbr_names)}."
        elif shared_topic_names:
            rationale = f"Topical affinity in {', '.join(shared_topic_names)} across disparate research groups."
        else:
            rationale = "Prospective alignment based on research network trajectory."

        cand_info = authors_map.get(cand, {})
        cand_inst_ids = author_institutions.get(cand, set())
        inst_name = institutions_map.get(list(cand_inst_ids)[0], {}).get("name", "Independent / Unaffiliated") if cand_inst_ids else "Independent / Unaffiliated"

        scored_list.append({
            "author_id": cand,
            "name": cand_info.get("name", cand),
            "institution": inst_name,
            "hybrid_score": round(hybrid_score, 4),
            "topic_similarity": round(meta["topic_sim"], 4),
            "adamic_adar_score": round(meta["adamic_adar"], 4),
            "common_collaborators_count": len(meta["common_nbrs"]),
            "common_collaborators": common_nbr_names,
            "shared_topics": shared_topic_names,
            "recommendation_rationale": rationale
        })

    scored_list.sort(key=lambda x: x["hybrid_score"], reverse=True)
    return scored_list[:top_k]

# -----------------------------------------------------------------------------
# REST API Endpoints
# -----------------------------------------------------------------------------
@app.get("/api/stats")
def get_stats():
    total_cits = sum(w.get("citation_count", 0) for w in works_map.values())
    return {
        "status": "operational",
        "dataset_name": "OpenAlex AI/ML 2016-2025 Corpus (Impact-Stratified)",
        "total_works": len(works_map),
        "total_authors": len(authors_map),
        "total_institutions": len(institutions_map),
        "total_venues": len(venues_map),
        "total_topics": len(topics_map),
        "total_citations": total_cits,
        "active_coauthorship_nodes": len(coauthors),
        "network_topology": global_stats
    }

@app.get("/api/search")
def search_authors(q: str = Query(..., min_length=2)):
    q_lower = q.lower().strip()
    matches = []
    for aid, a in authors_map.items():
        name_lower = a["name"].lower()
        if q_lower in name_lower:
            inst_ids = author_institutions.get(aid, set())
            inst_name = institutions_map.get(list(inst_ids)[0], {}).get("name", "Independent / Unaffiliated") if inst_ids else "Independent / Unaffiliated"
            p_count = len(author_papers.get(aid, []))
            exact = 1 if name_lower == q_lower else 0
            prefix = 1 if name_lower.startswith(q_lower) else 0
            word_prefix = 1 if any(w.startswith(q_lower) for w in name_lower.split()) else 0
            matches.append({
                "author_id": aid,
                "name": a["name"],
                "paper_count": p_count,
                "institution": inst_name,
                "_rank": (exact, prefix, word_prefix, p_count)
            })
    matches.sort(key=lambda x: x["_rank"], reverse=True)
    results = [{k: v for k, v in m.items() if k != "_rank"} for m in matches[:15]]
    return {"query": q, "count": len(results), "results": results}

@app.get("/api/authors/{author_id}")
def get_author_profile(author_id: str):
    if author_id not in authors_map:
        raise HTTPException(status_code=404, detail="Author ID not found")

    a = authors_map[author_id]
    inst_ids = author_institutions.get(author_id, set())
    inst_names = [institutions_map.get(i, {}).get("name", i) for i in inst_ids]

    pids = author_papers.get(author_id, [])
    paper_list = []
    total_citations = 0
    for pid in pids:
        w = works_map.get(pid, {})
        cits = w.get("citation_count", 0)
        total_citations += cits
        v_name = venues_map.get(w.get("venue_id"), {}).get("name", "Academic Venue")
        paper_list.append({
            "paper_id": pid,
            "title": w.get("title", "Untitled Work"),
            "year": w.get("publication_year"),
            "venue": v_name,
            "citations": cits
        })
    paper_list.sort(key=lambda x: (x["year"] or 0, x["citations"]), reverse=True)

    t_counts = author_topic_counter.get(author_id, Counter())
    top_topics = [{"topic_id": tid, "name": topics_map.get(tid, {}).get("name", tid), "count": cnt}
                  for tid, cnt in t_counts.most_common(6)]

    q_nbrs = coauthors.get(author_id, {})
    coauthor_list = []
    for nbr, meta in q_nbrs.items():
        nbr_info = authors_map.get(nbr, {})
        nbr_inst_ids = author_institutions.get(nbr, set())
        nbr_inst_name = institutions_map.get(list(nbr_inst_ids)[0], {}).get("name", "Independent / Unaffiliated") if nbr_inst_ids else "Independent / Unaffiliated"
        coauthor_list.append({
            "author_id": nbr,
            "name": nbr_info.get("name", nbr),
            "institution": nbr_inst_name,
            "weight": round(meta["weight"], 3),
            "papers_count": meta["papers_count"]
        })
    coauthor_list.sort(key=lambda x: x["weight"], reverse=True)

    return {
        "author_id": author_id,
        "name": a["name"],
        "orcid": a.get("orcid", ""),
        "paper_count": len(pids),
        "total_citations": total_citations,
        "institutions": inst_names if inst_names else ["Independent / Unaffiliated"],
        "topics": top_topics,
        "collaborator_count": len(coauthor_list),
        "collaborators": coauthor_list[:25],
        "papers": paper_list
    }

@app.get("/api/authors/{author_id}/graph")
def get_author_graph(author_id: str):
    if author_id not in authors_map:
        raise HTTPException(status_code=404, detail="Author ID not found")

    q_info = authors_map[author_id]
    q_inst = list(author_institutions.get(author_id, set()))
    q_inst_name = institutions_map.get(q_inst[0], {}).get("name", "Independent / Unaffiliated") if q_inst else "Independent / Unaffiliated"

    nodes = [{
        "id": author_id,
        "label": q_info["name"],
        "group": "query",
        "institution": q_inst_name,
        "paper_count": len(author_papers.get(author_id, [])),
        "val": 24
    }]
    node_ids = {author_id}
    links = []

    q_nbrs = coauthors.get(author_id, {})
    sorted_nbrs = sorted(q_nbrs.items(), key=lambda x: x[1]["weight"], reverse=True)[:20]

    for nbr_id, meta in sorted_nbrs:
        nbr_info = authors_map.get(nbr_id, {})
        nbr_inst = list(author_institutions.get(nbr_id, set()))
        nbr_inst_name = institutions_map.get(nbr_inst[0], {}).get("name", "Independent / Unaffiliated") if nbr_inst else "Independent / Unaffiliated"
        w = meta["weight"]
        nodes.append({
            "id": nbr_id,
            "label": nbr_info.get("name", nbr_id),
            "group": "coauthor",
            "institution": nbr_inst_name,
            "weight": round(w, 3),
            "papers_count": meta["papers_count"],
            "val": max(10, min(20, int(9 + w * 2.2)))
        })
        node_ids.add(nbr_id)
        links.append({
            "source": author_id,
            "target": nbr_id,
            "weight": round(w, 3),
            "papers_count": meta["papers_count"],
            "type": "coauthor"
        })

    coauthor_set = set(node_ids) - {author_id}
    for u in coauthor_set:
        u_nbrs = coauthors.get(u, {})
        for v in coauthor_set:
            if u < v and v in u_nbrs:
                w_uv = u_nbrs[v]["weight"]
                links.append({
                    "source": u,
                    "target": v,
                    "weight": round(w_uv, 3),
                    "papers_count": u_nbrs[v]["papers_count"],
                    "type": "inter_coauthor"
                })

    recs = recommend_collaborators(author_id, top_k=5)
    for r in recs:
        r_id = r["author_id"]
        if r_id not in node_ids:
            nodes.append({
                "id": r_id,
                "label": r["name"],
                "group": "recommended",
                "institution": r["institution"],
                "hybrid_score": r["hybrid_score"],
                "topic_similarity": r["topic_similarity"],
                "adamic_adar_score": r["adamic_adar_score"],
                "rationale": r["recommendation_rationale"],
                "val": 16
            })
            node_ids.add(r_id)

        links.append({
            "source": author_id,
            "target": r_id,
            "score": r["hybrid_score"],
            "type": "recommended"
        })

    return {
        "query_author_id": author_id,
        "nodes": nodes,
        "links": links
    }

@app.get("/api/authors/{author_id}/recommendations")
def get_author_recommendations(author_id: str, k: int = 5):
    return {
        "query_author_id": author_id,
        "query_author_name": authors_map.get(author_id, {}).get("name", author_id),
        "recommendations": recommend_collaborators(author_id, top_k=k)
    }

@app.get("/api/communities")
def get_communities():
    return {
        "count": len(communities_summary),
        "communities": communities_summary
    }

@app.get("/api/figures/{figure_name}")
def get_figure(figure_name: str):
    safe_name = os.path.basename(figure_name)
    fig_path = os.path.join(FIGURES_DIR, safe_name)
    if not os.path.exists(fig_path):
        raise HTTPException(status_code=404, detail="Figure not found")
    return FileResponse(fig_path)

# -----------------------------------------------------------------------------
# Clean, Professional Scientific Single-Page Application (HTML/SVG Engine)
# Responsive Layout, Auto-Fitted SVG Graph, Clean Navy/White Palette, Blue Action Buttons
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Clean, Professional Scientific Single-Page Application (HTML/SVG Engine)
# Responsive Layout, Auto-Fitted SVG Graph, Bright / Dark Mode Theme System
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Clean, Professional Scientific Single-Page Application (HTML/SVG Engine)
# Responsive Layout, Auto-Fitted SVG Graph, Bright / Dark Mode Theme System
# -----------------------------------------------------------------------------
HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ScholarlyKG — Research Collaboration Analytics</title>
  <style>
    /* Theme Variables: Light Mode (Default) */
    :root, [data-theme="light"] {
      --bg-body: #f8fafc;
      --bg-surface: #ffffff;
      --bg-subtle: #f1f5f9;
      --bg-accent-light: #eff6ff;
      --border-subtle: #e2e8f0;
      --border-accent: #cbd5e1;
      --border-focus: #2563eb;
      --color-primary: #2563eb;
      --color-primary-hover: #1d4ed8;
      --color-primary-active: #1e40af;
      --color-orange: #ea580c;
      --color-orange-light: #fff7ed;
      --color-orange-border: #fed7aa;
      --color-teal: #059669;
      --color-teal-light: #ecfdf5;
      --color-navy: #0f172a;
      --color-slate: #334155;
      --color-muted: #64748b;
      --canvas-bg: #ffffff;
      --grid-dot: #e2e8f0;
      --node-label-stroke: #ffffff;
      --edge-coauthor: #475569;
      --edge-inter: #cbd5e1;
      --edge-rec: #ea580c;
      --card-glass-bg: rgba(255, 255, 255, 0.94);
      --card-glass-border: var(--border-subtle);
      --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.05);
      --shadow-md: 0 4px 6px -1px rgba(15, 23, 42, 0.08), 0 2px 4px -2px rgba(15, 23, 42, 0.05);
      --shadow-lg: 0 10px 15px -3px rgba(15, 23, 42, 0.1), 0 4px 6px -4px rgba(15, 23, 42, 0.05);
      --theme-toggle-bg: #f1f5f9;
      --theme-toggle-border: #cbd5e1;
    }

    /* Theme Variables: Dark Mode */
    [data-theme="dark"] {
      --bg-body: #090d16;
      --bg-surface: #111827;
      --bg-subtle: #1e293b;
      --bg-accent-light: rgba(59, 130, 246, 0.14);
      --border-subtle: #1f293d;
      --border-accent: #334155;
      --border-focus: #3b82f6;
      --color-primary: #3b82f6;
      --color-primary-hover: #60a5fa;
      --color-primary-active: #2563eb;
      --color-orange: #f97316;
      --color-orange-light: rgba(249, 115, 22, 0.14);
      --color-orange-border: rgba(249, 115, 22, 0.35);
      --color-teal: #10b981;
      --color-teal-light: rgba(16, 185, 129, 0.14);
      --color-navy: #f8fafc;
      --color-slate: #cbd5e1;
      --color-muted: #94a3b8;
      --canvas-bg: #090d16;
      --grid-dot: #1e293b;
      --node-label-stroke: #090d16;
      --edge-coauthor: #64748b;
      --edge-inter: #334155;
      --edge-rec: #f97316;
      --card-glass-bg: rgba(17, 24, 39, 0.92);
      --card-glass-border: rgba(51, 65, 85, 0.65);
      --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.4);
      --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
      --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.6);
      --theme-toggle-bg: #1e293b;
      --theme-toggle-border: #334155;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }

    body {
      background-color: var(--bg-body);
      color: var(--color-navy);
      height: 100vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      -webkit-font-smoothing: antialiased;
      transition: background-color 0.25s ease, color 0.25s ease;
    }

    /* Custom Sleek Scrollbars */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--border-accent); border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--color-muted); }

    /* Button System */
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      font-size: 13px;
      font-weight: 600;
      padding: 7px 14px;
      border-radius: 6px;
      border: none;
      cursor: pointer;
      transition: all 0.15s ease;
      white-space: nowrap;
      text-decoration: none;
    }
    .btn-primary {
      background-color: var(--color-primary);
      color: #ffffff;
      box-shadow: 0 1px 2px rgba(37, 99, 235, 0.25);
    }
    .btn-primary:hover { background-color: var(--color-primary-hover); box-shadow: 0 2px 4px rgba(37, 99, 235, 0.35); }
    .btn-primary:active { background-color: var(--color-primary-active); transform: scale(0.98); }
    .btn-primary:focus-visible { outline: 2px solid var(--color-primary); outline-offset: 2px; }

    .btn-sm { padding: 5px 11px; font-size: 12px; border-radius: 5px; }
    .btn-outline {
      background-color: var(--bg-surface);
      color: var(--color-primary);
      border: 1px solid var(--border-accent);
    }
    .btn-outline:hover { background-color: var(--bg-accent-light); border-color: var(--color-primary); }

    /* Theme Toggle Button */
    .theme-toggle-btn {
      background: var(--theme-toggle-bg);
      border: 1px solid var(--theme-toggle-border);
      color: var(--color-navy);
      padding: 6px 12px;
      border-radius: 20px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    .theme-toggle-btn:hover {
      background: var(--bg-accent-light);
      border-color: var(--color-primary);
      color: var(--color-primary);
    }
    .theme-icon { font-size: 13px; line-height: 1; }

    /* Header Bar */
    header {
      background: var(--bg-surface);
      border-bottom: 1px solid var(--border-subtle);
      height: 56px;
      padding: 0 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      flex-shrink: 0;
      z-index: 30;
      box-shadow: var(--shadow-sm);
      transition: background-color 0.25s ease, border-color 0.25s ease;
    }
    .header-left { display: flex; align-items: center; gap: 12px; min-width: 260px; }
    .brand-mark {
      width: 32px;
      height: 32px;
      background: var(--color-primary);
      color: #ffffff;
      font-weight: 800;
      font-size: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 7px;
      box-shadow: 0 2px 4px rgba(37, 99, 235, 0.3);
    }
    .brand-titles { display: flex; flex-direction: column; }
    .brand-title { font-size: 15px; font-weight: 700; color: var(--color-navy); letter-spacing: -0.3px; line-height: 1.2; }
    .brand-subtitle { font-size: 11px; color: var(--color-muted); font-weight: 500; }

    /* Search Component */
    .header-search { position: relative; width: 420px; max-width: 100%; display: flex; align-items: center; gap: 6px; }
    .search-input-wrap { position: relative; flex: 1; display: flex; align-items: center; }
    .search-input {
      width: 100%;
      background: var(--bg-subtle);
      border: 1px solid var(--border-subtle);
      border-radius: 6px;
      padding: 7px 32px 7px 32px;
      font-size: 13px;
      color: var(--color-navy);
      outline: none;
      transition: all 0.15s ease;
    }
    .search-input:focus { background: var(--bg-surface); border-color: var(--border-focus); box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15); }
    .search-icon { position: absolute; left: 10px; width: 14px; height: 14px; fill: var(--color-muted); pointer-events: none; }
    .search-clear {
      position: absolute;
      right: 28px;
      cursor: pointer;
      font-size: 14px;
      color: var(--color-muted);
      display: none;
      line-height: 1;
      padding: 2px 4px;
    }
    .search-clear:hover { color: var(--color-navy); }
    .search-spinner { position: absolute; right: 10px; width: 14px; height: 14px; border: 2px solid var(--border-accent); border-top-color: var(--color-primary); border-radius: 50%; animation: spin 0.6s linear infinite; display: none; }
    @keyframes spin { to { transform: rotate(360deg); } }

    .search-kbd {
      position: absolute;
      right: 8px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 10px;
      color: var(--color-muted);
      background: var(--border-subtle);
      padding: 1px 5px;
      border-radius: 3px;
      pointer-events: none;
    }

    .search-results {
      position: absolute;
      top: 42px;
      left: 0;
      right: 76px;
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 7px;
      max-height: 340px;
      overflow-y: auto;
      z-index: 50;
      box-shadow: var(--shadow-lg);
      display: none;
    }
    .search-item {
      padding: 9px 12px;
      border-bottom: 1px solid var(--border-subtle);
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
      transition: background 0.1s;
    }
    .search-item:hover, .search-item.active-item { background: var(--bg-accent-light); outline: none; }
    .search-item:last-child { border-bottom: none; }
    .search-item-title { font-size: 13px; font-weight: 600; color: var(--color-navy); }
    .search-item-inst { font-size: 11px; color: var(--color-muted); margin-top: 2px; }
    .match-highlight { color: var(--color-primary); font-weight: 700; text-decoration: underline; }

    /* Header Controls and Telemetry */
    .header-right { display: flex; align-items: center; gap: 14px; }
    .header-telemetry { display: flex; align-items: center; gap: 14px; font-size: 12px; color: var(--color-muted); font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }
    .telemetry-item strong { color: var(--color-navy); font-weight: 700; }

    /* Workbench Main Split Layout */
    .workbench {
      display: flex;
      flex: 1;
      height: calc(100vh - 56px);
      overflow: hidden;
      background: var(--bg-body);
    }

    /* Graph Canvas Area (62% wide) */
    .graph-pane {
      flex: 62;
      position: relative;
      background: var(--canvas-bg);
      border-right: 1px solid var(--border-subtle);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      min-width: 0;
      min-height: 480px;
      height: 100%;
      transition: background-color 0.25s ease;
    }

    .graph-toolbar {
      position: absolute;
      top: 12px;
      left: 14px;
      z-index: 10;
      display: flex;
      align-items: center;
      gap: 6px;
      background: var(--card-glass-bg);
      backdrop-filter: blur(8px);
      padding: 6px 10px;
      border: 1px solid var(--card-glass-border);
      border-radius: 7px;
      box-shadow: var(--shadow-sm);
      transition: all 0.25s ease;
    }
    .graph-title { font-size: 13px; font-weight: 700; color: var(--color-navy); margin-right: 6px; }

    .graph-legend {
      position: absolute;
      bottom: 14px;
      left: 14px;
      z-index: 10;
      background: var(--card-glass-bg);
      backdrop-filter: blur(8px);
      padding: 8px 12px;
      border: 1px solid var(--card-glass-border);
      border-radius: 7px;
      font-size: 11px;
      display: flex;
      flex-direction: column;
      gap: 5px;
      box-shadow: var(--shadow-sm);
      color: var(--color-slate);
      transition: all 0.25s ease;
    }
    .legend-row { display: flex; align-items: center; gap: 8px; }
    .legend-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
    .legend-line { width: 14px; height: 2px; flex-shrink: 0; }

    #networkSvg {
      width: 100%;
      height: 100%;
      min-height: 480px;
      flex: 1;
      display: block;
      cursor: grab;
      background: var(--canvas-bg);
      touch-action: none;
      transition: background-color 0.25s ease;
    }
    #networkSvg:active { cursor: grabbing; }

    /* SVG Graph Elements Styling */
    .node-element {
      transition: opacity 0.25s cubic-bezier(0.16, 1, 0.3, 1), transform 0.05s linear;
      cursor: pointer;
    }
    .node-element:hover circle {
      stroke-width: 4px;
      filter: drop-shadow(0 3px 6px rgba(0, 0, 0, 0.25));
    }
    .node-label {
      font-size: 11px;
      font-weight: 600;
      fill: var(--color-navy);
      text-anchor: middle;
      pointer-events: none;
      user-select: none;
      paint-order: stroke;
      stroke: var(--node-label-stroke);
      stroke-width: 3.5px;
      stroke-linecap: round;
      stroke-linejoin: round;
      transition: fill 0.25s ease, stroke 0.25s ease;
    }
    .node-label-query {
      font-weight: 800;
      font-size: 12px;
      fill: var(--color-primary);
      stroke-width: 4px;
    }

    /* Ego-Focus Highlighting */
    .node-dimmed { opacity: 0.15 !important; }
    .link-dimmed { opacity: 0.08 !important; }
    .node-highlight circle { stroke: var(--color-primary) !important; stroke-width: 4.5px !important; }
    .link-highlight { stroke: var(--color-primary) !important; stroke-width: 3.5px !important; opacity: 1 !important; }

    .link-element {
      transition: opacity 0.25s cubic-bezier(0.16, 1, 0.3, 1), stroke-width 0.2s ease, stroke 0.2s ease;
      cursor: pointer;
    }
    .link-element:hover { stroke-width: 4px !important; stroke: var(--color-primary) !important; }

    /* Interactive Graph Tooltip */
    #svgTooltip {
      position: fixed;
      display: none;
      background: rgba(15, 23, 42, 0.95);
      color: #ffffff;
      backdrop-filter: blur(8px);
      border-radius: 6px;
      padding: 9px 12px;
      font-size: 12px;
      line-height: 1.4;
      pointer-events: none;
      z-index: 100;
      box-shadow: var(--shadow-lg);
      max-width: 290px;
      border: 1px solid rgba(255, 255, 255, 0.15);
      transition: opacity 0.15s ease;
    }

    /* Right Sidebar Area (38% wide) */
    .sidebar-pane {
      flex: 38;
      display: flex;
      flex-direction: column;
      background: var(--bg-surface);
      border-left: 1px solid var(--border-subtle);
      overflow: hidden;
      min-width: 340px;
      transition: background-color 0.25s ease, border-color 0.25s ease;
    }

    .sidebar-tabs {
      display: flex;
      border-bottom: 1px solid var(--border-subtle);
      background: var(--bg-subtle);
      padding: 0 12px;
      gap: 4px;
      flex-shrink: 0;
      transition: background-color 0.25s ease;
    }
    .tab-item {
      padding: 10px 14px;
      font-size: 12px;
      font-weight: 600;
      color: var(--color-muted);
      border: none;
      background: transparent;
      cursor: pointer;
      border-bottom: 2px solid transparent;
      transition: all 0.15s ease;
      white-space: nowrap;
    }
    .tab-item:hover { color: var(--color-navy); }
    .tab-item.active { color: var(--color-primary); border-bottom-color: var(--color-primary); background: var(--bg-surface); }

    .sidebar-content {
      flex: 1;
      overflow-y: auto;
      padding: 18px;
    }

    /* Researcher Dossier View */
    .dossier-header { margin-bottom: 16px; }
    .dossier-name { font-size: 19px; font-weight: 800; color: var(--color-navy); letter-spacing: -0.4px; }
    .dossier-affiliation { font-size: 12px; color: var(--color-muted); margin-top: 4px; line-height: 1.4; }

    /* KPI Row */
    .kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin: 14px 0; }
    .kpi-box {
      background: var(--bg-subtle);
      border: 1px solid var(--border-subtle);
      border-radius: 6px;
      padding: 8px 10px;
      text-align: center;
      transition: all 0.25s ease;
    }
    .kpi-value { font-size: 17px; font-weight: 800; color: var(--color-primary); font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }
    .kpi-label { font-size: 10px; font-weight: 600; text-transform: uppercase; color: var(--color-muted); margin-top: 2px; }

    .section-heading { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: var(--color-muted); margin: 16px 0 8px 0; }

    .topic-pills { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 16px; }
    .topic-pill {
      font-size: 11px;
      font-weight: 500;
      color: var(--color-primary);
      background: var(--bg-accent-light);
      border: 1px solid rgba(37, 99, 235, 0.2);
      padding: 3px 8px;
      border-radius: 4px;
    }

    /* Structured Data Tables */
    .data-table { width: 100%; border-collapse: collapse; font-size: 12px; text-align: left; }
    .data-table th {
      padding: 8px 10px;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.4px;
      color: var(--color-muted);
      border-bottom: 1px solid var(--border-subtle);
      background: var(--bg-subtle);
    }
    .data-table td { padding: 9px 10px; border-bottom: 1px solid var(--border-subtle); color: var(--color-slate); }
    .data-table tr:hover td { background: var(--bg-accent-light); }

    /* Recommendation Cards */
    .rec-list { display: flex; flex-direction: column; gap: 10px; }
    .rec-card {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-left: 4px solid var(--color-orange);
      border-radius: 6px;
      padding: 12px;
      transition: all 0.15s ease;
    }
    .rec-card:hover { border-color: var(--color-orange-border); box-shadow: var(--shadow-md); transform: translateY(-1px); }
    .rec-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 4px; }
    .rec-title-group { display: flex; align-items: center; gap: 7px; }
    .rec-rank {
      font-size: 11px;
      font-weight: 800;
      color: var(--color-orange);
      background: var(--color-orange-light);
      border: 1px solid var(--color-orange-border);
      padding: 2px 6px;
      border-radius: 4px;
    }
    .rec-author-name { font-size: 14px; font-weight: 700; color: var(--color-navy); cursor: pointer; }
    .rec-author-name:hover { color: var(--color-primary); text-decoration: underline; }
    .rec-score-pill {
      font-size: 11px;
      font-weight: 700;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      color: #ffffff;
      background: var(--color-orange);
      padding: 3px 8px;
      border-radius: 12px;
    }
    .rec-affiliation { font-size: 11px; color: var(--color-muted); margin-bottom: 6px; }
    .rec-callout {
      background: var(--color-orange-light);
      border: 1px solid var(--color-orange-border);
      border-radius: 4px;
      padding: 6px 9px;
      font-size: 11px;
      color: var(--color-orange);
      line-height: 1.35;
      margin: 6px 0;
    }
    .rec-breakdown { display: flex; flex-wrap: wrap; gap: 10px; font-size: 11px; color: var(--color-slate); margin-top: 6px; }
    .rec-breakdown span strong { color: var(--color-navy); }
    .rec-footer { margin-top: 8px; display: flex; justify-content: flex-end; }

    /* Figure Preview Cards */
    .fig-item {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 7px;
      padding: 12px;
      margin-bottom: 14px;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .fig-item:hover { border-color: var(--color-primary); box-shadow: var(--shadow-md); }
    .fig-caption-title { font-size: 13px; font-weight: 700; color: var(--color-navy); margin-bottom: 4px; }
    .fig-caption-desc { font-size: 11px; color: var(--color-muted); line-height: 1.4; margin-bottom: 8px; }
    .fig-preview-img { width: 100%; height: auto; border-radius: 5px; border: 1px solid var(--border-subtle); display: block; }

    /* Lightbox Modal for Figures */
    #figModal {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(15, 23, 42, 0.85);
      backdrop-filter: blur(6px);
      z-index: 200;
      align-items: center;
      justify-content: center;
      padding: 24px;
    }
    .modal-box {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 8px;
      max-width: 900px;
      width: 100%;
      max-height: 90vh;
      overflow-y: auto;
      box-shadow: var(--shadow-lg);
      padding: 20px;
      position: relative;
    }
    .modal-close {
      position: absolute;
      top: 14px;
      right: 16px;
      background: var(--bg-subtle);
      border: 1px solid var(--border-subtle);
      font-size: 18px;
      cursor: pointer;
      width: 32px;
      height: 32px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--color-navy);
      font-weight: 700;
      transition: background 0.1s;
    }
    .modal-close:hover { background: var(--border-subtle); }

    /* Community Cards */
    .comm-card {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 6px;
      padding: 10px 12px;
      margin-bottom: 8px;
    }
    .comm-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
    .comm-title { font-size: 12px; font-weight: 700; color: var(--color-navy); }
    .comm-stats { font-size: 11px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; color: var(--color-muted); }
    .comm-leaders { font-size: 11px; color: var(--color-primary); font-weight: 600; margin-bottom: 3px; }
    .comm-topics { font-size: 11px; color: var(--color-muted); line-height: 1.35; }

    /* Responsive Breakpoints */
    @media (max-width: 1024px) {
      .workbench { flex-direction: column; height: auto; overflow: visible; }
      body { height: auto; overflow: auto; }
      .graph-pane { flex: none; height: 520px; }
      .sidebar-pane { flex: none; height: auto; }
      .header-telemetry { display: none; }
    }
  </style>
</head>
<body>

  <!-- Top Navigation Header -->
  <header>
    <div class="header-left">
      <div class="brand-mark">G</div>
      <div class="brand-titles">
        <span class="brand-title">ScholarlyKG</span>
        <span class="brand-subtitle">Research Collaboration Workbench · OpenAlex Corpus</span>
      </div>
    </div>

    <!-- Search Bar -->
    <div class="header-search">
      <div class="search-input-wrap">
        <svg class="search-icon" viewBox="0 0 20 20">
          <path d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" />
        </svg>
        <input type="text" id="authorSearchInput" class="search-input" placeholder="Search researcher name (e.g. Luke Zettlemoyer)..." autocomplete="off" aria-label="Search researcher">
        <span id="searchClearBtn" class="search-clear" title="Clear search">&times;</span>
        <span class="search-kbd">/</span>
        <div id="searchSpinner" class="search-spinner"></div>
      </div>
      <button class="btn btn-primary btn-sm" onclick="triggerSearch()">Search</button>
      <div id="searchDropdown" class="search-results"></div>
    </div>

    <!-- Header Controls & Telemetry -->
    <div class="header-right">
      <!-- Bright / Dark Mode Toggle Button -->
      <button id="themeToggleBtn" class="theme-toggle-btn" onclick="toggleTheme()" title="Switch between Bright and Dark Mode">
        <span id="themeIcon" class="theme-icon">🌙</span>
        <span id="themeLabel">Dark Mode</span>
      </button>

      <div class="header-telemetry">
        <span class="telemetry-item">Works: <strong>4,989</strong></span>
        <span class="telemetry-item">Authors: <strong>22,185</strong></span>
        <span class="telemetry-item">Edges: <strong>221,903</strong></span>
        <span class="telemetry-item">Giant Component: <strong>67.5%</strong></span>
      </div>
    </div>
  </header>

  <!-- Workbench Main View -->
  <div class="workbench">

    <!-- Left Graph Canvas Area -->
    <div class="graph-pane">
      <div class="graph-toolbar">
        <span class="graph-title" id="networkTitleText">Ego-Network Graph</span>
        <button class="btn btn-primary btn-sm" onclick="zoomIn()" title="Smooth Zoom In (+)">Zoom In (+)</button>
        <button class="btn btn-primary btn-sm" onclick="zoomOut()" title="Smooth Zoom Out (−)">Zoom Out (−)</button>
        <button class="btn btn-primary btn-sm" onclick="autoFitGraph(true)" title="Smooth Fit graph to canvas (F)">Fit to View</button>
        <button class="btn btn-primary btn-sm" onclick="toggleRecommendations(this)" id="toggleRecBtn" title="Toggle prospective recommendations (R)">Toggle Recommendations</button>
        <button class="btn btn-outline btn-sm" onclick="resetLayout()" title="Re-simulate organic layout">Reset</button>
        <span style="font-size: 11px; color: var(--color-muted); font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; margin-left: 6px;" id="networkStatsText">26 Nodes · 73 Edges</span>
      </div>

      <div class="graph-legend">
        <div class="legend-row">
          <div class="legend-dot" style="background:var(--color-primary); border: 2px solid var(--color-primary-hover);"></div>
          <span>Focus Researcher</span>
        </div>
        <div class="legend-row">
          <div class="legend-dot" style="background:var(--color-teal); border: 2px solid #047857;"></div>
          <span>Direct Co-Author (Observed)</span>
        </div>
        <div class="legend-row">
          <div class="legend-dot" style="background:var(--color-orange); border: 2px solid var(--color-orange-border);"></div>
          <span>Prospective Partner (Recommendation)</span>
        </div>
        <div class="legend-row">
          <div class="legend-line" style="background:var(--edge-coauthor);"></div>
          <span>Co-Authorship Edge (Weight)</span>
        </div>
        <div class="legend-row">
          <div class="legend-line" style="border-top: 2px dashed var(--edge-rec); background:none;"></div>
          <span>Predicted Collaboration Link</span>
        </div>
      </div>

      <!-- Interactive SVG Canvas with Spatial Grid Pattern -->
      <svg id="networkSvg" width="100%" height="100%">
        <defs>
          <pattern id="gridPattern" width="40" height="40" patternUnits="userSpaceOnUse">
            <circle cx="20" cy="20" r="1" fill="var(--grid-dot)" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#gridPattern)" pointer-events="none" />
        <g id="viewport">
          <g id="linksLayer"></g>
          <g id="nodesLayer"></g>
        </g>
      </svg>
      <div id="svgTooltip"></div>
    </div>

    <!-- Right Sidebar Area -->
    <div class="sidebar-pane">
      <div class="sidebar-tabs">
        <button class="tab-item active" onclick="switchSidebarTab('dossier', this)">Researcher Dossier</button>
        <button class="tab-item" onclick="switchSidebarTab('recommendations', this)">Prospective Partners</button>
        <button class="tab-item" onclick="switchSidebarTab('figures', this)">Visual Figures &amp; Charts</button>
        <button class="tab-item" onclick="switchSidebarTab('communities', this)">Disciplinary Clusters</button>
      </div>

      <!-- Tab 1: Researcher Dossier -->
      <div class="sidebar-content" id="tabDossier">
        <div id="dossierLoading" style="display: none; padding: 20px; text-align: center; color: var(--color-muted);">Loading researcher profile...</div>
        <div id="dossierDetails">
          <div class="dossier-header">
            <div class="dossier-name" id="profName">Luke Zettlemoyer</div>
            <div class="dossier-affiliation" id="profInst">Meta (Israel), Allen Institute for Artificial Intelligence, Stanford University, Meta (United States), Carnegie Mellon University, University of Hong Kong, Johns Hopkins University, New York University, University of California, Los Angeles, University of Washington, University of Massachusetts Amherst</div>
            <div class="kpi-row">
              <div class="kpi-box">
                <div class="kpi-value" id="profPapers">40</div>
                <div class="kpi-label">Corpus Works</div>
              </div>
              <div class="kpi-box">
                <div class="kpi-value" id="profCollabs">260</div>
                <div class="kpi-label">Collaborators</div>
              </div>
              <div class="kpi-box">
                <div class="kpi-value" id="profCitations">96,575</div>
                <div class="kpi-label">Citations</div>
              </div>
              <div class="kpi-box">
                <div class="kpi-value" id="profOrcid">Verified</div>
                <div class="kpi-label">ORCID Verified</div>
              </div>
            </div>
          </div>

          <div class="section-heading">Core Research Topics</div>
          <div class="topic-pills" id="profTopics">
            <span class="topic-pill">Topic Modeling (39)</span>
            <span class="topic-pill">Natural Language Processing Techniques (36)</span>
            <span class="topic-pill">Multimodal Machine Learning Applications (11)</span>
            <span class="topic-pill">Domain Adaptation and Few-Shot Learning (11)</span>
            <span class="topic-pill">Information Retrieval and Search Behavior (4)</span>
            <span class="topic-pill">Sentiment Analysis and Opinion Mining (4)</span>
          </div>

          <div class="section-heading">Direct Co-Authors (Collaboration Intensity)</div>
          <table class="data-table">
            <thead>
              <tr>
                <th>Co-Author</th>
                <th>Newman Weight</th>
                <th>Joint Works</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody id="coauthorTableBody">
              <tr><td><strong>Mike Lewis</strong><div style="font-size:11px; color:var(--color-muted);">Meta (United States)</div></td><td><strong>1.55</strong></td><td>7</td><td><button class="btn btn-primary btn-sm" onclick="loadAuthor('A5004412943')">Pivot Graph</button></td></tr>
              <tr><td><strong>Kenton Lee</strong><div style="font-size:11px; color:var(--color-muted);">Google (United States)</div></td><td><strong>1.33</strong></td><td>4</td><td><button class="btn btn-primary btn-sm" onclick="loadAuthor('A5081862885')">Pivot Graph</button></td></tr>
              <tr><td><strong>Sewon Min</strong><div style="font-size:11px; color:var(--color-muted);">Meta (United States)</div></td><td><strong>1.27</strong></td><td>6</td><td><button class="btn btn-primary btn-sm" onclick="loadAuthor('A5039158419')">Pivot Graph</button></td></tr>
              <tr><td><strong>Luheng He</strong><div style="font-size:11px; color:var(--color-muted);">Google (United States)</div></td><td><strong>1.17</strong></td><td>3</td><td><button class="btn btn-primary btn-sm" onclick="loadAuthor('A5025887224')">Pivot Graph</button></td></tr>
              <tr><td><strong>Hannaneh Hajishirzi</strong><div style="font-size:11px; color:var(--color-muted);">Yale University</div></td><td><strong>1.12</strong></td><td>7</td><td><button class="btn btn-primary btn-sm" onclick="loadAuthor('A5082305994')">Pivot Graph</button></td></tr>
              <tr><td><strong>Omer Levy</strong><div style="font-size:11px; color:var(--color-muted);">Meta (Israel)</div></td><td><strong>1.09</strong></td><td>5</td><td><button class="btn btn-primary btn-sm" onclick="loadAuthor('A5024311574')">Pivot Graph</button></td></tr>
            </tbody>
          </table>

          <div class="section-heading">Recent Publications in Corpus</div>
          <table class="data-table">
            <thead>
              <tr>
                <th>Year</th>
                <th>Citations</th>
                <th>Title &amp; Venue</th>
              </tr>
            </thead>
            <tbody id="papersTableBody">
              <tr><td><span style="font-family:ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-weight:600; color:var(--color-muted);">2025</span></td><td><strong style="color:var(--color-primary); font-family:ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;">1,973</strong></td><td><strong>s1: Simple test-time scaling</strong><div style="font-size:11px; color:var(--color-muted);">Conference on Empirical Methods in Natural Language Processing (EMNLP)</div></td></tr>
              <tr><td><span style="font-family:ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-weight:600; color:var(--color-muted);">2025</span></td><td><strong style="color:var(--color-primary); font-family:ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;">259</strong></td><td><strong>MUSE: Machine Unlearning Six-Way Evaluation for Language Models</strong><div style="font-size:11px; color:var(--color-muted);">International Conference on Learning Representations</div></td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Tab 2: Prospective Partners -->
      <div class="sidebar-content" id="tabRecommendations" style="display: none;">
        <div style="background: var(--bg-subtle); border: 1px solid var(--border-subtle); border-radius: 6px; padding: 10px 12px; margin-bottom: 14px; font-size: 12px; color: var(--color-slate); line-height: 1.4;">
          Ranked by hybrid link score: <strong>40% collaboration network signal &middot; 60% research topic similarity</strong>, strictly evaluated on non-connected candidate researchers.
        </div>
        <div id="recsContainer" class="rec-list"></div>
      </div>

      <!-- Tab 3: Visual Figures & Charts -->
      <div class="sidebar-content" id="tabFigures" style="display: none;">
        <div class="section-heading" style="margin-top: 0;">Empirical Publication Figures (Network Analysis &amp; Trends)</div>

        <div class="fig-item" onclick="openFigureModal('/api/figures/fig1_degree_distribution.png', 'Figure 1: Co-Authorship Degree Distribution', 'Linear and log-log scale-free distributions demonstrating heavy-tailed collaborative clustering in AI/ML research.')">
          <div class="fig-caption-title">Figure 1: Co-Authorship Degree Distribution</div>
          <div class="fig-caption-desc">Linear and log-log scale-free distributions demonstrating heavy-tailed collaborative clustering in AI/ML research.</div>
          <img class="fig-preview-img" src="/api/figures/fig1_degree_distribution.png" alt="Degree Distribution Figure" loading="lazy">
        </div>

        <div class="fig-item" onclick="openFigureModal('/api/figures/fig2_community_sizes_and_topics.png', 'Figure 2: Community Sizes &amp; Core Topics', 'Louvain modularity Q=0.926 community sizes and predominant NLP/Robotics/Healthcare subfield partitions.')">
          <div class="fig-caption-title">Figure 2: Community Sizes &amp; Core Topics</div>
          <div class="fig-caption-desc">Louvain modularity Q=0.926 community sizes and predominant NLP/Robotics/Healthcare subfield partitions.</div>
          <img class="fig-preview-img" src="/api/figures/fig2_community_sizes_and_topics.png" alt="Community Sizes Figure" loading="lazy">
        </div>

        <div class="fig-item" onclick="openFigureModal('/api/figures/fig3_temporal_collaboration_trends.png', 'Figure 3: Temporal Collaboration Dynamics', 'Evolution of team sizes, multi-institutional co-authorship proportions, and cross-topic convergence from 2016 to 2025.')">
          <div class="fig-caption-title">Figure 3: Temporal Collaboration Dynamics</div>
          <div class="fig-caption-desc">Evolution of team sizes, multi-institutional co-authorship proportions, and cross-topic convergence from 2016 to 2025.</div>
          <img class="fig-preview-img" src="/api/figures/fig3_temporal_collaboration_trends.png" alt="Temporal Trends Figure" loading="lazy">
        </div>

        <div class="fig-item" onclick="openFigureModal('/api/figures/fig4_top_centrality_researchers.png', 'Figure 4: Top Centrality Researchers', 'Betweenness vs. degree centrality scatter plot identifying structural bridge researchers across disparate disciplines.')">
          <div class="fig-caption-title">Figure 4: Top Centrality Researchers</div>
          <div class="fig-caption-desc">Betweenness vs. degree centrality scatter plot identifying structural bridge researchers across disparate disciplines.</div>
          <img class="fig-preview-img" src="/api/figures/fig4_top_centrality_researchers.png" alt="Centrality Analysis Figure" loading="lazy">
        </div>
      </div>

      <!-- Tab 4: Disciplinary Clusters -->
      <div class="sidebar-content" id="tabCommunities" style="display: none;">
        <div class="section-heading" style="margin-top: 0;">Louvain Disciplinary Clusters (Modularity Q: 0.926)</div>
        <div id="communitiesContainer"></div>
      </div>

    </div>
  </div>

  <!-- Figure Lightbox Modal -->
  <div id="figModal" onclick="closeFigureModal(event)">
    <div class="modal-box" onclick="event.stopPropagation()">
      <button class="modal-close" onclick="closeFigureModal()">&times;</button>
      <div id="modalFigTitle" style="font-size: 16px; font-weight: 700; color: var(--color-navy); margin-bottom: 6px;">Figure Title</div>
      <div id="modalFigDesc" style="font-size: 12px; color: var(--color-muted); margin-bottom: 12px; line-height: 1.4;">Figure Description</div>
      <img id="modalFigImg" src="" alt="Enlarged Publication Figure" style="width: 100%; height: auto; border-radius: 6px; border: 1px solid var(--border-subtle); display: block;">
    </div>
  </div>

  <script>
    // -------------------------------------------------------------------------
    // Pre-Baked Fallback Data (Zero Latency Instant Initial Render)
    // -------------------------------------------------------------------------
    const DEFAULT_DATA = {"profile": {"author_id": "A5067919401", "name": "Luke Zettlemoyer", "orcid": "https://orcid.org/0009-0008-8296-0764", "paper_count": 40, "institutions": ["Stanford University", "Johns Hopkins University", "Meta (Israel)", "Allen Institute for Artificial Intelligence", "University of Hong Kong", "University of Massachusetts Amherst", "University of Washington", "New York University", "Meta (United States)", "University of California, Los Angeles", "Carnegie Mellon University"], "topics": [{"topic_id": "T10028", "name": "Topic Modeling", "count": 39}, {"topic_id": "T10181", "name": "Natural Language Processing Techniques", "count": 36}, {"topic_id": "T11714", "name": "Multimodal Machine Learning Applications", "count": 11}, {"topic_id": "T11307", "name": "Domain Adaptation and Few-Shot Learning", "count": 11}, {"topic_id": "T10286", "name": "Information Retrieval and Search Behavior", "count": 4}, {"topic_id": "T10664", "name": "Sentiment Analysis and Opinion Mining", "count": 4}], "collaborator_count": 260, "collaborators": [{"author_id": "A5004412943", "name": "Mike Lewis", "institution": "New York University", "weight": 1.554, "papers_count": 7}, {"author_id": "A5081862885", "name": "Kenton Lee", "institution": "Google (United States)", "weight": 1.333, "papers_count": 4}, {"author_id": "A5039158419", "name": "Sewon Min", "institution": "Meta (United States)", "weight": 1.268, "papers_count": 6}, {"author_id": "A5025887224", "name": "Luheng He", "institution": "Google (United States)", "weight": 1.167, "papers_count": 3}, {"author_id": "A5082305994", "name": "Hannaneh Hajishirzi", "institution": "Johns Hopkins University", "weight": 1.122, "papers_count": 7}, {"author_id": "A5024311574", "name": "Omer Levy", "institution": "Stanford University", "weight": 1.086, "papers_count": 5}, {"author_id": "A5062471396", "name": "Armen Aghajanyan", "institution": "Meta (United States)", "weight": 0.833, "papers_count": 2}, {"author_id": "A5019081674", "name": "Yinhan Liu", "institution": "Meta (United States)", "weight": 0.819, "papers_count": 4}, {"author_id": "A5035142405", "name": "Eunsol Choi", "institution": "Stanford University", "weight": 0.81, "papers_count": 3}, {"author_id": "A5088517824", "name": "Noah A. Smith", "institution": "Stanford University", "weight": 0.791, "papers_count": 5}, {"author_id": "A5066873932", "name": "Wen-tau Yih", "institution": "Meta (Israel)", "weight": 0.769, "papers_count": 4}, {"author_id": "A5082767919", "name": "Mohit Iyyer", "institution": "Stanford University", "weight": 0.768, "papers_count": 4}, {"author_id": "A5063151917", "name": "Ari Holtzman", "institution": "Stanford University", "weight": 0.754, "papers_count": 4}, {"author_id": "A5101509445", "name": "Matthew E. Peters", "institution": "University of Washington", "weight": 0.654, "papers_count": 4}, {"author_id": "A5011974509", "name": "Marjan Ghazvininejad", "institution": "Meta (United States)", "weight": 0.619, "papers_count": 3}, {"author_id": "A5075834790", "name": "Naman Goyal", "institution": "Meta (United States)", "weight": 0.558, "papers_count": 5}, {"author_id": "A5085011940", "name": "Daniel S. Weld", "institution": "Allen Institute", "weight": 0.533, "papers_count": 2}, {"author_id": "A5082136238", "name": "Gabriel Stanovsky", "institution": "Hebrew University of Jerusalem", "weight": 0.5, "papers_count": 1}, {"author_id": "A5045050802", "name": "Sonal Gupta", "institution": "Meta (United States)", "weight": 0.5, "papers_count": 1}, {"author_id": "A5103238719", "name": "Weijia Shi", "institution": "University of Washington", "weight": 0.486, "papers_count": 3}, {"author_id": "A5087565126", "name": "Minjoon Seo", "institution": "LG AI Research (South Korea)", "weight": 0.476, "papers_count": 2}, {"author_id": "A5025255782", "name": "Percy Liang", "institution": "University of North Carolina at Chapel Hill", "weight": 0.397, "papers_count": 3}, {"author_id": "A5051064208", "name": "Danqi Chen", "institution": "Stanford University", "weight": 0.343, "papers_count": 2}, {"author_id": "A_anon_79c9881763", "name": "Mandar Joshi", "institution": "University of Washington", "weight": 0.333, "papers_count": 1}, {"author_id": "A5002499277", "name": "John Wieting", "institution": "Google (United States)", "weight": 0.333, "papers_count": 1}], "papers": [{"paper_id": "W4416036482", "title": "s1: Simple test-time scaling", "year": 2025, "venue": "Conference on Empirical Methods in Natural Language Processing (EMNLP)", "citations": 1973}, {"paper_id": "W4400572793", "title": "MUSE: Machine Unlearning Six-Way Evaluation for Language Models", "year": 2025, "venue": "International Conference on Learning Representations", "citations": 259}, {"paper_id": "W4401042773", "title": "REPLUG: Retrieval-Augmented Black-Box Language Models", "year": 2024, "venue": "Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (NAACL-HLT)", "citations": 1210}, {"paper_id": "W4402671236", "title": "OLMo: Accelerating the Science of Language Models", "year": 2024, "venue": "Proceedings of the conference - Association for Computational Linguistics. Meeting", "citations": 921}, {"paper_id": "W4402671286", "title": "Dolma: an Open Corpus of Three Trillion Tokens for Language Model Pretraining Research", "year": 2024, "venue": "Proceedings of the conference - Association for Computational Linguistics. Meeting", "citations": 685}, {"paper_id": "W4415798713", "title": "DataComp-LM: In search of the next generation of training sets for language models", "year": 2024, "venue": "neural information processing systems", "citations": 635}, {"paper_id": "W4401042371", "title": "Trusting Your Evidence: Hallucinate Less with Context-aware Decoding", "year": 2024, "venue": "Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (NAACL-HLT)", "citations": 550}, {"paper_id": "W4387985331", "title": "Detecting Pretraining Data from Large Language Models", "year": 2024, "venue": "International Conference on Learning Representations", "citations": 513}, {"paper_id": "W4402667037", "title": "The Belebele Benchmark: a Parallel Reading Comprehension Dataset in 122 Language Variants", "year": 2024, "venue": "Proceedings of the conference - Association for Computational Linguistics. Meeting", "citations": 486}, {"paper_id": "W7133214447", "title": "Toolformer: Language Models Can Teach Themselves to Use Tools", "year": 2023, "venue": "neural information processing systems", "citations": 7861}, {"paper_id": "W7133233472", "title": "QLoRA: Efficient Finetuning of Quantized LLMs", "year": 2023, "venue": "neural information processing systems", "citations": 7544}, {"paper_id": "W4389519598", "title": "FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation", "year": 2023, "venue": "Conference on Empirical Methods in Natural Language Processing (EMNLP)", "citations": 2384}, {"paper_id": "W7133189643", "title": "LIMA: Less Is More for Alignment", "year": 2023, "venue": "neural information processing systems", "citations": 2049}, {"paper_id": "W4385571645", "title": "Contrastive Decoding: Open-ended Text Generation as Optimization", "year": 2023, "venue": "Proceedings of the conference - Association for Computational Linguistics. Meeting", "citations": 879}, {"paper_id": "W4385571045", "title": "Towards Understanding Chain-of-Thought Prompting: An Empirical Study of What Matters", "year": 2023, "venue": "Proceedings of the conference - Association for Computational Linguistics. Meeting", "citations": 489}, {"paper_id": "W4385570594", "title": "One Embedder, Any Task: Instruction-Finetuned Text Embeddings", "year": 2023, "venue": "Findings of the Association for Computational Linguistics: ACL (Findings of ACL)", "citations": 412}, {"paper_id": "W4385567149", "title": "Rethinking the Role of Demonstrations: What Makes In-Context Learning Work?", "year": 2022, "venue": "Conference on Empirical Methods in Natural Language Processing (EMNLP)", "citations": 2440}, {"paper_id": "W4385565879", "title": "Few-shot Learning with Multilingual Generative Language Models", "year": 2022, "venue": "Conference on Empirical Methods in Natural Language Processing (EMNLP)", "citations": 531}, {"paper_id": "W7133262701", "title": "Memorization Without Overfitting: Analyzing the Training Dynamics of Large Language Models", "year": 2022, "venue": "neural information processing systems", "citations": 513}, {"paper_id": "W3210277894", "title": "MetaICL: Learning to Learn In Context", "year": 2022, "venue": "Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (NAACL-HLT)", "citations": 482}, {"paper_id": "W4385572953", "title": "UnifiedSKG: Unifying and Multi-Tasking Structured Knowledge Grounding with Text-to-Text Language Models", "year": 2022, "venue": "Conference on Empirical Methods in Natural Language Processing (EMNLP)", "citations": 449}, {"paper_id": "W3118216348", "title": "Intrinsic Dimensionality Explains the Effectiveness of Language Model Fine-Tuning", "year": 2021, "venue": "Academic Venue", "citations": 1200}, {"paper_id": "W2982399380", "title": "BART: Denoising Sequence-to-Sequence Pre-training for Natural Language Generation, Translation, and Comprehension", "year": 2020, "venue": "Proceedings of the conference - Association for Computational Linguistics. Meeting", "citations": 15130}, {"paper_id": "W2983040767", "title": "Unsupervised Cross-lingual Representation Learning at Scale", "year": 2020, "venue": "Proceedings of the conference - Association for Computational Linguistics. Meeting", "citations": 11144}, {"paper_id": "W3001434439", "title": "Multilingual Denoising Pre-training for Neural Machine Translation", "year": 2020, "venue": "Transactions of the Association for Computational Linguistics", "citations": 2612}, {"paper_id": "W2962753370", "title": "SpanBERT: Improving Pre-training by Representing and Predicting Spans", "year": 2020, "venue": "Transactions of the Association for Computational Linguistics", "citations": 2555}, {"paper_id": "W3104748221", "title": "Scalable Zero-shot Entity Linking with Dense Entity Retrieval", "year": 2020, "venue": "Conference on Empirical Methods in Natural Language Processing (EMNLP)", "citations": 793}, {"paper_id": "W3100292568", "title": "AmbigQA: Answering Ambiguous Open-domain Questions", "year": 2020, "venue": "Conference on Empirical Methods in Natural Language Processing (EMNLP)", "citations": 617}, {"paper_id": "W2937808806", "title": "Mask-Predict: Parallel Decoding of Conditional Masked Language Models", "year": 2019, "venue": "Conference on Empirical Methods in Natural Language Processing (EMNLP)", "citations": 875}, {"paper_id": "W2947599143", "title": "Evaluating Gender Bias in Machine Translation", "year": 2019, "venue": "Proceedings of the conference - Association for Computational Linguistics. Meeting", "citations": 649}, {"paper_id": "W2787560479", "title": "Deep Contextualized Word Representations", "year": 2018, "venue": "Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (NAACL-HLT)", "citations": 15639}, {"paper_id": "W2793978524", "title": "AllenNLP: A Deep Semantic Natural Language Processing Platform", "year": 2018, "venue": "Workshop for NLP Open Source Software (NLP-OSS)", "citations": 1500}, {"paper_id": "W2888302696", "title": "QuAC: Question Answering in Context", "year": 2018, "venue": "Conference on Empirical Methods in Natural Language Processing (EMNLP)", "citations": 965}, {"paper_id": "W2798139452", "title": "Adversarial Example Generation with Syntactically Controlled Paraphrase Networks", "year": 2018, "venue": "Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (NAACL-HLT)", "citations": 883}, {"paper_id": "W2797051334", "title": "Higher-Order Coreference Resolution with Coarse-to-Fine Inference", "year": 2018, "venue": "Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (NAACL-HLT)", "citations": 570}, {"paper_id": "W2888329843", "title": "Dissecting Contextual Word Embeddings: Architecture and Representation", "year": 2018, "venue": "Conference on Empirical Methods in Natural Language Processing (EMNLP)", "citations": 561}, {"paper_id": "W2612431505", "title": "TriviaQA: A Large Scale Distantly Supervised Challenge Dataset for Reading Comprehension", "year": 2017, "venue": "Proceedings of the conference - Association for Computational Linguistics. Meeting", "citations": 4965}, {"paper_id": "W2738152205", "title": "End-to-end Neural Coreference Resolution", "year": 2017, "venue": "Conference on Empirical Methods in Natural Language Processing (EMNLP)", "citations": 1184}, {"paper_id": "W2624677889", "title": "Zero-Shot Relation Extraction via Reading Comprehension", "year": 2017, "venue": "Conference on Computational Natural Language Learning", "citations": 925}, {"paper_id": "W2740765036", "title": "Deep Semantic Role Labeling: What Works and What\u2019s Next", "year": 2017, "venue": "Proceedings of the conference - Association for Computational Linguistics. Meeting", "citations": 543}]}, "graph": {"query_author_id": "A5067919401", "nodes": [{"id": "A5067919401", "label": "Luke Zettlemoyer", "group": "query", "institution": "Stanford University", "paper_count": 40, "val": 24, "x": 0.0, "y": 0.0, "fixed": true}, {"id": "A5004412943", "label": "Mike Lewis", "group": "coauthor", "institution": "New York University", "weight": 1.554, "papers_count": 7, "val": 12, "x": 54.42, "y": -24.06, "fixed": false}, {"id": "A5081862885", "label": "Kenton Lee", "group": "coauthor", "institution": "Google (United States)", "weight": 1.333, "papers_count": 4, "val": 11, "x": 100.38, "y": 21.01, "fixed": false}, {"id": "A5039158419", "label": "Sewon Min", "group": "coauthor", "institution": "Meta (United States)", "weight": 1.268, "papers_count": 6, "val": 11, "x": 37.64, "y": 78.29, "fixed": false}, {"id": "A5025887224", "label": "Luheng He", "group": "coauthor", "institution": "Google (United States)", "weight": 1.167, "papers_count": 3, "val": 11, "x": 90.49, "y": 121.93, "fixed": false}, {"id": "A5082305994", "label": "Hannaneh Hajishirzi", "group": "coauthor", "institution": "Johns Hopkins University", "weight": 1.122, "papers_count": 7, "val": 11, "x": -50.91, "y": 97.75, "fixed": false}, {"id": "A5024311574", "label": "Omer Levy", "group": "coauthor", "institution": "Stanford University", "weight": 1.086, "papers_count": 5, "val": 11, "x": -4.32, "y": 71.55, "fixed": false}, {"id": "A5062471396", "label": "Armen Aghajanyan", "group": "coauthor", "institution": "Meta (United States)", "weight": 0.833, "papers_count": 2, "val": 10, "x": -0.59, "y": 126.43, "fixed": false}, {"id": "A5019081674", "label": "Yinhan Liu", "group": "coauthor", "institution": "Meta (United States)", "weight": 0.819, "papers_count": 4, "val": 10, "x": -91.7, "y": 17.84, "fixed": false}, {"id": "A5035142405", "label": "Eunsol Choi", "group": "coauthor", "institution": "Stanford University", "weight": 0.81, "papers_count": 3, "val": 10, "x": -122.17, "y": 73.85, "fixed": false}, {"id": "A5088517824", "label": "Noah A. Smith", "group": "coauthor", "institution": "Stanford University", "weight": 0.791, "papers_count": 5, "val": 10, "x": -112.37, "y": 38.67, "fixed": false}, {"id": "A5066873932", "label": "Wen-tau Yih", "group": "coauthor", "institution": "Meta (Israel)", "weight": 0.769, "papers_count": 4, "val": 10, "x": -46.69, "y": 9.54, "fixed": false}, {"id": "A5082767919", "label": "Mohit Iyyer", "group": "coauthor", "institution": "Stanford University", "weight": 0.768, "papers_count": 4, "val": 10, "x": -96.82, "y": -9.84, "fixed": false}, {"id": "A5063151917", "label": "Ari Holtzman", "group": "coauthor", "institution": "Stanford University", "weight": 0.754, "papers_count": 4, "val": 10, "x": -109.49, "y": -43.67, "fixed": false}, {"id": "A5101509445", "label": "Matthew E. Peters", "group": "coauthor", "institution": "University of Washington", "weight": 0.654, "papers_count": 4, "val": 10, "x": -61.49, "y": -77.81, "fixed": false}, {"id": "A5011974509", "label": "Marjan Ghazvininejad", "group": "coauthor", "institution": "Meta (United States)", "weight": 0.619, "papers_count": 3, "val": 10, "x": -71.75, "y": -103.5, "fixed": false}, {"id": "A5075834790", "label": "Naman Goyal", "group": "coauthor", "institution": "Meta (United States)", "weight": 0.558, "papers_count": 5, "val": 10, "x": -1.98, "y": -106.99, "fixed": false}, {"id": "A5085011940", "label": "Daniel S. Weld", "group": "coauthor", "institution": "Allen Institute", "weight": 0.533, "papers_count": 2, "val": 10, "x": -4.48, "y": -74.9, "fixed": false}, {"id": "A5082136238", "label": "Gabriel Stanovsky", "group": "coauthor", "institution": "Hebrew University of Jerusalem", "weight": 0.5, "papers_count": 1, "val": 10, "x": 51.54, "y": -113.37, "fixed": false}, {"id": "A5045050802", "label": "Sonal Gupta", "group": "coauthor", "institution": "Meta (United States)", "weight": 0.5, "papers_count": 1, "val": 10, "x": 108.12, "y": -46.61, "fixed": false}, {"id": "A5103238719", "label": "Weijia Shi", "group": "coauthor", "institution": "University of Washington", "weight": 0.486, "papers_count": 3, "val": 10, "x": 136.2, "y": -29.03, "fixed": false}, {"id": "A5016956470", "label": "Douwe Kiela", "group": "recommended", "institution": "University of North Carolina at Chapel Hill", "hybrid_score": 0.9441, "topic_similarity": 0.9068, "adamic_adar_score": 5.8095, "rationale": "Shares 24 mutual co-author(s) and strong alignment in Domain Adaptation and Few-Shot Learning.", "val": 16, "x": 275.3, "y": 100.44, "fixed": false}, {"id": "A5037862554", "label": "David Wadden", "group": "recommended", "institution": "University of Washington", "hybrid_score": 0.9345, "topic_similarity": 0.9647, "adamic_adar_score": 5.166, "rationale": "Shares 22 mutual co-author(s) and strong alignment in Domain Adaptation and Few-Shot Learning.", "val": 16, "x": -10.62, "y": 299.22, "fixed": false}, {"id": "A5003423990", "label": "Alexander Wettig", "group": "recommended", "institution": "Princeton University", "hybrid_score": 0.8693, "topic_similarity": 0.9218, "adamic_adar_score": 4.593, "rationale": "Shares 19 mutual co-author(s) and strong alignment in Topic Modeling.", "val": 16, "x": -282.24, "y": 80.5, "fixed": false}, {"id": "A5104036615", "label": "Amanpreet Singh", "group": "recommended", "institution": "New York University", "hybrid_score": 0.7875, "topic_similarity": 0.8603, "adamic_adar_score": 3.941, "rationale": "Shares 17 mutual co-author(s) and strong alignment in Topic Modeling.", "val": 16, "x": -167.17, "y": -248.41, "fixed": false}, {"id": "A5080628250", "label": "Binyuan Hui", "group": "recommended", "institution": "Independent / Unaffiliated", "hybrid_score": 0.7807, "topic_similarity": 0.8489, "adamic_adar_score": 3.941, "rationale": "Shares 17 mutual co-author(s) and strong alignment in Topic Modeling.", "val": 16, "x": 180.82, "y": -230.95, "fixed": false}], "links": [{"source": "A5067919401", "target": "A5004412943", "weight": 1.554, "papers_count": 7, "type": "coauthor"}, {"source": "A5067919401", "target": "A5081862885", "weight": 1.333, "papers_count": 4, "type": "coauthor"}, {"source": "A5067919401", "target": "A5039158419", "weight": 1.268, "papers_count": 6, "type": "coauthor"}, {"source": "A5067919401", "target": "A5025887224", "weight": 1.167, "papers_count": 3, "type": "coauthor"}, {"source": "A5067919401", "target": "A5082305994", "weight": 1.122, "papers_count": 7, "type": "coauthor"}, {"source": "A5067919401", "target": "A5024311574", "weight": 1.086, "papers_count": 5, "type": "coauthor"}, {"source": "A5067919401", "target": "A5062471396", "weight": 0.833, "papers_count": 2, "type": "coauthor"}, {"source": "A5067919401", "target": "A5019081674", "weight": 0.819, "papers_count": 4, "type": "coauthor"}, {"source": "A5067919401", "target": "A5035142405", "weight": 0.81, "papers_count": 3, "type": "coauthor"}, {"source": "A5067919401", "target": "A5088517824", "weight": 0.791, "papers_count": 5, "type": "coauthor"}, {"source": "A5067919401", "target": "A5066873932", "weight": 0.769, "papers_count": 4, "type": "coauthor"}, {"source": "A5067919401", "target": "A5082767919", "weight": 0.768, "papers_count": 4, "type": "coauthor"}, {"source": "A5067919401", "target": "A5063151917", "weight": 0.754, "papers_count": 4, "type": "coauthor"}, {"source": "A5067919401", "target": "A5101509445", "weight": 0.654, "papers_count": 4, "type": "coauthor"}, {"source": "A5067919401", "target": "A5011974509", "weight": 0.619, "papers_count": 3, "type": "coauthor"}, {"source": "A5067919401", "target": "A5075834790", "weight": 0.558, "papers_count": 5, "type": "coauthor"}, {"source": "A5067919401", "target": "A5085011940", "weight": 0.533, "papers_count": 2, "type": "coauthor"}, {"source": "A5067919401", "target": "A5082136238", "weight": 0.5, "papers_count": 1, "type": "coauthor"}, {"source": "A5067919401", "target": "A5045050802", "weight": 0.5, "papers_count": 1, "type": "coauthor"}, {"source": "A5067919401", "target": "A5103238719", "weight": 0.486, "papers_count": 3, "type": "coauthor"}, {"source": "A5081862885", "target": "A5101509445", "weight": 0.167, "papers_count": 1, "type": "inter_coauthor"}, {"source": "A5081862885", "target": "A5082767919", "weight": 0.167, "papers_count": 1, "type": "inter_coauthor"}, {"source": "A5019081674", "target": "A5085011940", "weight": 0.2, "papers_count": 1, "type": "inter_coauthor"}, {"source": "A5019081674", "target": "A5075834790", "weight": 0.386, "papers_count": 3, "type": "inter_coauthor"}, {"source": "A5019081674", "target": "A5024311574", "weight": 0.676, "papers_count": 3, "type": "inter_coauthor"}, {"source": "A5063151917", "target": "A5088517824", "weight": 0.111, "papers_count": 1, "type": "inter_coauthor"}, {"source": "A5063151917", "target": "A5082305994", "weight": 0.167, "papers_count": 1, "type": "inter_coauthor"}, {"source": "A5004412943", "target": "A5081862885", "weight": 0.667, "papers_count": 2, "type": "inter_coauthor"}, {"source": "A5004412943", "target": "A5019081674", "weight": 0.286, "papers_count": 2, "type": "inter_coauthor"}, {"source": "A5004412943", "target": "A5075834790", "weight": 0.377, "papers_count": 3, "type": "inter_coauthor"}, {"source": "A5004412943", "target": "A5066873932", "weight": 0.216, "papers_count": 2, "type": "inter_coauthor"}, {"source": "A5004412943", "target": "A5039158419", "weight": 0.601, "papers_count": 3, "type": "inter_coauthor"}, {"source": "A5004412943", "target": "A5011974509", "weight": 0.286, "papers_count": 2, "type": "inter_coauthor"}, {"source": "A5004412943", "target": "A5103238719", "weight": 0.143, "papers_count": 1, "type": "inter_coauthor"}, {"source": "A5004412943", "target": "A5082305994", "weight": 0.458, "papers_count": 2, "type": "inter_coauthor"}, {"source": "A5004412943", "target": "A5025887224", "weight": 0.667, "papers_count": 2, "type": "inter_coauthor"}, {"source": "A5004412943", "target": "A5082767919", "weight": 0.125, "papers_count": 1, "type": "inter_coauthor"}, {"source": "A5004412943", "target": "A5024311574", "weight": 0.143, "papers_count": 1, "type": "inter_coauthor"}, {"source": "A5066873932", "target": "A5075834790", "weight": 0.091, "papers_count": 1, "type": "inter_coauthor"}, {"source": "A5066873932", "target": "A5101509445", "weight": 0.333, "papers_count": 1, "type": "inter_coauthor"}, {"source": "A5066873932", "target": "A5088517824", "weight": 0.111, "papers_count": 1, "type": "inter_coauthor"}, {"source": "A5066873932", "target": "A5103238719", "weight": 0.2, "papers_count": 1, "type": "inter_coauthor"}, {"source": "A5066873932", "target": "A5082305994", "weight": 0.125, "papers_count": 1, "type": "inter_coauthor"}, {"source": "A5066873932", "target": "A5082767919", "weight": 0.125, "papers_count": 1, "type": "inter_coauthor"}, {"source": "A5039158419", "target": "A5063151917", "weight": 0.167, "papers_count": 1, "type": "inter_coauthor"}, {"source": "A5039158419", "target": "A5066873932", "weight": 0.268, "papers_count": 2, "type": "inter_coauthor"}, {"source": "A5039158419", "target": "A5088517824", "weight": 0.243, "papers_count": 2, "type": "inter_coauthor"}, {"source": "A5039158419", "target": "A5103238719", "weight": 0.143, "papers_count": 1, "type": "inter_coauthor"}, {"source": "A5039158419", "target": "A5082305994", "weight": 1.168, "papers_count": 6, "type": "inter_coauthor"}, {"source": "A5039158419", "target": "A5082767919", "weight": 0.125, "papers_count": 1, "type": "inter_coauthor"}, {"source": "A5011974509", "target": "A5019081674", "weight": 0.619, "papers_count": 3, "type": "inter_coauthor"}, {"source": "A5011974509", "target": "A5075834790", "weight": 0.286, "papers_count": 2, "type": "inter_coauthor"}, {"source": "A5011974509", "target": "A5024311574", "weight": 0.476, "papers_count": 2, "type": "inter_coauthor"}, {"source": "A5045050802", "target": "A5062471396", "weight": 0.5, "papers_count": 1, "type": "inter_coauthor"}, {"source": "A5088517824", "target": "A5101509445", "weight": 0.917, "papers_count": 3, "type": "inter_coauthor"}, {"source": "A5082136238", "target": "A5088517824", "weight": 0.5, "papers_count": 1, "type": "inter_coauthor"}, {"source": "A5082305994", "target": "A5101509445", "weight": 0.029, "papers_count": 1, "type": "inter_coauthor"}, {"source": "A5082305994", "target": "A5088517824", "weight": 0.441, "papers_count": 5, "type": "inter_coauthor"}, {"source": "A5082305994", "target": "A5082767919", "weight": 0.125, "papers_count": 1, "type": "inter_coauthor"}, {"source": "A5025887224", "target": "A5081862885", "weight": 1.167, "papers_count": 3, "type": "inter_coauthor"}, {"source": "A5025887224", "target": "A5082305994", "weight": 0.333, "papers_count": 1, "type": "inter_coauthor"}, {"source": "A5082767919", "target": "A5101509445", "weight": 0.167, "papers_count": 1, "type": "inter_coauthor"}, {"source": "A5024311574", "target": "A5085011940", "weight": 0.2, "papers_count": 1, "type": "inter_coauthor"}, {"source": "A5024311574", "target": "A5075834790", "weight": 0.143, "papers_count": 1, "type": "inter_coauthor"}, {"source": "A5024311574", "target": "A5088517824", "weight": 0.2, "papers_count": 1, "type": "inter_coauthor"}, {"source": "A5024311574", "target": "A5035142405", "weight": 0.333, "papers_count": 1, "type": "inter_coauthor"}, {"source": "A5035142405", "target": "A5085011940", "weight": 0.333, "papers_count": 1, "type": "inter_coauthor"}, {"source": "A5035142405", "target": "A5082767919", "weight": 0.143, "papers_count": 1, "type": "inter_coauthor"}, {"source": "A5067919401", "target": "A5016956470", "score": 0.9441, "type": "recommended"}, {"source": "A5067919401", "target": "A5037862554", "score": 0.9345, "type": "recommended"}, {"source": "A5067919401", "target": "A5003423990", "score": 0.8693, "type": "recommended"}, {"source": "A5067919401", "target": "A5104036615", "score": 0.7875, "type": "recommended"}, {"source": "A5067919401", "target": "A5080628250", "score": 0.7807, "type": "recommended"}]}, "recs": {"query_author_id": "A5067919401", "query_author_name": "Luke Zettlemoyer", "recommendations": [{"author_id": "A5016956470", "name": "Douwe Kiela", "institution": "University of North Carolina at Chapel Hill", "hybrid_score": 0.9441, "topic_similarity": 0.9068, "adamic_adar_score": 5.8095, "common_collaborators_count": 24, "common_collaborators": ["Dustin Schwenk", "Naman Goyal", "Niklas Muennighoff"], "shared_topics": ["Domain Adaptation and Few-Shot Learning", "Speech and dialogue systems", "Adversarial Robustness in Machine Learning"], "recommendation_rationale": "Shares 24 mutual co-author(s) and strong alignment in Domain Adaptation and Few-Shot Learning."}, {"author_id": "A5037862554", "name": "David Wadden", "institution": "University of Washington", "hybrid_score": 0.9345, "topic_similarity": 0.9647, "adamic_adar_score": 5.166, "common_collaborators_count": 22, "common_collaborators": ["Tushar Khot", "Dustin Schwenk", "Niklas Muennighoff"], "shared_topics": ["Domain Adaptation and Few-Shot Learning", "Multimodal Machine Learning Applications", "Topic Modeling"], "recommendation_rationale": "Shares 22 mutual co-author(s) and strong alignment in Domain Adaptation and Few-Shot Learning."}, {"author_id": "A5003423990", "name": "Alexander Wettig", "institution": "Princeton University", "hybrid_score": 0.8693, "topic_similarity": 0.9218, "adamic_adar_score": 4.593, "common_collaborators_count": 19, "common_collaborators": ["Dustin Schwenk", "Niklas Muennighoff", "Sewon Min"], "shared_topics": ["Topic Modeling", "Multimodal Machine Learning Applications", "Natural Language Processing Techniques"], "recommendation_rationale": "Shares 19 mutual co-author(s) and strong alignment in Topic Modeling."}, {"author_id": "A5104036615", "name": "Amanpreet Singh", "institution": "New York University", "hybrid_score": 0.7875, "topic_similarity": 0.8603, "adamic_adar_score": 3.941, "common_collaborators_count": 17, "common_collaborators": ["Tim Dettmers", "Dustin Schwenk", "Luca Soldaini"], "shared_topics": ["Topic Modeling", "Syntax, Semantics, Linguistic Variation", "Natural Language Processing Techniques"], "recommendation_rationale": "Shares 17 mutual co-author(s) and strong alignment in Topic Modeling."}, {"author_id": "A5080628250", "name": "Binyuan Hui", "institution": "Independent / Unaffiliated", "hybrid_score": 0.7807, "topic_similarity": 0.8489, "adamic_adar_score": 3.941, "common_collaborators_count": 17, "common_collaborators": ["Tim Dettmers", "Dustin Schwenk", "Luca Soldaini"], "shared_topics": ["Topic Modeling", "Natural Language Processing Techniques"], "recommendation_rationale": "Shares 17 mutual co-author(s) and strong alignment in Topic Modeling."}]}, "comms": {"count": 10, "communities": [{"community_id": 1, "author_count": 1382, "internal_edges": 12500, "leading_researchers": ["Luke Zettlemoyer (str=37.5)", "Noah A. Smith (str=23.2)", "Hannaneh Hajishirzi (str=22.4)"], "core_topics": ["Topic Modeling", "Natural Language Processing Techniques", "Domain Adaptation and Few-Shot Learning", "Multimodal Machine Learning Applications"], "key_venues": ["Proceedings of the conference - Association for Computational Linguistics. Meeting", "Conference on Empirical Methods in Natural Language Processing (EMNLP)"]}, {"community_id": 2, "author_count": 702, "internal_edges": 30483, "leading_researchers": ["Ryan Babbush (str=18.5)", "Jarrod R. McClean (str=15.7)", "Hartmut Neven (str=14.6)"], "core_topics": ["Quantum Computing Algorithms and Architecture", "Quantum many-body systems", "Quantum Information and Cryptography", "Advanced Chemical Physics Studies"], "key_venues": ["Nature", "Science"]}, {"community_id": 3, "author_count": 594, "internal_edges": 4258, "leading_researchers": ["Zhiyuan Liu (str=26.3)", "Maosong Sun (str=23.6)", "Jie Tang (str=10.4)"], "core_topics": ["Topic Modeling", "Natural Language Processing Techniques", "Multimodal Machine Learning Applications", "Domain Adaptation and Few-Shot Learning"], "key_venues": ["Proceedings of the conference - Association for Computational Linguistics. Meeting", "neural information processing systems"]}, {"community_id": 4, "author_count": 591, "internal_edges": 7461, "leading_researchers": ["Furu Wei (str=13.6)", "Jianfeng Gao (str=13.0)", "Weizhu Chen (str=9.7)"], "core_topics": ["Topic Modeling", "Natural Language Processing Techniques", "Domain Adaptation and Few-Shot Learning", "Multimodal Machine Learning Applications"], "key_venues": ["Proceedings of the conference - Association for Computational Linguistics. Meeting", "Nature"]}, {"community_id": 5, "author_count": 544, "internal_edges": 2561, "leading_researchers": ["Sergey Levine (str=16.5)", "Pieter Abbeel (str=16.5)", "Trevor Darrell (str=11.0)"], "core_topics": ["Reinforcement Learning in Robotics", "Domain Adaptation and Few-Shot Learning", "Robot Manipulation and Learning", "Advanced Neural Network Applications"], "key_venues": ["IEEE Computer Society Conference on Computer Vision and Pattern Recognition/Proceedings - IEEE Computer Society Conference on Computer Vision and Pattern Recognition/Proceedings", "neural information processing systems"]}, {"community_id": 6, "author_count": 511, "internal_edges": 14021, "leading_researchers": ["Bram van Ginneken (str=8.8)", "Pheng\u2010Ann Heng (str=7.9)", "Hao Chen (str=6.9)"], "core_topics": ["AI in cancer detection", "Radiomics and Machine Learning in Medical Imaging", "Artificial Intelligence in Healthcare and Education", "Cell Image Analysis Techniques"], "key_venues": ["IEEE Transactions on Medical Imaging", "Nature Communications"]}, {"community_id": 7, "author_count": 466, "internal_edges": 5487, "leading_researchers": ["David Silver (str=11.8)", "Demis Hassabis (str=11.4)", "Timothy Lillicrap (str=9.9)"], "core_topics": ["Reinforcement Learning in Robotics", "Artificial Intelligence in Games", "Topic Modeling", "Artificial Intelligence Applications"], "key_venues": ["Nature", "Science"]}, {"community_id": 8, "author_count": 415, "internal_edges": 4870, "leading_researchers": ["Kai-Wei Chang (str=6.8)", "William Yang Wang (str=6.0)", "Stella Biderman (str=4.2)"], "core_topics": ["Natural Language Processing Techniques", "Topic Modeling", "Speech Recognition and Synthesis", "Multimodal Machine Learning Applications"], "key_venues": ["Proceedings of the conference - Association for Computational Linguistics. Meeting", "Findings of the Association for Computational Linguistics: EMNLP (Findings of EMNLP)"]}, {"community_id": 9, "author_count": 398, "internal_edges": 2145, "leading_researchers": ["Philip S. Yu (str=16.7)", "Shirui Pan (str=10.4)", "Wenwu Zhu (str=9.9)"], "core_topics": ["Topic Modeling", "Advanced Graph Neural Networks", "Natural Language Processing Techniques", "Domain Adaptation and Few-Shot Learning"], "key_venues": ["Proceedings of the AAAI Conference on Artificial Intelligence", "ACM Computing Surveys"]}, {"community_id": 10, "author_count": 390, "internal_edges": 2610, "leading_researchers": ["Quoc Viet Le (str=18.0)", "Nicholas Evans (str=10.9)", "Massimiliano Todisco (str=10.0)"], "core_topics": ["Topic Modeling", "Speech Recognition and Synthesis", "Natural Language Processing Techniques", "Speech and Audio Processing"], "key_venues": ["neural information processing systems", "IEEE International Conference on Acoustics Speech and Signal Processing"]}]}};

    // -------------------------------------------------------------------------
    // DOM Elements & Canvas State (Declared FIRST to avoid TDZ)
    // -------------------------------------------------------------------------
    const svg = document.getElementById('networkSvg');
    const viewport = document.getElementById('viewport');
    const linksLayer = document.getElementById('linksLayer');
    const nodesLayer = document.getElementById('nodesLayer');
    const tooltip = document.getElementById('svgTooltip');

    let graphData = { nodes: [], links: [] };
    let currentAuthorId = 'A5067919401'; // Default: Luke Zettlemoyer
    let showRecommendations = true;

    // Viewport transform state
    let view = { x: 0, y: 0, scale: 1.0 };
    let isPanning = false;
    let panStart = { x: 0, y: 0 };
    let draggedNode = null;
    let hoveredNodeId = null;
    let animFrameId = null;
    let simulationFrameId = null;

    // -------------------------------------------------------------------------
    // Theme Management: Bright / Dark Mode
    // -------------------------------------------------------------------------
    function setTheme(theme) {
      document.documentElement.setAttribute('data-theme', theme);
      try { localStorage.setItem('scholarlykg_theme', theme); } catch(e){}
      const icon = document.getElementById('themeIcon');
      const label = document.getElementById('themeLabel');
      if (theme === 'dark') {
        if (icon) icon.innerText = '☀️';
        if (label) label.innerText = 'Bright';
      } else {
        if (icon) icon.innerText = '🌙';
        if (label) label.innerText = 'Dark';
      }
      if (nodesLayer && graphData && graphData.nodes && graphData.nodes.length > 0) {
        renderSvg();
      }
    }

    function toggleTheme() {
      const current = document.documentElement.getAttribute('data-theme') || 'light';
      setTheme(current === 'dark' ? 'light' : 'dark');
    }

    function initTheme() {
      let saved = null;
      try { saved = localStorage.getItem('scholarlykg_theme'); } catch(e){}
      if (!saved && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        saved = 'dark';
      }
      setTheme(saved || 'light');
    }

    // -------------------------------------------------------------------------
    // Viewport Transforms & Smooth Animations
    // -------------------------------------------------------------------------
    function applyTransform() {
      if (!isFinite(view.x)) view.x = 0;
      if (!isFinite(view.y)) view.y = 0;
      if (!isFinite(view.scale) || view.scale <= 0) view.scale = 1.0;
      viewport.setAttribute('transform', `translate(${view.x.toFixed(2)}, ${view.y.toFixed(2)}) scale(${view.scale.toFixed(4)})`);
    }

    // Smooth Viewport Animation (Ease-out Cubic)
    function animateViewTo(targetX, targetY, targetScale, duration = 300) {
      if (animFrameId) cancelAnimationFrame(animFrameId);
      const startX = view.x;
      const startY = view.y;
      const startScale = view.scale;
      const startTime = performance.now();

      function step(now) {
        const elapsed = now - startTime;
        const progress = Math.min(1, elapsed / duration);
        const ease = 1 - Math.pow(1 - progress, 3);

        view.x = startX + (targetX - startX) * ease;
        view.y = startY + (targetY - startY) * ease;
        view.scale = startScale + (targetScale - startScale) * ease;
        applyTransform();

        if (progress < 1) {
          animFrameId = requestAnimationFrame(step);
        } else {
          animFrameId = null;
        }
      }
      animFrameId = requestAnimationFrame(step);
    }

    function autoFitGraph(smooth = true) {
      const rect = svg.getBoundingClientRect();
      const parent = svg.parentElement;
      let width = (rect && rect.width > 50) ? rect.width : (svg.clientWidth || (parent && parent.clientWidth) || 850);
      let height = (rect && rect.height > 50) ? rect.height : (svg.clientHeight || (parent && parent.clientHeight) || 600);
      if (width < 100) width = 850;
      if (height < 100) height = 600;

      const activeNodes = (graphData.nodes || []).filter(n => (showRecommendations || n.group !== 'recommended') && isFinite(n.x) && isFinite(n.y));
      if (activeNodes.length === 0) {
        if (smooth) animateViewTo(width / 2, height / 2, 1.0, 300);
        else { view.x = width / 2; view.y = height / 2; view.scale = 1.0; applyTransform(); }
        return;
      }

      let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
      activeNodes.forEach(n => {
        if (n.x < minX) minX = n.x;
        if (n.x > maxX) maxX = n.x;
        if (n.y < minY) minY = n.y;
        if (n.y > maxY) maxY = n.y;
      });

      if (!isFinite(minX) || !isFinite(maxX) || minX >= maxX || !isFinite(minY) || !isFinite(maxY) || minY >= maxY) {
        if (smooth) animateViewTo(width / 2, height / 2, 1.0, 300);
        else { view.x = width / 2; view.y = height / 2; view.scale = 1.0; applyTransform(); }
        return;
      }

      const padding = 75;
      const graphW = Math.max(140, (maxX - minX) + padding * 2);
      const graphH = Math.max(140, (maxY - minY) + padding * 2);
      const scaleX = width / graphW;
      const scaleY = height / graphH;
      const targetScale = Math.max(0.45, Math.min(1.4, Math.min(scaleX, scaleY)));

      const centerX = (minX + maxX) / 2;
      const centerY = (minY + maxY) / 2;

      const targetX = (width / 2) - (centerX * targetScale);
      const targetY = (height / 2) - (centerY * targetScale);

      if (smooth) {
        animateViewTo(targetX, targetY, targetScale, 320);
      } else {
        view.scale = targetScale;
        view.x = targetX;
        view.y = targetY;
        applyTransform();
      }
    }

    // -------------------------------------------------------------------------
    // Force Simulation & Layout
    // -------------------------------------------------------------------------
    function initGraphLayout(animated = true) {
      if (simulationFrameId) cancelAnimationFrame(simulationFrameId);

      const nodes = graphData.nodes || [];
      const coauthors = nodes.filter(n => n.group === 'coauthor');
      const recs = nodes.filter(n => n.group === 'recommended');

      nodes.forEach(node => {
        node.vx = 0; node.vy = 0;
        if (node.group === 'query') {
          node.x = 0; node.y = 0;
          node.fixed = true;
        } else if (node.group === 'coauthor') {
          const idx = coauthors.indexOf(node);
          const total = Math.max(1, coauthors.length);
          const angle = (idx / total) * 2 * Math.PI;
          const r = 160 + (idx % 3) * 20;
          node.x = r * Math.cos(angle);
          node.y = r * Math.sin(angle);
          node.fixed = false;
        } else {
          const idx = recs.indexOf(node);
          const total = Math.max(1, recs.length);
          const angle = (idx / total) * 2 * Math.PI + 0.35;
          const r = 290 + (idx % 2) * 25;
          node.x = r * Math.cos(angle);
          node.y = r * Math.sin(angle);
          node.fixed = false;
        }
      });

      renderSvg();

      // Quick warm up
      for (let i = 0; i < 12; i++) {
        stepPhysicsSimulation(0.6 * Math.pow(0.92, i));
      }
      renderSvg();
      autoFitGraph(false);

      if (animated) {
        let frame = 0;
        const totalFrames = 28;
        function animStep() {
          frame++;
          const alpha = 0.5 * Math.pow(0.91, frame);
          stepPhysicsSimulation(alpha);
          updateSvgPositions();

          if (frame < totalFrames) {
            simulationFrameId = requestAnimationFrame(animStep);
          } else {
            simulationFrameId = null;
            autoFitGraph(true);
          }
        }
        simulationFrameId = requestAnimationFrame(animStep);
      } else {
        for (let i = 12; i < 45; i++) {
          stepPhysicsSimulation(0.6 * Math.pow(0.92, i));
        }
        renderSvg();
        autoFitGraph(false);
      }
    }

    function stepPhysicsSimulation(alpha) {
      const nodes = graphData.nodes || [];
      const links = (graphData.links || []).filter(l => showRecommendations || l.type !== 'recommended');
      const nodeMap = {};
      nodes.forEach(n => {
        nodeMap[n.id] = n;
        n.vx = 0; n.vy = 0;
        if (!isFinite(n.x)) n.x = 0;
        if (!isFinite(n.y)) n.y = 0;
      });

      // Pairwise repulsion
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const u = nodes[i];
          const v = nodes[j];
          let dx = v.x - u.x;
          let dy = v.y - u.y;
          let dist = Math.hypot(dx, dy);
          if (dist < 0.1) {
            dx = 1.0; dy = 1.0; dist = 1.414;
          }
          if (dist > 360) continue;
          const repForce = Math.min(22, (1400 / (dist * dist + 80))) * alpha;
          const fx = (dx / dist) * repForce;
          const fy = (dy / dist) * repForce;
          if (!u.fixed) { u.vx -= fx; u.vy -= fy; }
          if (!v.fixed) { v.vx += fx; v.vy += fy; }
        }
      }

      // Link attraction
      for (let k = 0; k < links.length; k++) {
        const l = links[k];
        const u = nodeMap[l.source];
        const v = nodeMap[l.target];
        if (!u || !v) continue;
        const dx = v.x - u.x;
        const dy = v.y - u.y;
        const dist = Math.hypot(dx, dy);
        if (dist < 0.1) continue;
        const targetDist = l.type === 'recommended' ? 290 : (l.type === 'inter_coauthor' ? 110 : 165);
        const springK = 0.05 * alpha;
        const force = (dist - targetDist) * springK;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        if (!u.fixed) { u.vx += fx; u.vy += fy; }
        if (!v.fixed) { v.vx -= fx; v.vy -= fy; }
      }

      // Concentric orbital guidance
      nodes.forEach(n => {
        if (n.fixed) return;
        const rTarget = n.group === 'recommended' ? 290 : 170;
        const rCurrent = Math.hypot(n.x, n.y) || 1;
        const radialForce = (rCurrent - rTarget) * 0.035 * alpha;
        n.vx -= (n.x / rCurrent) * radialForce;
        n.vy -= (n.y / rCurrent) * radialForce;
      });

      // Update positions with damping
      nodes.forEach(n => {
        if (!n.fixed) {
          n.x += Math.max(-25, Math.min(25, n.vx * 0.5));
          n.y += Math.max(-25, Math.min(25, n.vy * 0.5));
        }
        n.vx *= 0.5;
        n.vy *= 0.5;
      });
    }

    function resetLayout() {
      initGraphLayout(true);
    }

    // High-performance DOM position update
    function updateSvgPositions() {
      const nodeMap = {};
      (graphData.nodes || []).forEach(n => { nodeMap[n.id] = n; });

      nodesLayer.querySelectorAll('.node-element').forEach(el => {
        const node = nodeMap[el.dataset.id];
        if (node && isFinite(node.x) && isFinite(node.y)) {
          el.setAttribute('transform', `translate(${node.x.toFixed(2)}, ${node.y.toFixed(2)})`);
        }
      });

      linksLayer.querySelectorAll('.link-element').forEach(line => {
        const u = nodeMap[line.dataset.source];
        const v = nodeMap[line.dataset.target];
        if (u && v && isFinite(u.x) && isFinite(u.y) && isFinite(v.x) && isFinite(v.y)) {
          line.setAttribute('x1', u.x.toFixed(2));
          line.setAttribute('y1', u.y.toFixed(2));
          line.setAttribute('x2', v.x.toFixed(2));
          line.setAttribute('y2', v.y.toFixed(2));
        }
      });
    }

    // -------------------------------------------------------------------------
    // Render SVG Elements
    // -------------------------------------------------------------------------
    function renderSvg() {
      while (linksLayer.firstChild) linksLayer.removeChild(linksLayer.firstChild);
      while (nodesLayer.firstChild) nodesLayer.removeChild(nodesLayer.firstChild);

      const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      const nodeMap = {};
      (graphData.nodes || []).forEach(n => {
        nodeMap[n.id] = n;
        if (!isFinite(n.x)) n.x = 0;
        if (!isFinite(n.y)) n.y = 0;
      });

      // Render Links
      const activeLinks = (graphData.links || []).filter(l => showRecommendations || l.type !== 'recommended');
      activeLinks.forEach(l => {
        const u = nodeMap[l.source];
        const v = nodeMap[l.target];
        if (!u || !v || !isFinite(u.x) || !isFinite(u.y) || !isFinite(v.x) || !isFinite(v.y)) return;

        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', u.x.toFixed(2));
        line.setAttribute('y1', u.y.toFixed(2));
        line.setAttribute('x2', v.x.toFixed(2));
        line.setAttribute('y2', v.y.toFixed(2));
        line.setAttribute('class', 'link-element');
        line.dataset.source = l.source;
        line.dataset.target = l.target;

        if (l.type === 'recommended') {
          line.setAttribute('stroke', isDark ? '#f97316' : '#ea580c');
          line.setAttribute('stroke-width', '2.5');
          line.setAttribute('stroke-dasharray', '6,4');
        } else if (l.type === 'inter_coauthor') {
          line.setAttribute('stroke', isDark ? '#334155' : '#cbd5e1');
          line.setAttribute('stroke-width', '1.2');
        } else {
          line.setAttribute('stroke', isDark ? '#64748b' : '#475569');
          line.setAttribute('stroke-width', Math.min(5, Math.max(1.5, 1.2 + (l.weight || 1) * 0.7)).toFixed(2));
        }

        // Edge Tooltip
        line.addEventListener('mouseenter', (e) => showEdgeTooltip(e, l, u, v));
        line.addEventListener('mouseleave', hideTooltip);

        linksLayer.appendChild(line);
      });

      // Render Nodes
      (graphData.nodes || []).forEach(node => {
        if (!showRecommendations && node.group === 'recommended') return;
        if (!isFinite(node.x) || !isFinite(node.y)) return;

        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttribute('transform', `translate(${node.x.toFixed(2)}, ${node.y.toFixed(2)})`);
        g.setAttribute('class', 'node-element');
        g.setAttribute('tabindex', '0');
        g.setAttribute('role', 'button');
        g.setAttribute('aria-label', `${node.label}, ${node.institution}`);
        g.dataset.id = node.id;

        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', '0');
        circle.setAttribute('cy', '0');
        circle.setAttribute('r', (node.val || 16));

        if (node.group === 'query') {
          circle.setAttribute('fill', isDark ? '#3b82f6' : '#2563eb');
          circle.setAttribute('stroke', isDark ? '#60a5fa' : '#1d4ed8');
          circle.setAttribute('stroke-width', '4');
        } else if (node.group === 'coauthor') {
          circle.setAttribute('fill', isDark ? '#10b981' : '#059669');
          circle.setAttribute('stroke', isDark ? '#34d399' : '#047857');
          circle.setAttribute('stroke-width', '2.5');
        } else {
          circle.setAttribute('fill', isDark ? '#f97316' : '#ea580c');
          circle.setAttribute('stroke', isDark ? '#fb923c' : '#c2410c');
          circle.setAttribute('stroke-width', '2.5');
          circle.setAttribute('stroke-dasharray', '4,2');
        }

        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.textContent = node.label;
        text.setAttribute('class', node.group === 'query' ? 'node-label node-label-query' : 'node-label');
        text.setAttribute('y', ((node.val || 16) + 14));

        g.appendChild(circle);
        g.appendChild(text);

        // Tooltip & Ego-Focus Hover Events
        g.addEventListener('mouseenter', (e) => {
          showTooltip(e, node);
          highlightEgoNetwork(node.id);
        });
        g.addEventListener('mouseleave', () => {
          hideTooltip();
          unhighlightEgoNetwork();
        });

        // Click to Pivot
        g.addEventListener('click', (e) => {
          e.stopPropagation();
          if (node.id !== currentAuthorId) {
            loadAuthor(node.id);
          }
        });

        // Butter-smooth node dragging
        g.addEventListener('mousedown', (e) => {
          e.stopPropagation();
          draggedNode = { node, el: g };
        });

        nodesLayer.appendChild(g);
      });
    }

    // Ego-Network Focus Highlighting
    function highlightEgoNetwork(targetId) {
      hoveredNodeId = targetId;
      const connected = new Set([targetId]);
      (graphData.links || []).forEach(l => {
        if (!showRecommendations && l.type === 'recommended') return;
        if (l.source === targetId) connected.add(l.target);
        if (l.target === targetId) connected.add(l.source);
      });

      nodesLayer.querySelectorAll('.node-element').forEach(el => {
        if (connected.has(el.dataset.id)) {
          el.classList.remove('node-dimmed');
          if (el.dataset.id === targetId) el.classList.add('node-highlight');
        } else {
          el.classList.add('node-dimmed');
          el.classList.remove('node-highlight');
        }
      });

      linksLayer.querySelectorAll('.link-element').forEach(line => {
        const s = line.dataset.source;
        const t = line.dataset.target;
        if ((s === targetId && connected.has(t)) || (t === targetId && connected.has(s))) {
          line.classList.remove('link-dimmed');
          line.classList.add('link-highlight');
        } else {
          line.classList.add('link-dimmed');
          line.classList.remove('link-highlight');
        }
      });
    }

    function unhighlightEgoNetwork() {
      hoveredNodeId = null;
      nodesLayer.querySelectorAll('.node-element').forEach(el => {
        el.classList.remove('node-dimmed', 'node-highlight');
      });
      linksLayer.querySelectorAll('.link-element').forEach(line => {
        line.classList.remove('link-dimmed', 'link-highlight');
      });
    }

    function showTooltip(e, node) {
      const clientX = e.clientX;
      const clientY = e.clientY;
      tooltip.style.display = 'block';
      tooltip.style.left = (clientX + 14) + 'px';
      tooltip.style.top = (clientY + 14) + 'px';

      if (node.group === 'query') {
        tooltip.innerHTML = `<strong>${node.label}</strong><br><span style="color:#94a3b8">${node.institution}</span><br><span style="color:#60a5fa; font-weight:700;">${node.paper_count} Works in AI/ML Corpus</span>`;
      } else if (node.group === 'coauthor') {
        tooltip.innerHTML = `<strong>${node.label}</strong><br><span style="color:#94a3b8">${node.institution}</span><br>Collaboration Strength: <strong>${node.weight}</strong><br>Joint Works: <strong>${node.papers_count}</strong><br><em style="color:#34d399; font-weight:600;">Click to center network</em>`;
      } else {
        tooltip.innerHTML = `<strong>${node.label}</strong> <span style="color:#fb923c; font-weight:700;">(Recommended)</span><br><span style="color:#94a3b8">${node.institution}</span><br>Hybrid Score: <strong>${Number(node.hybrid_score).toFixed(3)}</strong><br>Topic Match: <strong>${(node.topic_similarity * 100).toFixed(1)}%</strong><br><em style="color:#fb923c; font-weight:600;">Click to explore ego-network</em>`;
      }
    }

    function showEdgeTooltip(e, l, u, v) {
      const clientX = e.clientX;
      const clientY = e.clientY;
      tooltip.style.display = 'block';
      tooltip.style.left = (clientX + 14) + 'px';
      tooltip.style.top = (clientY + 14) + 'px';

      if (l.type === 'recommended') {
        tooltip.innerHTML = `<strong>Prospective Collaboration</strong><br><span style="color:#94a3b8">${u.label} &amp; ${v.label}</span><br>Hybrid Link Score: <strong style="color:#fb923c;">${Number(l.score || 0).toFixed(3)}</strong><br><span style="font-size:11px; color:#cbd5e1;">40% network closure &middot; 60% topical cosine</span>`;
      } else {
        tooltip.innerHTML = `<strong>Co-Authorship Edge</strong><br><span style="color:#94a3b8">${u.label} &amp; ${v.label}</span><br>Newman Intensity: <strong>${l.weight}</strong><br>Joint Works: <strong>${l.papers_count}</strong>`;
      }
    }

    function hideTooltip() {
      tooltip.style.display = 'none';
    }

    // Smooth Wheel Zoom with Soft Interpolation
    svg.addEventListener('wheel', (e) => {
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.15 : 0.87;
      const rect = svg.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      const newScale = Math.max(0.3, Math.min(3.5, view.scale * zoomFactor));
      const newX = mouseX - (mouseX - view.x) * (newScale / view.scale);
      const newY = mouseY - (mouseY - view.y) * (newScale / view.scale);

      animateViewTo(newX, newY, newScale, 130);
    }, { passive: false });

    svg.addEventListener('mousedown', (e) => {
      if (draggedNode) return;
      isPanning = true;
      panStart = { x: e.clientX - view.x, y: e.clientY - view.y };
    });

    // Real-time butter-smooth node dragging
    window.addEventListener('mousemove', (e) => {
      if (draggedNode) {
        const rect = svg.getBoundingClientRect();
        const nx = (e.clientX - rect.left - view.x) / view.scale;
        const ny = (e.clientY - rect.top - view.y) / view.scale;
        draggedNode.node.x = nx;
        draggedNode.node.y = ny;
        draggedNode.el.setAttribute('transform', `translate(${nx.toFixed(2)}, ${ny.toFixed(2)})`);

        // Real-time line updates
        const nodeId = draggedNode.node.id;
        linksLayer.querySelectorAll(`.link-element[data-source="${nodeId}"]`).forEach(l => {
          l.setAttribute('x1', nx.toFixed(2));
          l.setAttribute('y1', ny.toFixed(2));
        });
        linksLayer.querySelectorAll(`.link-element[data-target="${nodeId}"]`).forEach(l => {
          l.setAttribute('x2', nx.toFixed(2));
          l.setAttribute('y2', ny.toFixed(2));
        });
      } else if (isPanning) {
        view.x = e.clientX - panStart.x;
        view.y = e.clientY - panStart.y;
        applyTransform();
      }
    });

    window.addEventListener('mouseup', () => {
      draggedNode = null;
      isPanning = false;
    });

    function zoomIn() {
      const rect = svg.getBoundingClientRect();
      const cx = (rect.width || 800) / 2;
      const cy = (rect.height || 600) / 2;
      const newScale = Math.min(3.5, view.scale * 1.25);
      const ratio = newScale / view.scale;
      const newX = cx - (cx - view.x) * ratio;
      const newY = cy - (cy - view.y) * ratio;
      animateViewTo(newX, newY, newScale, 220);
    }

    function zoomOut() {
      const rect = svg.getBoundingClientRect();
      const cx = (rect.width || 800) / 2;
      const cy = (rect.height || 600) / 2;
      const newScale = Math.max(0.3, view.scale / 1.25);
      const ratio = newScale / view.scale;
      const newX = cx - (cx - view.x) * ratio;
      const newY = cy - (cy - view.y) * ratio;
      animateViewTo(newX, newY, newScale, 220);
    }

    function toggleRecommendations(btn) {
      showRecommendations = !showRecommendations;
      const button = btn || document.getElementById('toggleRecBtn');
      if (showRecommendations) {
        button.classList.remove('btn-outline');
        button.classList.add('btn-primary');
        button.innerText = 'Hide Recommendations';
      } else {
        button.classList.remove('btn-primary');
        button.classList.add('btn-outline');
        button.innerText = 'Show Recommendations';
      }
      renderSvg();
      autoFitGraph(true);
    }

    window.addEventListener('resize', () => {
      autoFitGraph(false);
    });

    // -------------------------------------------------------------------------
    // Search Autocomplete with Full Keyboard Navigation
    // -------------------------------------------------------------------------
    const searchInput = document.getElementById('authorSearchInput');
    const searchDropdown = document.getElementById('searchDropdown');
    const searchSpinner = document.getElementById('searchSpinner');
    const searchClearBtn = document.getElementById('searchClearBtn');
    let searchTimer;
    let selectedSearchIdx = -1;
    let currentSearchResults = [];

    searchInput.addEventListener('input', () => {
      clearTimeout(searchTimer);
      const q = searchInput.value.trim();
      searchClearBtn.style.display = q.length > 0 ? 'block' : 'none';

      if (q.length < 2) {
        searchDropdown.style.display = 'none';
        searchSpinner.style.display = 'none';
        currentSearchResults = [];
        selectedSearchIdx = -1;
        return;
      }
      searchSpinner.style.display = 'block';
      searchTimer = setTimeout(() => {
        fetch('/api/search?q=' + encodeURIComponent(q))
          .then(res => res.json())
          .then(data => {
            searchSpinner.style.display = 'none';
            currentSearchResults = data.results || [];
            selectedSearchIdx = -1;
            if (currentSearchResults.length > 0) {
              const qEsc = q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
              const qRegex = new RegExp(`(${qEsc})`, 'gi');

              searchDropdown.innerHTML = currentSearchResults.map((a, i) => {
                const highlightedName = a.name.replace(qRegex, '<span class="match-highlight">$1</span>');
                return `
                  <div class="search-item" data-idx="${i}" onclick="selectSearch('${a.author_id}')" tabindex="0">
                    <div>
                      <div class="search-item-title">${highlightedName}</div>
                      <div class="search-item-inst">${a.institution} &middot; <span style="font-family:ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace">${a.paper_count} works</span></div>
                    </div>
                    <span class="btn btn-primary btn-sm">Select</span>
                  </div>
                `;
              }).join('');
              searchDropdown.style.display = 'block';
            } else {
              searchDropdown.innerHTML = '<div style="padding: 12px; color: var(--color-muted); font-size: 12px;">No matching researchers found in corpus.</div>';
              searchDropdown.style.display = 'block';
            }
          })
          .catch(() => { searchSpinner.style.display = 'none'; });
      }, 140);
    });

    searchClearBtn.addEventListener('click', () => {
      searchInput.value = '';
      searchClearBtn.style.display = 'none';
      searchDropdown.style.display = 'none';
      searchInput.focus();
    });

    searchInput.addEventListener('keydown', (e) => {
      const items = searchDropdown.querySelectorAll('.search-item');
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (items.length > 0) {
          selectedSearchIdx = (selectedSearchIdx + 1) % items.length;
          updateSearchHighlight(items);
        }
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (items.length > 0) {
          selectedSearchIdx = (selectedSearchIdx - 1 + items.length) % items.length;
          updateSearchHighlight(items);
        }
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (selectedSearchIdx >= 0 && selectedSearchIdx < currentSearchResults.length) {
          selectSearch(currentSearchResults[selectedSearchIdx].author_id);
        } else {
          triggerSearch();
        }
      } else if (e.key === 'Escape') {
        searchDropdown.style.display = 'none';
      }
    });

    function updateSearchHighlight(items) {
      items.forEach((item, idx) => {
        if (idx === selectedSearchIdx) {
          item.classList.add('active-item');
          item.scrollIntoView({ block: 'nearest' });
        } else {
          item.classList.remove('active-item');
        }
      });
    }

    function selectSearch(authorId) {
      searchDropdown.style.display = 'none';
      searchInput.value = '';
      searchClearBtn.style.display = 'none';
      loadAuthor(authorId);
    }

    function triggerSearch() {
      const q = searchInput.value.trim();
      if (q.length >= 2) {
        searchSpinner.style.display = 'block';
        fetch('/api/search?q=' + encodeURIComponent(q))
          .then(res => res.json())
          .then(data => {
            searchSpinner.style.display = 'none';
            if (data.results && data.results.length > 0) {
              selectSearch(data.results[0].author_id);
            }
          })
          .catch(() => { searchSpinner.style.display = 'none'; });
      }
    }

    document.addEventListener('click', (e) => {
      if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
        searchDropdown.style.display = 'none';
      }
    });

    // Global Keyboard Shortcuts
    document.addEventListener('keydown', (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      if (e.key === '/') {
        e.preventDefault();
        searchInput.focus();
        searchInput.select();
      } else if (e.key === '+' || e.key === '=') {
        zoomIn();
      } else if (e.key === '-' || e.key === '_') {
        zoomOut();
      } else if (e.key === 'f' || e.key === 'F' || e.key === '0') {
        autoFitGraph(true);
      } else if (e.key === 'r' || e.key === 'R') {
        toggleRecommendations();
      } else if (e.key === 't' || e.key === 'T') {
        toggleTheme();
      } else if (e.key === 'Escape') {
        closeFigureModal();
        searchDropdown.style.display = 'none';
        hideTooltip();
      }
    });

    // -------------------------------------------------------------------------
    // Sidebar Tabs
    // -------------------------------------------------------------------------
    function switchSidebarTab(tab, btn) {
      document.querySelectorAll('.tab-item').forEach(b => b.classList.remove('active'));
      ['tabDossier', 'tabRecommendations', 'tabFigures', 'tabCommunities'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
      });

      if (btn) {
        btn.classList.add('active');
      } else if (window.event && window.event.currentTarget) {
        window.event.currentTarget.classList.add('active');
      }

      if (tab === 'dossier') { const el = document.getElementById('tabDossier'); if (el) el.style.display = 'block'; }
      else if (tab === 'recommendations') { const el = document.getElementById('tabRecommendations'); if (el) el.style.display = 'block'; }
      else if (tab === 'figures') { const el = document.getElementById('tabFigures'); if (el) el.style.display = 'block'; }
      else if (tab === 'communities') { const el = document.getElementById('tabCommunities'); if (el) el.style.display = 'block'; }
    }

    // Figure Lightbox Modal
    function openFigureModal(src, title, desc) {
      document.getElementById('modalFigImg').src = src;
      document.getElementById('modalFigTitle').innerText = title;
      document.getElementById('modalFigDesc').innerText = desc;
      const modal = document.getElementById('figModal');
      modal.style.display = 'flex';
    }
    function closeFigureModal(e) {
      const modal = document.getElementById('figModal');
      modal.style.display = 'none';
    }

    // -------------------------------------------------------------------------
    // Data Renderers
    // -------------------------------------------------------------------------
    function renderAuthorProfile(data) {
      if (!data) return;
      document.getElementById('profName').innerText = data.name || 'Unknown Researcher';
      document.getElementById('profInst').innerText = (data.institutions && data.institutions.join(', ')) || 'Independent / Unaffiliated';
      document.getElementById('profPapers').innerText = (data.paper_count || 0).toLocaleString();
      document.getElementById('profCollabs').innerText = (data.collaborator_count || 0).toLocaleString();
      document.getElementById('profCitations').innerText = ((data.total_citations !== undefined ? data.total_citations : (data.papers ? data.papers.reduce((a, b) => a + (b.citations || 0), 0) : 0))).toLocaleString();
      document.getElementById('profOrcid').innerText = data.orcid ? 'Verified' : 'None';

      if (data.topics) {
        document.getElementById('profTopics').innerHTML = data.topics.map(t => `<span class="topic-pill">${t.name} (${t.count})</span>`).join('');
      }

      if (data.collaborators) {
        document.getElementById('coauthorTableBody').innerHTML = data.collaborators.slice(0, 15).map(c => `
          <tr>
            <td><strong>${c.name}</strong><div style="font-size:11px; color:var(--color-muted);">${c.institution}</div></td>
            <td><strong>${Number(c.weight).toFixed(2)}</strong></td>
            <td>${c.papers_count}</td>
            <td><button class="btn btn-primary btn-sm" onclick="loadAuthor('${c.author_id}')">Pivot Graph</button></td>
          </tr>
        `).join('');
      }

      if (data.papers) {
        document.getElementById('papersTableBody').innerHTML = data.papers.slice(0, 15).map(p => `
          <tr>
            <td><span style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-weight:600; color: var(--color-muted);">${p.year || 'N/A'}</span></td>
            <td><strong style="color: var(--color-primary); font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;">${(p.citations || 0).toLocaleString()}</strong></td>
            <td><strong>${p.title}</strong><div style="font-size: 11px; color: var(--color-muted);">${p.venue}</div></td>
          </tr>
        `).join('');
      }
    }

    function renderRecommendations(data) {
      const container = document.getElementById('recsContainer');
      const recs = (data && data.recommendations) || [];
      if (recs.length > 0) {
        container.innerHTML = recs.map((r, i) => `
          <div class="rec-card">
            <div class="rec-header">
              <div class="rec-title-group">
                <span class="rec-rank">#${i + 1}</span>
                <span class="rec-author-name" onclick="loadAuthor('${r.author_id}')">${r.name}</span>
              </div>
              <span class="rec-score-pill">Match: ${(r.hybrid_score * 100).toFixed(1)}%</span>
            </div>
            <div class="rec-affiliation">${r.institution}</div>
            <div class="rec-callout">${r.recommendation_rationale}</div>
            <div class="rec-breakdown">
              <span>Topic Alignment: <strong>${(r.topic_similarity * 100).toFixed(1)}%</strong></span>
              <span>Mutual Contacts: <strong>${r.common_collaborators_count}</strong></span>
              <span>Adamic-Adar: <strong>${Number(r.adamic_adar_score).toFixed(2)}</strong></span>
            </div>
            <div class="rec-footer">
              <button class="btn btn-primary btn-sm" onclick="loadAuthor('${r.author_id}')">Pivot Graph</button>
            </div>
          </div>
        `).join('');
      } else {
        container.innerHTML = '<div style="padding: 24px; text-align: center; color: var(--color-muted);">No prospective candidates found outside immediate co-authorship circle.</div>';
      }
    }

    function renderCommunities(data) {
      const container = document.getElementById('communitiesContainer');
      const comms = (data && data.communities) || [];
      if (comms.length > 0) {
        container.innerHTML = comms.map(c => `
          <div class="comm-card">
            <div class="comm-head">
              <span class="comm-title">Community #${c.community_id}</span>
              <span class="comm-stats">${(c.size || c.author_count || 0).toLocaleString()} authors &middot; ${(c.internal_edges || 0).toLocaleString()} edges</span>
            </div>
            <div class="comm-leaders">${(c.leading_authors || c.leading_researchers || []).join(' &middot; ')}</div>
            <div class="comm-topics">${(c.core_topics || []).join(', ')}</div>
          </div>
        `).join('');
      }
    }

    function loadAuthor(authorId) {
      currentAuthorId = authorId;
      hideTooltip();

      // If requested author matches embedded default, immediately show embedded data while fetching
      if (typeof DEFAULT_DATA !== 'undefined' && DEFAULT_DATA.profile && DEFAULT_DATA.profile.author_id === authorId) {
        renderAuthorProfile(DEFAULT_DATA.profile);
        renderRecommendations(DEFAULT_DATA.recs);
        graphData = JSON.parse(JSON.stringify(DEFAULT_DATA.graph));
        renderSvg();
        autoFitGraph(true);
      }

      // 1. Fetch Profile
      fetch('/api/authors/' + authorId)
        .then(res => res.json())
        .then(data => {
          if (data && data.name) renderAuthorProfile(data);
        })
        .catch(err => console.warn('Author profile fetch skipped / offline:', err));

      // 2. Fetch Graph Data
      fetch('/api/authors/' + authorId + '/graph')
        .then(res => res.json())
        .then(data => {
          if (!data || !data.nodes) return;
          graphData = data;
          const queryNode = data.nodes.find(n => n.group === 'query') || data.nodes[0];
          document.getElementById('networkTitleText').innerText = `${queryNode ? queryNode.label : 'Author'} — Ego-Network`;
          document.getElementById('networkStatsText').innerText = `${(data.nodes || []).length} Nodes · ${(data.links || []).length} Edges`;
          initGraphLayout(true);
        })
        .catch(err => console.warn('Author graph fetch skipped / offline:', err));

      // 3. Fetch Recommendations
      fetch('/api/authors/' + authorId + '/recommendations?k=5')
        .then(res => res.json())
        .then(data => {
          if (data && data.recommendations) renderRecommendations(data);
        })
        .catch(err => console.warn('Recommendations fetch skipped / offline:', err));
    }

    // Communities Loader
    fetch('/api/communities')
      .then(res => res.json())
      .then(data => renderCommunities(data))
      .catch(err => console.error('Error fetching communities:', err));

    // Reliable Initial Load: Instant Render from Embedded Data + Theme Init
    function initDashboard() {
      initTheme();

      if (typeof DEFAULT_DATA !== 'undefined' && DEFAULT_DATA.graph) {
        graphData = JSON.parse(JSON.stringify(DEFAULT_DATA.graph));
        const queryNode = (graphData.nodes || []).find(n => n.group === 'query') || (graphData.nodes && graphData.nodes[0]);
        document.getElementById('networkTitleText').innerText = `${queryNode ? queryNode.label : 'Author'} — Ego-Network`;
        document.getElementById('networkStatsText').innerText = `${(graphData.nodes || []).length} Nodes · ${(graphData.links || []).length} Edges`;
        renderAuthorProfile(DEFAULT_DATA.profile);
        renderRecommendations(DEFAULT_DATA.recs);
        renderCommunities(DEFAULT_DATA.comms);
        renderSvg();
        autoFitGraph(false);
      }
      loadAuthor('A5067919401');
    }

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', initDashboard);
    } else {
      initDashboard();
    }
  </script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(content=HTML_PAGE, status_code=200)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
