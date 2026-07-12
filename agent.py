"""
The agent loop: this is the "Agentic AI" piece.

Instead of one single prompt -> one single response, the agent:
  1. Sends the conversation + tool definitions to Claude
  2. If Claude decides to call a tool (e.g. search_jobs), we run it
  3. We feed the tool's result back to Claude
  4. Claude reasons over the result and either calls another tool
     or gives a final natural-language answer
  5. Repeat until Claude stops calling tools (or we hit a safety limit)

This lets the agent do multi-step reasoning, e.g.:
  "search jobs matching this resume" -> get results ->
  "get full details of job_005" -> reason over it -> answer the user
"""

from src import config
from src.llm_client import get_client
from src.tools import TOOL_SCHEMAS, TOOL_DISPATCH

SYSTEM_PROMPT = """You are a helpful, honest Job Search AI Agent.

You help candidates find relevant jobs, understand how well their resume
matches a job, identify skill gaps, and draft tailored cover letters.

You have access to tools that search a real vector database of job
postings. ALWAYS use the search_jobs tool to find jobs -- never invent
job listings, companies, or salaries that didn't come from a tool result.

When you recommend jobs, ground every claim in the retrieved job data
(title, company, skills, match_score). If the user's resume or query is
vague, ask a clarifying question instead of guessing.

When asked to draft a cover letter or evaluate a match, use get_job_details
first if you don't already have the full job description in context.

Be concise, practical, and honest -- if a match is weak, say so and explain
why, rather than being falsely encouraging.
"""

MAX_AGENT_STEPS = 6  # safety limit to avoid infinite tool-calling loops


def run_agent_turn(conversation_history: list, user_message: str) -> dict:
    """
    Runs one full agent turn (which may involve multiple internal tool
    calls) given the conversation so far and a new user message.

    Returns a dict with:
      - "reply": the final natural language text to show the user
      - "updated_history": the full message history to persist for next turn
      - "tool_trace": a list of (tool_name, tool_input, tool_result) for
                       transparency / debugging in the UI
    """
    client = get_client()

    messages = list(conversation_history) + [
        {"role": "user", "content": user_message}
    ]

    tool_trace = []

    for _ in range(MAX_AGENT_STEPS):
        response = client.messages.create(
            model=config.LLM_MODEL_NAME,
            max_tokens=config.LLM_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )

        # Append Claude's response (may contain text and/or tool_use blocks)
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            # Claude gave a final answer -- extract the text and stop.
            final_text = _extract_text(response.content)
            return {
                "reply": final_text,
                "updated_history": messages,
                "tool_trace": tool_trace,
            }

        # Claude wants to call one or more tools. Execute each requested
        # tool_use block and collect results as tool_result blocks.
        tool_results_content = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            tool_name = block.name
            tool_input = block.input
            tool_fn = TOOL_DISPATCH.get(tool_name)

            if tool_fn is None:
                result_payload = {"error": f"Unknown tool '{tool_name}'"}
            else:
                try:
                    result_payload = tool_fn(tool_input)
                except Exception as exc:
                    result_payload = {"error": str(exc)}

            tool_trace.append(
                {"tool": tool_name, "input": tool_input, "result": result_payload}
            )

            tool_results_content.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result_payload),
                }
            )

        # Feed tool results back to Claude as a user turn, then loop again
        messages.append({"role": "user", "content": tool_results_content})

    # Safety fallback if we hit MAX_AGENT_STEPS without a final answer
    return {
        "reply": (
            "I wasn't able to finish reasoning about this within my step "
            "limit. Could you rephrase or narrow your request?"
        ),
        "updated_history": messages,
        "tool_trace": tool_trace,
    }


def _extract_text(content_blocks) -> str:
    """Pulls the plain text out of Claude's response content blocks."""
    parts = [block.text for block in content_blocks if block.type == "text"]
    return "\n".join(parts).strip()
