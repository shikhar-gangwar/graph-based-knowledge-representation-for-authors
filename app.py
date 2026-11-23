"""
Root entrypoint and module re-export for ScholarlyKG Dashboard.
Allows running:
  python app.py
  uvicorn app:app --reload
  python run_dashboard.py
"""
import os
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.dashboard.app import app

if __name__ == "__main__":
    from run_dashboard import get_free_port
    import uvicorn
    import webbrowser

    port = get_free_port(8000)
    url = f"http://127.0.0.1:{port}"
    print("=" * 64)
    print("  ScholarlyKG — Research Collaboration Analytics")
    print(f"  Server URL: {url}")
    print("=" * 64)
    import threading
    try:
        threading.Thread(target=webbrowser.open, args=(url,), daemon=True).start()
    except Exception:
        pass
    uvicorn.run(app, host="127.0.0.1", port=port)
