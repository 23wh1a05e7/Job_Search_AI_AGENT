"""
Central configuration for the Job Search AI Agent.
All paths and model names are defined here so the rest of the code
never hardcodes them.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
JOBS_JSON_PATH = DATA_DIR / "jobs.json"
CHROMA_DB_DIR = str(BASE_DIR / "chroma_db")
CHROMA_COLLECTION_NAME = "job_postings"

# --- Embedding model (local, free, no API key needed) ---
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# --- LLM (Anthropic Claude) ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "claude-sonnet-4-5-20250929")
LLM_MAX_TOKENS = 2000

# --- Retrieval settings ---
DEFAULT_TOP_K = 5
