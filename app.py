import os
import json
import streamlit as st
import pandas as pd
from agent import process_transcript

# Page Configuration
st.set_page_config(
    page_title="ActionPulse AI — Meeting Notes to Action Items",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for modern aesthetic
st.markdown("""
<style>
    /* Global Styling */
    .main {
        background-color: #0e1117;
        font-family: 'Inter', sans-serif;
    }
    
    /* Header Card */
    .header-card {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        border: 1px solid #374151;
        padding: 24px;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    
    .header-title {
        color: #f9fafb;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .header-subtitle {
        color: #9ca3af;
        font-size: 1.05rem;
    }

    /* Summary Card */
    .summary-box {
        background: rgba(30, 58, 138, 0.2);
        border-left: 4px solid #3b82f6;
        padding: 16px;
        border-radius: 8px;
        color: #e0e7ff;
        font-size: 1rem;
        line-height: 1.6;
        margin-bottom: 20px;
    }

    /* Action Item Card */
    .action-card {
        background-color: #1f2937;
        border: 1px solid #374151;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    .action-card:hover {
        border-color: #3b82f6;
    }

    .action-task {
        font-weight: 600;
        color: #f3f4f6;
        font-size: 1.05rem;
        margin-bottom: 8px;
    }

    .action-meta {
        display: flex;
        gap: 20px;
        color: #9ca3af;
        font-size: 0.9rem;
    }

    .badge-owner {
        background-color: #374151;
        color: #60a5fa;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 500;
    }

    .badge-date {
        background-color: #374151;
        color: #f59e0b;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

if "raw_input" not in st.session_state:
    st.session_state.raw_input = ""

# Helper to load sample files safely
def load_sample(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            st.session_state.raw_input = f.read()
    else:
        st.error(f"Sample file {filename} not found.")

# Sidebar Configuration
with st.sidebar:
    st.image("https://img.icons8.com/isometric-headers/100/flash-on.png", width=64)
    st.title("⚡ ActionPulse AI")
    st.caption("Automated Meeting Insights & Action Extraction")
    st.markdown("---")

    st.subheader("📁 Input Source")
    
    # File Uploader
    uploaded_file = st.file_uploader("Upload transcript file (.txt)", type=["txt"])
    if uploaded_file is not None:
        st.session_state.raw_input = uploaded_file.read().decode("utf-8")
        st.success(f"Loaded `{uploaded_file.name}` successfully!")

    st.markdown("**Or pick a pre-loaded sample:**")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("Sample 1 🚀", help="Product Launch Sync", use_container_width=True):
            load_sample("sample_transcript.txt")
    with col_s2:
        if st.button("Sample 2 💼", help="Q3 Budgeting & Hiring", use_container_width=True):
            load_sample("sample_transcript_2.txt")

    st.markdown("---")

    # API Configuration in Sidebar
    st.subheader("🔑 API Settings")
    
    def _clean(v):
        return v.strip().strip('"').strip("'") if v else ""

    env_key = _clean(os.getenv("OPENAI_API_KEY", ""))
    user_api_key = st.text_input(
        "API Key (OpenAI / OpenRouter / Groq):",
        type="password",
        value=env_key,
        help="Paste your API key here (e.g. Groq key gsk_... or OpenRouter key sk-or-v1-...)."
    )
    
    # Auto-detect defaults based on key type
    default_base = ""
    default_model = "gpt-4o-mini"
    if user_api_key.startswith("gsk_"):
        default_base = "https://api.groq.com/openai/v1"
        default_model = "llama-3.3-70b-versatile"
    elif user_api_key.startswith("sk-or-v1-"):
        default_base = "https://openrouter.ai/api/v1"
        default_model = "meta-llama/llama-3.3-70b-instruct:free"

    env_base_url = _clean(os.getenv("OPENAI_BASE_URL", "")) or default_base
    user_base_url = st.text_input(
        "Base URL (Optional):",
        value=env_base_url,
        placeholder="https://api.groq.com/openai/v1",
        help="Custom API base URL (e.g., https://api.groq.com/openai/v1 or https://openrouter.ai/api/v1)."
    )

    env_model = _clean(os.getenv("LLM_MODEL", "")) or _clean(os.getenv("OPENAI_MODEL", "")) or default_model
    user_model = st.text_input(
        "Model Name:",
        value=env_model,
        placeholder="llama-3.3-70b-versatile",
        help="Specify the model ID (e.g. llama-3.3-70b-versatile, meta-llama/llama-3.3-70b-instruct:free, gpt-4o-mini)."
    )

    if user_api_key:
        st.sidebar.success("✅ API Key configured")
    else:
        st.sidebar.warning("⚠️ API Key missing. Enter it above or set in environment.")

    st.markdown("---")

    if st.button("Clear Chat History", type="secondary", use_container_width=True):
        st.session_state.messages = []
        st.session_state.raw_input = ""
        st.rerun()

# Main Layout Header
st.markdown("""
<div class="header-card">
    <div class="header-title">
        <span>⚡ ActionPulse AI</span>
    </div>
    <div class="header-subtitle">
        Transform raw, unstructured meeting transcripts into concise executive summaries and structured, actionable tasks.
    </div>
</div>
""", unsafe_allow_html=True)

# Render Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(message["content"])
        else:
            data = message.get("result")
            if data:
                st.markdown("### 📌 Executive Summary")
                st.markdown(f'<div class="summary-box">{data.get("summary", "No summary extracted.")}</div>', unsafe_allow_html=True)

                st.markdown("### ✅ Extracted Action Items")
                action_items = data.get("action_items", [])
                if action_items:
                    # Table view option
                    df = pd.DataFrame(action_items)
                    st.dataframe(
                        df, 
                        column_config={
                            "task": st.column_config.TextColumn("Task Description", width="large"),
                            "owner": st.column_config.TextColumn("Assignee / Owner", width="medium"),
                            "due_date": st.column_config.TextColumn("Due Date", width="small"),
                        },
                        hide_index=True,
                        use_container_width=True
                    )

                    # Export JSON
                    json_str = json.dumps(data, indent=2)
                    st.download_button(
                        label="📥 Download action_items.json",
                        data=json_str,
                        file_name="action_items.json",
                        mime="application/json",
                        key=f"dl_{message.get('id', 'default')}"
                    )
                else:
                    st.info("No action items identified in this transcript.")

# Meeting Input Section
st.subheader("📝 Transcript Input")
transcript_text = st.text_area(
    "Paste transcript content or notes below:",
    value=st.session_state.raw_input,
    height=220,
    placeholder="Alex: Good morning team...\nSarah: Morning Alex..."
)

submit_clicked = st.button("⚡ Process & Extract Action Items", type="primary", use_container_width=True)

if submit_clicked:
    if not transcript_text.strip():
        st.warning("Please provide a meeting transcript first.")
    elif not user_api_key and not os.getenv("OPENAI_API_KEY"):
        st.error("Please enter your API key in the sidebar or set the OPENAI_API_KEY environment variable.")
    else:
        # Save user prompt to history
        st.session_state.messages.append({
            "role": "user",
            "content": f"**Analyzed Transcript:**\n\n```text\n{transcript_text[:300]}...\n```"
        })

        with st.spinner("Extracting action items..."):
            try:
                result = process_transcript(
                    transcript_text,
                    api_key=user_api_key if user_api_key else None,
                    base_url=user_base_url if user_base_url else None,
                    model=user_model if user_model else None
                )
                
                # Append assistant response
                msg_id = len(st.session_state.messages)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Analysis complete.",
                    "result": result,
                    "id": msg_id
                })
                st.rerun()

            except Exception as e:
                err_msg = str(e)
                st.error(f"❌ Analysis Failed: {err_msg}")
                st.info(
                    "💡 **Troubleshooting Guide:**\n\n"
                    "1. **Windows Quotes Issue**: In `cmd.exe`, using `set OPENAI_API_KEY=\"key\"` includes literal quotation marks in the environment variable. (Quotes are now automatically stripped by the app!).\n"
                    "2. **OpenRouter Model Name**: OpenRouter requires a specific model ID (e.g. `meta-llama/llama-3.3-70b-instruct:free`, `google/gemini-2.0-flash-lite-001`, or `openai/gpt-4o-mini`).\n"
                    "3. **Base URL**: Ensure Base URL is set to `https://openrouter.ai/api/v1` when using OpenRouter keys."
                )
