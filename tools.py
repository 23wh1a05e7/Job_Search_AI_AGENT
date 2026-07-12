"""
Defines the tools the agent can call. This is what makes the system
"agentic" rather than plain RAG: the LLM decides WHICH of these
functions to call and WITH WHAT arguments, based on the user's
message and the conversation so far.

Each tool has:
  1. A JSON schema description (so Claude knows it exists and how to call it)
  2. A Python function that actually executes it

The agent.py loop wires these together.
"""

from src.vector_store import JobVectorStore

# Single shared vector store instance used by all tools
_vector_store = JobVectorStore()


# ---------------------------------------------------------------------
# 1. Tool schemas (given to Claude so it knows what it can call)
# ---------------------------------------------------------------------

TOOL_SCHEMAS = [
    {
        "name": "search_jobs",
        "description": (
            "Search the job postings vector database for jobs relevant to a "
            "query. Use this whenever the user asks to find jobs, or when you "
            "need to look up jobs matching the candidate's resume/skills. "
            "Returns a ranked list of jobs with a match_score (0-1, higher is better)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "A natural language description of the jobs to search for, "
                        "e.g. 'remote Python backend developer with 2 years experience' "
                        "or the candidate's resume summary."
                    ),
                },
                "top_k": {
                    "type": "integer",
                    "description": "How many jobs to retrieve. Default 5.",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_job_details",
        "description": (
            "Fetch the full details of a single job posting by its job id "
            "(e.g. 'job_005'). Use this when the user asks about a specific "
            "job that was already retrieved, and you need its full description."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "The id of the job, e.g. 'job_005'.",
                }
            },
            "required": ["job_id"],
        },
    },
]


# ---------------------------------------------------------------------
# 2. Tool implementations (the actual Python logic)
# ---------------------------------------------------------------------

def tool_search_jobs(query: str, top_k: int = 5) -> dict:
    """Runs a vector similarity search against the job postings DB."""
    results = _vector_store.search(query=query, top_k=top_k)
    return {"jobs_found": len(results), "jobs": results}


def tool_get_job_details(job_id: str) -> dict:
    """Fetches one job's full metadata by id."""
    job = _vector_store.get_by_id(job_id)
    if job is None:
        return {"error": f"No job found with id '{job_id}'"}
    return job


# Maps tool name (as Claude will call it) -> Python function
TOOL_DISPATCH = {
    "search_jobs": lambda tool_input: tool_search_jobs(
        query=tool_input["query"], top_k=tool_input.get("top_k", 5)
    ),
    "get_job_details": lambda tool_input: tool_get_job_details(
        job_id=tool_input["job_id"]
    ),
}


def ensure_index_built():
    """Build the vector index from jobs.json if it hasn't been built yet."""
    if _vector_store.is_empty():
        count = _vector_store.build_from_json()
        return count
    return _vector_store.collection.count()


def get_vector_store() -> JobVectorStore:
    return _vector_store
