"""
Streamlit UI for the Job Search AI Agent.

Flow:
  1. User uploads a resume (PDF or TXT) or types their profile/query
  2. User chats with the agent: "find me jobs", "why is job_005 a good
     match", "draft a cover letter for job_002", etc.
  3. The agent (src/agent.py) decides which tools to call, retrieves
     jobs from the vector DB (src/vector_store.py), and reasons over
     them with the LLM.
"""

import streamlit as st
from src.tools import ensure_index_built
from src.resume_parser import extract_text_from_upload
from src.agent import run_agent_turn

st.set_page_config(page_title="Job Search AI Agent", page_icon="🧭", layout="wide")

# ---------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------
if "chat_display" not in st.session_state:
    st.session_state.chat_display = []  # what's shown in the UI: [(role, text)]
if "agent_history" not in st.session_state:
    st.session_state.agent_history = []  # raw message history passed to Claude
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "index_ready" not in st.session_state:
    with st.spinner("Building job vector index (first run only)..."):
        job_count = ensure_index_built()
    st.session_state.index_ready = True
    st.session_state.job_count = job_count


# ---------------------------------------------------------------------
# Sidebar: resume upload + info
# ---------------------------------------------------------------------
with st.sidebar:
    st.header("📄 Your Resume")
    uploaded_file = st.file_uploader("Upload resume (PDF or TXT)", type=["pdf", "txt"])

    if uploaded_file is not None:
        if st.button("Load resume into agent"):
            with st.spinner("Extracting resume text..."):
                text = extract_text_from_upload(uploaded_file)
            st.session_state.resume_text = text
            st.success(f"Resume loaded ({len(text)} characters).")

    if st.session_state.resume_text:
        with st.expander("View extracted resume text"):
            st.text_area("Resume text", st.session_state.resume_text, height=200)

    st.divider()
    st.caption(f"📊 Indexed jobs in vector DB: **{st.session_state.job_count}**")

    st.divider()
    st.header("💡 Try asking")
    st.markdown(
        "- *Find jobs matching my resume*\n"
        "- *Show me remote Python jobs for freshers*\n"
        "- *Why is job_005 a good match for me?*\n"
        "- *What skills am I missing for job_011?*\n"
        "- *Draft a cover letter for job_002*"
    )

    st.divider()
    if st.button("🔄 Reset conversation"):
        st.session_state.chat_display = []
        st.session_state.agent_history = []
        st.rerun()


# ---------------------------------------------------------------------
# Main chat area
# ---------------------------------------------------------------------
st.title("🧭 Job Search AI Agent")
st.caption(
    "An agentic RAG system: retrieves real job postings from a vector "
    "database, then reasons over them with an LLM to match, explain, "
    "and draft — instead of just listing search results."
)

# Render existing chat history
for role, text in st.session_state.chat_display:
    with st.chat_message(role):
        st.markdown(text)

user_input = st.chat_input("Ask about jobs, matches, skill gaps, or cover letters...")

if user_input:
    # If resume text is loaded but not yet mentioned, quietly prepend it
    # as context on the first message so the agent has it available.
    effective_message = user_input
    if st.session_state.resume_text and len(st.session_state.agent_history) == 0:
        effective_message = (
            f"My resume content is below. Use it as my profile for all "
            f"future job matching in this conversation.\n\n"
            f"--- RESUME START ---\n{st.session_state.resume_text}\n--- RESUME END ---\n\n"
            f"My request: {user_input}"
        )

    st.session_state.chat_display.append(("user", user_input))
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking and searching jobs..."):
            try:
                result = run_agent_turn(
                    conversation_history=st.session_state.agent_history,
                    user_message=effective_message,
                )
                reply = result["reply"]
                st.session_state.agent_history = result["updated_history"]

                # Show tool calls transparently (great for a project demo/viva)
                if result["tool_trace"]:
                    with st.expander("🔧 Agent reasoning trace (tools used)"):
                        for step in result["tool_trace"]:
                            st.markdown(f"**Tool:** `{step['tool']}`")
                            st.json(step["input"])
                            st.markdown("**Result:**")
                            st.code(str(step["result"])[:2000])

                st.markdown(reply)
                st.session_state.chat_display.append(("assistant", reply))

            except RuntimeError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Something went wrong: {e}")
