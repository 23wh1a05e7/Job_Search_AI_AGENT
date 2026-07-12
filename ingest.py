"""
Standalone script to (re)build the ChromaDB vector index from
data/jobs.json. Run this once before starting the app, or any time
you edit jobs.json.

Usage:
    python ingest.py
"""

from src.vector_store import JobVectorStore


def main():
    store = JobVectorStore()
    print("Building vector index from data/jobs.json ...")
    count = store.build_from_json()
    print(f"Done. Indexed {count} job postings into ChromaDB.")


if __name__ == "__main__":
    main()
