import streamlit as st
from langgraph_tool_backend import chatbot, retrieve_all_threads
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import uuid

# =========================== Page Configuration ===========================
st.set_page_config(
    page_title="AI Workspace",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================== Ultra-Clean CSS ===========================
st.markdown("""
<style>
    /* Tighten top/bottom page padding to maximize screen real estate */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 5rem !important;
        max-width: 840px !important;
        margin: 0 auto;
    }

    /* Hide default Streamlit header/footer clutter */
    header[data-testid="stHeader"] {
        background: transparent;
    }
    footer {visibility: hidden;}

    /* Sidebar compact & sleek styling */
    [data-testid="stSidebar"] {
        background-color: #111318;
        border-right: 1px solid #262932;
    }
    [data-testid="stSidebar"] .block-container {
        padding-top: 1.2rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }

    /* Left-align sidebar thread buttons & truncate long prompts cleanly */
    [data-testid="stSidebar"] .stButton button {
        justify-content: flex-start !important;
        text-align: left !important;
        padding: 0.45rem 0.75rem !important;
        border-radius: 8px !important;
        font-size: 0.88rem !important;
        font-weight: 400 !important;
        border: 1px solid transparent !important;
        background-color: transparent !important;
        color: #c9d1d9 !important;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        margin-bottom: 2px;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background-color: #1f242d !important;
        color: #ffffff !important;
    }

    /* Highlight the active conversation button */
    [data-testid="stSidebar"] .stButton button[kind="primary"] {
        background-color: #232834 !important;
        border: 1px solid #383e4e !important;
        color: #ffffff !important;
        font-weight: 500 !important;
    }

    /* Chat message spacing & clean bubbles */
    [data-testid="stChatMessage"] {
        padding: 0.85rem 1rem;
        border-radius: 12px;
        margin-bottom: 0.6rem;
        background-color: #161920;
        border: 1px solid #232732;
    }

    /* Compact tool status bar */
    .stStatus {
        border-radius: 8px;
        border: 1px solid #2d3340;
        background-color: #1a1e26;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# =========================== Utilities ===========================
def generate_thread_id():
    return str(uuid.uuid4())

def load_conversation(thread_id):
    try:
        state = chatbot.get_state(config={"configurable": {"thread_id": thread_id}})
        return state.values.get("messages", [])
    except Exception:
        return []

def get_thread_title(thread_id):
    """Fetches and caches the first user prompt as the conversation title."""
    if thread_id in st.session_state["thread_titles"]:
        return st.session_state["thread_titles"][thread_id]
    
    messages = load_conversation(thread_id)
    for msg in messages:
        if isinstance(msg, HumanMessage) and msg.content:
            clean_text = " ".join(str(msg.content).split())
            title = clean_text[:34] + ("…" if len(clean_text) > 34 else "")
            st.session_state["thread_titles"][thread_id] = title
            return title
            
    return "New Chat"

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state["thread_id"] = thread_id
    add_thread(thread_id)
    st.session_state["message_history"] = []

def add_thread(thread_id):
    tid_str = str(thread_id)
    if tid_str not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(tid_str)

# ======================= Session Initialization ===================
if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "thread_titles" not in st.session_state:
    st.session_state["thread_titles"] = {}

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generate_thread_id()

if "chat_threads" not in st.session_state:
    try:
        raw_threads = retrieve_all_threads()
        st.session_state["chat_threads"] = [str(t) for t in raw_threads]
    except Exception:
        st.session_state["chat_threads"] = []

add_thread(st.session_state["thread_id"])

# ============================ Sidebar ============================
with st.sidebar:
    if st.button("＋  New Chat", use_container_width=True, type="primary"):
        reset_chat()
        st.rerun()

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    st.caption("RECENT CONVERSATIONS")

    for tid in st.session_state["chat_threads"][::-1]:
        title = get_thread_title(tid)
        is_active = (tid == st.session_state["thread_id"])
        btn_type = "primary" if is_active else "secondary"

        if st.button(f"💬  {title}", key=f"thread_{tid}", use_container_width=True, type=btn_type):
            st.session_state["thread_id"] = tid
            messages = load_conversation(tid)

            temp_messages = []
            for msg in messages:
                if isinstance(msg, (HumanMessage, AIMessage)) and msg.content:
                    role = "user" if isinstance(msg, HumanMessage) else "assistant"
                    temp_messages.append({"role": role, "content": msg.content})
            st.session_state["message_history"] = temp_messages
            st.rerun()

# ============================ Main Chat Area ============================
# Minimal empty-state hero (takes zero vertical bloat once chatting starts)
if not st.session_state["message_history"]:
    st.markdown("""
        <div style="text-align: center; padding: 18vh 1rem 2rem 1rem;">
            <h2 style="font-weight: 600; margin-bottom: 0.4rem;">What can I help you with?</h2>
            <p style="color: #8b949e; font-size: 0.95rem;">Ask anything or trigger tools — click the stop button in the input bar anytime to pause generation.</p>
        </div>
    """, unsafe_allow_html=True)

# Render conversation history
for message in st.session_state["message_history"]:
    avatar = "🧑‍💻" if message["role"] == "user" else "✦"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Chat input with native Stop/Pause button during streaming (Streamlit 1.59+)
try:
    user_input = st.chat_input(
        "Ask anything...",
        submit_mode="stop"
    )
except TypeError:
    # Graceful fallback for older Streamlit versions (<1.59)
    user_input = st.chat_input("Ask anything...")

if user_input:
    # Update sidebar title immediately if this is the first message in the thread
    current_tid = st.session_state["thread_id"]
    if current_tid not in st.session_state["thread_titles"]:
        clean_text = " ".join(user_input.split())
        st.session_state["thread_titles"][current_tid] = clean_text[:34] + ("…" if len(clean_text) > 34 else "")

    # Show user message
    st.session_state["message_history"].append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(user_input)

    CONFIG = {
        "configurable": {"thread_id": current_tid},
        "metadata": {"thread_id": current_tid},
        "run_name": "chat_turn",
    }

    # Assistant streaming block
    with st.chat_message("assistant", avatar="✦"):
        status_holder = {"box": None}
        streamed_chunks = []

        def ai_only_stream():
            try:
                for message_chunk, metadata in chatbot.stream(
                    {"messages": [HumanMessage(content=user_input)]},
                    config=CONFIG,
                    stream_mode="messages",
                ):
                    if isinstance(message_chunk, ToolMessage):
                        tool_name = getattr(message_chunk, "name", "tool")
                        if status_holder["box"] is None:
                            status_holder["box"] = st.status(
                                f"🔧 Running `{tool_name}`…", expanded=True
                            )
                        else:
                            status_holder["box"].update(
                                label=f"🔧 Running `{tool_name}`…",
                                state="running",
                                expanded=True,
                            )

                    if isinstance(message_chunk, AIMessage) and message_chunk.content:
                        streamed_chunks.append(message_chunk.content)
                        yield message_chunk.content
            except Exception as e:
                err = f"\n\n⚠️ **Stopped / Error:** `{str(e)}`"
                streamed_chunks.append(err)
                yield err

        ai_message = st.write_stream(ai_only_stream())

        if status_holder["box"] is not None:
            status_holder["box"].update(
                label="✅ Tools completed", state="complete", expanded=False
            )

    # Save response (falls back to partial streamed chunks if user paused mid-stream)
    final_content = ai_message if ai_message else "".join(streamed_chunks)
    if final_content:
        st.session_state["message_history"].append(
            {"role": "assistant", "content": final_content}
        )
        # Refresh sidebar so the new prompt title appears immediately
        st.rerun()