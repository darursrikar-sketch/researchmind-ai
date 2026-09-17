#!/usr/bin/env python
"""
Quick entry point to start the ResearchMind AI Web Dashboard.
"""
import os
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from researchmind.web.app import app
from researchmind.config import Config

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "True").lower() in ("true", "1")

    print("\n" + "=" * 65)
    print("  RESEARCHMIND AI - ACADEMIC PAPER ANALYSIS AGENT")
    print("=" * 65)
    print(f"  * Web Server running at: http://{host}:{port}")
    print(f"  * Default Model:         {Config.get_default_model()}")
    print(f"  * Gemini API Key:        {'Configured' if Config.is_api_key_configured() else 'Not configured (Set in Web UI)'}")
    print("=" * 65 + "\n")

    app.run(host=host, port=port, debug=debug)

