"""
Update script to cleanly patch and synchronize dashboard files:
- src/dashboard/app.py
- src/dashboard/index.html
- run_dashboard.bat
"""
import os
import re

APP_PY = os.path.join("src", "dashboard", "app.py")
INDEX_HTML = os.path.join("src", "dashboard", "index.html")
RUN_BAT = "run_dashboard.bat"

# 1. Read app.py
with open(APP_PY, "r", encoding="utf-8") as f:
    text = f.read()

# Fix 1: syntax error }}}; -> }};
text = text.replace("}]}}};", "}]}};")

# Fix 2: c.leading_authors -> (c.leading_authors || c.leading_researchers || [])
text = text.replace("c.leading_authors.join", "(c.leading_authors || c.leading_researchers || []).join")
text = text.replace("c.core_topics.join", "(c.core_topics || []).join")
text = text.replace("(c.size || 0)", "(c.size || c.author_count || 0)")

# Fix 3: physics link attraction spring vector sign
# Both were += fx, += fy which propelled linked nodes away together instead of attracting
text = re.sub(
    r"if \(!u\.fixed\) \{ u\.vx \+= fx; u\.vy \+= fy; \}\s*if \(!v\.fixed\) \{ v\.vx \+= fx; v\.vy \+= fy; \}",
    "if (!u.fixed) { u.vx += fx; u.vy += fy; }\n          if (!v.fixed) { v.vx -= fx; v.vy -= fy; }",
    text
)

# Fix 4: initGraphLayout must call renderSvg()
text = re.sub(
    r"runPhysicsSimulation\(\);\s*autoFitGraph\(\);",
    "runPhysicsSimulation();\n      renderSvg();\n      autoFitGraph();",
    text
)

# Fix 5: SVG element width/height
text = text.replace('<svg id="networkSvg">', '<svg id="networkSvg" width="100%" height="100%">')

# Fix 6: Safe queryNode lookup in loadAuthor
text = text.replace(
    "const queryNode = (data.nodes || []).find(n => n.group === 'query') || data.nodes[0];",
    "const queryNode = (data.nodes && data.nodes.length > 0) ? (data.nodes.find(n => n.group === 'query') || data.nodes[0]) : null;"
)

# Write patched app.py
with open(APP_PY, "w", encoding="utf-8") as f:
    f.write(text)
print("[OK] Patched src/dashboard/app.py successfully.")

# Extract HTML_PAGE from app.py to overwrite src/dashboard/index.html
m = re.search(r'HTML_PAGE\s*=\s*r?"""(.*?)"""\s*@app\.get\(', text, re.DOTALL)
if m:
    html_content = m.group(1).strip()
    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(html_content + "\n")
    print(f"[OK] Overwrote src/dashboard/index.html with updated HTML ({len(html_content)} bytes).")
else:
    print("[WARN] Could not find HTML_PAGE delimiter in app.py")

# Update run_dashboard.bat to ensure cd and PYTHONPATH are always set
run_bat_content = """@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0;%PYTHONPATH%
echo ==============================================================
echo   ScholarlyKG - Research Collaboration Analytics Dashboard
echo ==============================================================
echo Starting server on http://127.0.0.1:8000 ...
python "%~dp0run_dashboard.py"
pause
"""
with open(RUN_BAT, "w", encoding="utf-8") as f:
    f.write(run_bat_content)
print("[OK] Updated run_dashboard.bat with working directory and PYTHONPATH.")

# Verify JS syntax
import subprocess
for fname in [APP_PY, INDEX_HTML]:
    with open(fname, "r", encoding="utf-8") as f:
        content = f.read()
    p1 = content.find("<script>")
    p2 = content.find("</script>")
    js_code = content[p1+8:p2]
    tmp_name = "temp_syntax_check.js"
    with open(tmp_name, "w", encoding="utf-8") as f:
        f.write(js_code)
    res = subprocess.run(["node", "-c", tmp_name], capture_output=True, text=True)
    if res.returncode == 0:
        print(f"[VERIFIED] {fname}: JS syntax is 100% CLEAN and VALID!")
    else:
        print(f"[ERROR] {fname} JS syntax error:\n{res.stderr}")

