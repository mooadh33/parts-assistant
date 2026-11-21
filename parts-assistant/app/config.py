import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DOCS_DIR = DATA / "docs"
PARTS_DB = DATA / "parts.db"
USAGE_DB = DATA / "usage.db"
CHROMA_DIR = DATA / "chroma"

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "claude-sonnet-4-5")
CHEAP_MODEL = os.getenv("CHEAP_MODEL", "claude-haiku-4-5")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "20"))
USERS = dict(u.split(":", 1) for u in os.getenv("APP_USERS", "admin:admin123,tester1:test123").split(","))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "600"))      # words
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "80"))
TOP_K = int(os.getenv("TOP_K", "4"))

# USD per 1M tokens (input, output). Verify against current provider pricing before quoting numbers.
PRICING = {
    "claude-sonnet-4-5": (3.0, 15.0),
    "claude-haiku-4-5": (1.0, 5.0),
    "gpt-4o": (2.5, 10.0),
    "gpt-4o-mini": (0.15, 0.6),
    "mock": (0.0, 0.0),
}
