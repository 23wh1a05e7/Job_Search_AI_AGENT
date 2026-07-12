"""
Wraps ChromaDB for storing and retrieving job posting embeddings.
This is the "Vector Database" piece that makes RAG possible: instead
of the LLM guessing which jobs exist, we retrieve the actual most
relevant job postings from this store and hand them to the LLM as
grounded context.
"""

import json
import chromadb
from src import config
from src.embeddings import embed_text, embed_texts


class JobVectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=config.CHROMA_DB_DIR)
        self.collection = self.client.get_or_create_collection(
            name=config.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def is_empty(self) -> bool:
        return self.collection.count() == 0

    def build_from_json(self, jobs_json_path=None):
        """
        Reads job postings from jobs.json, embeds each one, and stores
        it in ChromaDB. Safe to re-run (it clears and rebuilds).
        """
        path = jobs_json_path or config.JOBS_JSON_PATH
        with open(path, "r", encoding="utf-8") as f:
            jobs = json.load(f)

        # Clear existing collection so we don't get duplicates on rebuild
        existing_ids = self.collection.get()["ids"]
        if existing_ids:
            self.collection.delete(ids=existing_ids)

        documents = []
        metadatas = []
        ids = []

        for job in jobs:
            # Combine the fields that matter semantically into one
            # text blob so the embedding captures title + skills + description.
            searchable_text = (
                f"Title: {job['title']}\n"
                f"Company: {job['company']}\n"
                f"Location: {job['location']}\n"
                f"Experience required: {job['experience_required']}\n"
                f"Skills: {', '.join(job['skills'])}\n"
                f"Description: {job['description']}"
            )
            documents.append(searchable_text)
            metadatas.append(
                {
                    "id": job["id"],
                    "title": job["title"],
                    "company": job["company"],
                    "location": job["location"],
                    "experience_required": job["experience_required"],
                    "salary_range": job.get("salary_range", "Not disclosed"),
                    "employment_type": job.get("employment_type", "Full-time"),
                    "skills": ", ".join(job["skills"]),
                    "description": job["description"],
                }
            )
            ids.append(job["id"])

        vectors = embed_texts(documents)

        self.collection.add(
            ids=ids,
            embeddings=vectors,
            documents=documents,
            metadatas=metadatas,
        )
        return len(jobs)

    def search(self, query: str, top_k: int = None) -> list:
        """
        Embeds the query and retrieves the top_k most similar jobs.
        Returns a list of dicts with metadata + similarity score.
        """
        top_k = top_k or config.DEFAULT_TOP_K
        query_vector = embed_text(query)

        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
        )

        jobs = []
        if not results["ids"] or not results["ids"][0]:
            return jobs

        for i in range(len(results["ids"][0])):
            metadata = results["metadatas"][0][i]
            distance = results["distances"][0][i]
            # Cosine distance -> similarity score (0-1, higher is better)
            similarity = round(max(0.0, 1 - distance), 3)
            jobs.append({**metadata, "match_score": similarity})

        return jobs

    def get_by_id(self, job_id: str) -> dict:
        """Fetch a single job's full metadata by its id."""
        result = self.collection.get(ids=[job_id])
        if not result["ids"]:
            return None
        return result["metadatas"][0]
