import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root or user home
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Supported models
AVAILABLE_MODELS = [
    {
        "id": "gemini-3.5-flash",
        "name": "Gemini 3.5 Flash",
        "desc": "Ultra-fast, balanced reasoning & agentic execution (Recommended)",
        "default": True,
    },
    {
        "id": "gemini-3.5-flash-lite",
        "name": "Gemini 3.5 Flash Lite",
        "desc": "Ultra-low latency & responsive for quick summaries",
        "default": False,
    },
    {
        "id": "gemini-3.6-flash",
        "name": "Gemini 3.6 Flash",
        "desc": "Balanced performance and high context reasoning",
        "default": False,
    },
    {
        "id": "gemini-3.8-flash",
        "name": "Gemini 3.8 Flash",
        "desc": "Advanced reasoning & deep synthesis",
        "default": False,
    },
]

# Serverless / Vercel detection: Vercel defines VERCEL=1 or VERCEL_ENV in env
IS_VERCEL = os.environ.get("VERCEL") == "1" or "VERCEL" in os.environ

if IS_VERCEL:
    DATA_DIR = Path("/tmp/data")
    UPLOAD_DIR = DATA_DIR / "uploads"
    DB_PATH = DATA_DIR / "researchmind.db"
else:
    DATA_DIR = BASE_DIR / "data"
    UPLOAD_DIR = DATA_DIR / "uploads"
    DB_PATH = DATA_DIR / "researchmind.db"

# Ensure data directories exist safely
try:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    pass


class Config:
    @staticmethod
    def get_api_key() -> str:
        """Get the Gemini API key from environment or .env file."""
        return os.environ.get("GEMINI_API_KEY", "").strip()

    @staticmethod
    def set_api_key(api_key: str, persist: bool = True):
        """Set the Gemini API key for the current process and optionally persist to .env."""
        api_key = api_key.strip()
        os.environ["GEMINI_API_KEY"] = api_key

        if persist:
            try:
                env_path = BASE_DIR / ".env"
                lines = []
                key_updated = False
                if env_path.exists():
                    with open(env_path, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.startswith("GEMINI_API_KEY="):
                                lines.append(f"GEMINI_API_KEY={api_key}\n")
                                key_updated = True
                            else:
                                lines.append(line)
                if not key_updated:
                    lines.append(f"GEMINI_API_KEY={api_key}\n")
                with open(env_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)
            except OSError:
                pass

    @staticmethod
    def get_default_model() -> str:
        return os.environ.get("GEMINI_MODEL", "gemini-3.5-flash").strip()

    @staticmethod
    def set_default_model(model_name: str):
        os.environ["GEMINI_MODEL"] = model_name

    @staticmethod
    def is_api_key_configured() -> bool:
        key = Config.get_api_key()
        return bool(key and key != "your_gemini_api_key_here")


def get_genai_client(api_key: str | None = None):
    """
    Returns an initialized google.genai.Client instance.
    Raises ValueError if API key is not configured.
    """
    from google import genai

    key = api_key or Config.get_api_key()
    if not key or key == "your_gemini_api_key_here":
        raise ValueError(
            "Gemini API key is not configured. Please set GEMINI_API_KEY in your .env file "
            "or enter it in the Web UI / CLI."
        )
    return genai.Client(api_key=key)

