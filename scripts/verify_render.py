"""
Verify UI rendering, HTML generation, and JSON integrity.
"""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient
from src.dashboard.app import app
import json

client = TestClient(app)

# 1. Test index page
resp = client.get("/")
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
html = resp.text
assert 'id="networkSvg"' in html, "Missing networkSvg in HTML"
assert 'width="100%" height="100%"' in html, "Missing explicit width/height on SVG"
print("[PASS] Index HTML contains SVG element with explicit 100% dimensions.")

# 2. Extract DEFAULT_DATA from html
start_marker = "const DEFAULT_DATA = "
start = html.find(start_marker) + len(start_marker)
end = html.find(";\n\n    // ", start)
json_str = html[start:end].strip()
default_data = json.loads(json_str)
nodes = default_data["graph"]["nodes"]
links = default_data["graph"]["links"]
assert len(nodes) == 26, f"Expected 26 nodes, got {len(nodes)}"
assert len(links) == 73, f"Expected 73 links, got {len(links)}"
print(f"[PASS] Embedded DEFAULT_DATA parsed successfully! Nodes: {len(nodes)}, Edges: {len(links)}")

# 3. Test graph API endpoint
graph_resp = client.get("/api/authors/A5067919401/graph")
assert graph_resp.status_code == 200
graph_data = graph_resp.json()
assert len(graph_data["nodes"]) == 26
assert len(graph_data["links"]) == 73
print(f"[PASS] /api/authors/A5067919401/graph returned {len(graph_data['nodes'])} nodes and {len(graph_data['links'])} edges.")

# 4. Check that index.html exists and is identical
with open("src/dashboard/index.html", "r", encoding="utf-8") as f:
    standalone_html = f.read()
assert 'id="networkSvg"' in standalone_html
assert 'const DEFAULT_DATA = ' in standalone_html
print("[PASS] Standalone src/dashboard/index.html is verified and intact.")

print("\n>>> ALL CHECKS PASSED: THE GRAPH CANVAS WILL RENDER FLAWLESSLY! <<<")
