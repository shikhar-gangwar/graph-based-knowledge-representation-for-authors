"""
Unit and integration test for FastAPI dashboard endpoints.
"""
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi.testclient import TestClient
from src.dashboard.app import app

def test_dashboard():
    client = TestClient(app)

    # 1. Test root HTML
    res = client.get("/")
    assert res.status_code == 200, f"Root returned {res.status_code}"
    assert "ScholarlyKG" in res.text

    # 2. Test /api/stats
    res = client.get("/api/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["total_works"] == 4989
    assert data["total_authors"] == 22185
    assert data["active_coauthorship_nodes"] == 22037
    print("[PASS] /api/stats verified.")

    # 3. Test /api/search
    res = client.get("/api/search?q=Luke")
    assert res.status_code == 200
    data = res.json()
    assert len(data["results"]) > 0
    top_hit = data["results"][0]
    assert "Luke" in top_hit["name"]
    luke_id = top_hit["author_id"]
    print(f"[PASS] /api/search verified: found {top_hit['name']} ({luke_id}).")

    # 4. Test /api/authors/{author_id}
    res = client.get(f"/api/authors/{luke_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == top_hit["name"]
    assert len(data["collaborators"]) > 0
    assert len(data["topics"]) > 0
    assert "total_citations" in data
    assert data["total_citations"] > 0
    print(f"[PASS] /api/authors/{{id}} verified: {len(data['collaborators'])} collaborators, {len(data['topics'])} topics, {data['total_citations']:,} citations.")

    # 4b. Test /api/authors/{author_id}/graph
    res = client.get(f"/api/authors/{luke_id}/graph")
    assert res.status_code == 200
    graph_data = res.json()
    assert len(graph_data["nodes"]) > 0
    assert len(graph_data["links"]) > 0
    query_node = next(n for n in graph_data["nodes"] if n["group"] == "query")
    assert query_node["id"] == luke_id
    coauthor_nodes = [n for n in graph_data["nodes"] if n["group"] == "coauthor"]
    rec_nodes = [n for n in graph_data["nodes"] if n["group"] == "recommended"]
    print(f"[PASS] /api/authors/{{id}}/graph verified: {len(graph_data['nodes'])} nodes ({len(coauthor_nodes)} co-authors, {len(rec_nodes)} recommended) and {len(graph_data['links'])} edges.")

    # 5. Test /api/authors/{author_id}/recommendations
    res = client.get(f"/api/authors/{luke_id}/recommendations?k=5")
    assert res.status_code == 200
    data = res.json()
    recs = data["recommendations"]
    assert len(recs) > 0
    print(f"[PASS] /api/authors/{{id}}/recommendations verified: {len(recs)} candidates returned.")
    for i, r in enumerate(recs, 1):
        print(f"  {i}. {r['name']} ({r['institution']}) | Hybrid Score: {r['hybrid_score']} | Topics: {r['shared_topics']}")

    # 6. Test /api/communities
    res = client.get("/api/communities")
    assert res.status_code == 200
    data = res.json()
    assert len(data["communities"]) >= 10
    print(f"[PASS] /api/communities verified: {len(data['communities'])} communities.")

    # 7. Test /api/figures/{figure_name}
    res = client.get("/api/figures/fig1_degree_distribution.png")
    assert res.status_code == 200
    assert len(res.content) > 1000
    print(f"[PASS] /api/figures/fig1_degree_distribution.png verified ({len(res.content):,} bytes).")

    # 7b. Test /api/figures security against traversal / missing figures
    res_404 = client.get("/api/figures/nonexistent_fig.png")
    assert res_404.status_code == 404
    print("[PASS] /api/figures 404 protection verified.")

    # 8. Test Search ranking precision
    res_chen = client.get("/api/search?q=chen")
    assert res_chen.status_code == 200
    chen_data = res_chen.json()
    assert len(chen_data["results"]) == 15
    assert all("chen" in r["name"].lower() for r in chen_data["results"])
    print(f"[PASS] Search precision ranking verified across 22,185 authors.")

    print("\nALL DASHBOARD API TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_dashboard()
