import sys
from pathlib import Path

# Add project root to sys.path so researchmind package is importable
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from researchmind.web.app import app

# Vercel's Python serverless runtime looks for an ASGI or WSGI variable named 'app'
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
