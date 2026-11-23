"""
Direct entrypoint to launch the ScholarlyKG Dashboard from the project root.
"""
import os
import sys
import socket
import webbrowser

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.dashboard.app import app
import uvicorn

def get_free_port(preferred_port=8000):
    for port in [preferred_port, 8001, 8002, 8080, 8888]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except OSError:
                continue
    return preferred_port

if __name__ == "__main__":
    port = get_free_port(8000)
    url = f"http://127.0.0.1:{port}"
    print("=" * 64)
    print("  ScholarlyKG — Research Collaboration Analytics")
    print(f"  Server URL: {url}")
    print("=" * 64)
    print(f"Open your browser at: {url}")
    import threading
    try:
        threading.Thread(target=webbrowser.open, args=(url,), daemon=True).start()
    except Exception:
        pass
    uvicorn.run(app, host="127.0.0.1", port=port)
