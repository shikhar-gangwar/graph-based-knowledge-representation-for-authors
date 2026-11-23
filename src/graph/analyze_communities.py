"""
Co-Authorship Network Topology & Community Detection Module
Executes Louvain community detection on Newman-weighted co-authorship graphs.
Computes centrality metrics (PageRank, Betweenness), modularity Q, conductance,
and extracts semantic topic profiles for detected research communities.
"""

import os
import csv
import json
from collections import defaultdict, Counter
import networkx as nx
from typing import Dict, Any, List, Set, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

def load_csv(filename: str) -> List[Dict[str, str]]:
    path = os.path.join(PROCESSED_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def run_community_analysis():
    print("=" * 70)
    print("EXECUTING CO-AUTHORSHIP NETWORK ANALYSIS & COMMUNITY DETECTION")
    print("=" * 70)

    # 1. Load Data
    authors_rows = load_csv("authors.csv")
    author_name_map = {r["author_id"]: r["name"] for r in authors_rows}

    edges_rows = load_csv("coauthorship_edges.csv")
    authorships = load_csv("authorships.csv")
    work_topics = load_csv("work_topics.csv")
    topics_rows = load_csv("topics.csv")
    works_rows = load_csv("works.csv")

    topic_name_map = {r["topic_id"]: r["name"] for r in topics_rows}
    work_venue_map = {r["paper_id"]: r["venue_id"] for r in works_rows}

    # Author to papers index
    author_papers = defaultdict(set)
    for row in authorships:
        author_papers[row["author_id"]].add(row["paper_id"])

    # Paper to topics index
    paper_topics = defaultdict(set)
    for row in work_topics:
        paper_topics[row["paper_id"]].add(row["topic_id"])

    # 2. Build NetworkX Weighted Graph
    G = nx.Graph()
    for row in edges_rows:
        u = row["author_id_1"]
        v = row["author_id_2"]
        w = float(row["weight"])
        p_count = int(row["papers_count"])
        G.add_edge(u, v, weight=w, papers_count=p_count)

    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()

    print(f"\n[Network Topology Overview]")
    print(f"  Active Co-Authorship Nodes: {n_nodes}")
    print(f"  Weighted Collaboration Edges: {n_edges}")

    # Connected Components
    components = sorted(nx.connected_components(G), key=len, reverse=True)
    n_components = len(components)
    gcc_nodes = components[0] if components else set()
    gcc_size = len(gcc_nodes)
    gcc_ratio = (gcc_size / n_nodes) * 100 if n_nodes else 0

    print(f"  Connected Components: {n_components}")
    print(f"  Giant Connected Component (GCC): {gcc_size} nodes ({gcc_ratio:.1f}%)")

    # Degrees
    degrees = [d for _, d in G.degree()]
    avg_degree = sum(degrees) / len(degrees) if degrees else 0
    max_degree = max(degrees) if degrees else 0
    density = nx.density(G)
    clustering = nx.transitivity(G)

    print(f"  Average Degree: {avg_degree:.2f}")
    print(f"  Maximum Degree: {max_degree}")
    print(f"  Network Density: {density:.6f}")
    print(f"  Transitivity (Clustering Coefficient): {clustering:.4f}")

    # 3. Centrality Metrics on GCC
    GCC_G = G.subgraph(gcc_nodes)
    print("\n[Centrality Analysis on GCC]")
    pagerank_scores = nx.pagerank(GCC_G, weight='weight', alpha=0.85)
    
    # Top 5 PageRank Authors
    top_pagerank = sorted(pagerank_scores.items(), key=lambda x: x[1], reverse=True)[:5]
    print("  Top 5 Authoritative Researchers (PageRank):")
    for aid, score in top_pagerank:
        print(f"    - {author_name_map.get(aid, aid)}: {score:.5f}")

    # 4. Louvain Community Detection
    print("\n[Community Detection: Louvain Algorithm (seed=42)]")
    communities = nx.community.louvain_communities(G, weight='weight', seed=42)
    modularity_q = nx.community.modularity(G, communities, weight='weight')
    print(f"  Total Communities Detected: {len(communities)}")
    print(f"  Partition Modularity (Q):   {modularity_q:.4f}")

    # Sort communities by size
    sorted_communities = sorted(communities, key=len, reverse=True)
    community_sizes = [len(c) for c in sorted_communities]

    print("\n[Top 5 Research Communities Characterization]")
    community_summaries = []

    for i, comm in enumerate(sorted_communities[:5], 1):
        comm_nodes = list(comm)
        size = len(comm_nodes)
        
        # Subgraph density
        comm_subgraph = G.subgraph(comm)
        internal_edges = comm_subgraph.number_of_edges()

        # Leading authors in community by internal degree
        deg_in_comm = dict(comm_subgraph.degree())
        top_authors_aid = sorted(deg_in_comm.items(), key=lambda x: x[1], reverse=True)[:4]
        top_authors_names = [f"{author_name_map.get(aid, aid)} (deg={deg})" for aid, deg in top_authors_aid]

        # Gather topics for all papers authored by members
        comm_topics = Counter()
        comm_venues = Counter()
        for aid in comm_nodes:
            for pid in author_papers[aid]:
                for tid in paper_topics[pid]:
                    comm_topics[topic_name_map.get(tid, tid)] += 1
                v_name = work_venue_map.get(pid)
                if v_name:
                    comm_venues[v_name] += 1

        top_topics = [t for t, _ in comm_topics.most_common(5)]
        top_venues = [v for v, _ in comm_venues.most_common(3)]

        summary = {
            "community_id": i,
            "size_authors": size,
            "internal_edges": internal_edges,
            "top_authors": top_authors_names,
            "predominant_cso_topics": top_topics,
            "key_venues": top_venues
        }
        community_summaries.append(summary)

        print(f"\n  * Community #{i} (Size: {size} authors, Internal Edges: {internal_edges}):")
        print(f"    - Prominent Researchers: {', '.join(top_authors_names[:3])}")
        print(f"    - Core Topics:           {', '.join(top_topics)}")

    # 5. Save Results
    results = {
        "network_metrics": {
            "nodes": n_nodes,
            "edges": n_edges,
            "components": n_components,
            "gcc_size": gcc_size,
            "gcc_percentage": round(gcc_ratio, 2),
            "average_degree": round(avg_degree, 2),
            "maximum_degree": max_degree,
            "density": round(density, 6),
            "transitivity": round(clustering, 4)
        },
        "community_detection": {
            "algorithm": "Louvain",
            "seed": 42,
            "weight_metric": "Newman co-authorship",
            "modularity_q": round(modularity_q, 4),
            "num_communities": len(communities),
            "largest_5_sizes": community_sizes[:5]
        },
        "top_communities": community_summaries
    }

    out_path = os.path.join(PROCESSED_DIR, "community_analysis_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n[Artifact] Analysis results saved to: {out_path}")

if __name__ == "__main__":
    run_community_analysis()
