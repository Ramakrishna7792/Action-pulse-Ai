import os
import json
import uuid
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

# Custom Styling for Gemini-inspired Dark Theme
st.markdown("""
<style>
    /* Main Container */
    .stApp {
        background-color: #131314;
        color: #e3e3e3;
        font-family: 'Google Sans', 'Inter', sans-serif;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #1e1f20;
        border-right: 1px solid #2e2f31;
    }

    /* Gemini-style Sidebar Buttons */
    [data-testid="stSidebar"] button[kind="secondary"] {
        background-color: transparent !important;
        border: none !important;
        color: #c4c7c5 !important;
        text-align: left !important;
        justify-content: flex-start !important;
        font-size: 0.9rem !important;
        border-radius: 8px !important;
        padding: 6px 10px !important;
    }
    
    [data-testid="stSidebar"] button[kind="primary"] {
        background-color: #282a2c !important;
        border: 1px solid #374151 !important;
        color: #ffffff !important;
        text-align: left !important;
        justify-content: flex-start !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        padding: 6px 10px !important;
    }

    [data-testid="stSidebar"] button:hover {
        background-color: #2e3034 !important;
        color: #ffffff !important;
    }

    /* Popover Menu Styling */
    [data-testid="stPopover"] button {
        background: transparent !important;
        border: none !important;
        color: #9ca3af !important;
        padding: 2px 6px !important;
    }
    [data-testid="stPopover"] button:hover {
        color: #ffffff !important;
    }

    /* Header Card */
    .header-card {
        background: linear-gradient(135deg, #1e2022 0%, #17181a 100%);
        border: 1px solid #2e3034;
        padding: 20px 24px;
        border-radius: 16px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
    }
    
    .header-title {
        color: #f3f4f6;
        font-size: 1.8rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 6px;
    }
    
    .header-subtitle {
        color: #9ca3af;
        font-size: 0.95rem;
    }

    /* Executive Summary Box */
    .summary-box {
        background: rgba(37, 99, 235, 0.15);
        border-left: 4px solid #3b82f6;
        padding: 16px 20px;
        border-radius: 10px;
        color: #dbeafe;
        font-size: 0.98rem;
        line-height: 1.6;
        margin-bottom: 16px;
    }

    /* Sidebar Headings */
    .recent-header {
        font-size: 0.8rem;
        font-weight: 600;
        color: #8e918f;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 14px;
        margin-bottom: 6px;
    }

    /* Hide default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

def _clean(v):
    return v.strip().strip('"').strip("'") if v else ""

# Initialize State Management
if "chats" not in st.session_state:
    initial_id = str(uuid.uuid4())
    st.session_state.chats = {
        initial_id: {
            "title": "New Chat",
            "messages": [],
            "pinned": False
        }
    }
    st.session_state.current_chat_id = initial_id

if "api_key" not in st.session_state:
    st.session_state.api_key = _clean(os.getenv("OPENAI_API_KEY", ""))

if "base_url" not in st.session_state:
    st.session_state.base_url = _clean(os.getenv("OPENAI_BASE_URL", ""))

if "model_name" not in st.session_state:
    st.session_state.model_name = _clean(os.getenv("LLM_MODEL", "")) or _clean(os.getenv("OPENAI_MODEL", ""))

if "search_query" not in st.session_state:
    st.session_state.search_query = ""

# Helper to create a new chat thread
def start_new_chat():
    new_id = str(uuid.uuid4())
    st.session_state.chats[new_id] = {
        "title": "New Chat",
        "messages": [],
        "pinned": False
    }
    st.session_state.current_chat_id = new_id

# Ensure active chat exists
if st.session_state.current_chat_id not in st.session_state.chats:
    start_new_chat()

current_chat = st.session_state.chats[st.session_state.current_chat_id]

# SIDEBAR (Gemini AI Layout)
with st.sidebar:
    # 1. Header (No broken image icon)
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 2px;">
            <span style="font-size: 1.6rem;">⚡</span>
            <span style="font-size: 1.35rem; font-weight: 700; color: #f9fafb;">ActionPulse AI</span>
        </div>
        <div style="color: #9ca3af; font-size: 0.82rem; margin-bottom: 16px;">
            Automated Meeting Insights & Action Extraction
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # 2. New Chat Button
    if st.button("📝 New chat", use_container_width=True, type="primary"):
        start_new_chat()
        st.rerun()

    # 3. Search Chats
    search_input = st.text_input("🔍 Search chats", value=st.session_state.search_query, placeholder="Filter conversations...")
    st.session_state.search_query = search_input

    # 4. Pinned & Recents Lists (Only show chats that have messages)
    chat_items = list(st.session_state.chats.items())
    filtered_chats = [
        (cid, cdata) for cid, cdata in chat_items
        if len(cdata.get("messages", [])) > 0 and (not search_input.strip() or search_input.lower() in cdata["title"].lower())
    ]

    pinned_chats = [(cid, cdata) for cid, cdata in filtered_chats if cdata.get("pinned", False)]
    recent_chats = [(cid, cdata) for cid, cdata in filtered_chats if not cdata.get("pinned", False)]

    def render_chat_item(cid, cdata):
        is_active = (cid == st.session_state.current_chat_id)
        is_pinned = cdata.get("pinned", False)
        title = cdata["title"]

        col_title, col_opts = st.columns([0.82, 0.18])
        with col_title:
            btn_type = "primary" if is_active else "secondary"
            if st.button(title, key=f"nav_{cid}", use_container_width=True, type=btn_type):
                st.session_state.current_chat_id = cid
                st.rerun()

        with col_opts:
            with st.popover("⋮", help="Options"):
                # Pin / Unpin Option
                pin_action = "Unpin" if is_pinned else "Pin"
                if st.button(f"📌 {pin_action}", key=f"pin_act_{cid}", use_container_width=True):
                    cdata["pinned"] = not is_pinned
                    st.rerun()

                # Rename Form Option
                with st.form(key=f"rename_form_{cid}"):
                    new_t = st.text_input("Rename:", value=title)
                    if st.form_submit_button("✏️ Save"):
                        if new_t.strip():
                            cdata["title"] = new_t.strip()
                            st.rerun()

                # Delete Option
                if st.button("🗑️ Delete", key=f"del_act_{cid}", use_container_width=True):
                    del st.session_state.chats[cid]
                    if not st.session_state.chats:
                        start_new_chat()
                    else:
                        st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
                    st.rerun()

    # Render Pinned Section
    if pinned_chats:
        st.markdown('<div class="recent-header">Pinned</div>', unsafe_allow_html=True)
        for cid, cdata in reversed(pinned_chats):
            render_chat_item(cid, cdata)

    # Render Recents Section
    st.markdown('<div class="recent-header">Recents</div>', unsafe_allow_html=True)
    if recent_chats:
        for cid, cdata in reversed(recent_chats):
            render_chat_item(cid, cdata)
    else:
        st.caption("No recent conversations.")

    st.markdown("---")

    # 5. Settings Popover / Expander at Left Bottom
    with st.expander("⚙️ Settings", expanded=False):
        tab_app, tab_api, tab_fb, tab_about = st.tabs(["Appearance", "API Keys", "Feedback", "About Us"])

        with tab_app:
            st.write("**Theme:** Dark Mode 🌙")
            st.caption("Matches Gemini-style modern dark aesthetics.")

        with tab_api:
            st.markdown("#### API Configuration")
            new_key = st.text_input("API Key:", value=st.session_state.api_key, type="password", help="OpenAI, Groq (gsk_...), or OpenRouter (sk-or-v1-...) key")
            new_url = st.text_input("Base URL (Optional):", value=st.session_state.base_url, placeholder="https://api.groq.com/openai/v1")
            new_model = st.text_input("Model Name:", value=st.session_state.model_name, placeholder="llama-3.3-70b-versatile")

            if st.button("Save Credentials", key="save_creds_btn", use_container_width=True):
                st.session_state.api_key = _clean(new_key)
                st.session_state.base_url = _clean(new_url)
                st.session_state.model_name = _clean(new_model)
                st.success("API Settings saved!")
                st.rerun()

        with tab_fb:
            st.markdown("#### Send Feedback")
            fb_text = st.text_area("How can we improve ActionPulse AI?", height=80)
            if st.button("Submit Feedback", key="submit_fb_btn"):
                if fb_text.strip():
                    st.success("Thank you for your feedback!")

        with tab_about:
            st.markdown("#### ActionPulse AI v2.0")
            st.write("Executes executive summaries and extracts structured action items from transcripts, notes, and paragraphs.")

# MAIN CONTENT AREA

# 1. Header Card
st.markdown("""
<div class="header-card">
    <div class="header-title">
        <span>⚡ ActionPulse AI</span>
    </div>
    <div class="header-subtitle">
        Transform raw, unstructured meeting transcripts, notes, or paragraphs into concise executive summaries and structured action items.
    </div>
</div>
""", unsafe_allow_html=True)

# 2. Render Active Chat Messages
messages = current_chat["messages"]

for message in messages:
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

                    json_str = json.dumps(data, indent=2)
                    st.download_button(
                        label="📥 Download action_items.json",
                        data=json_str,
                        file_name="action_items.json",
                        mime="application/json",
                        key=f"dl_{message.get('id', uuid.uuid4())}"
                    )
                else:
                    st.info("No action items identified in this text.")

import pypdf
import docx

def extract_file_data(uploaded_file):
    name = uploaded_file.name.lower()
    if name.endswith((".txt", ".md")):
        return uploaded_file.read().decode("utf-8", errors="ignore"), None, None
    elif name.endswith(".pdf"):
        reader = pypdf.PdfReader(uploaded_file)
        text = "\n".join([page.extract_text() or "" for page in reader.pages])
        return text, None, None
    elif name.endswith(".docx"):
        doc = docx.Document(uploaded_file)
        text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        return text, None, None
    elif name.endswith((".png", ".jpg", ".jpeg", ".webp")):
        mime = "image/jpeg" if name.endswith((".jpg", ".jpeg")) else "image/png"
        if name.endswith(".webp"):
            mime = "image/webp"
        return None, uploaded_file.read(), mime
    return uploaded_file.read().decode("utf-8", errors="ignore"), None, None

# 3. File Attachment Bar (Supports TXT, PDF, DOCX, PNG, JPG, WEBP)
with st.expander("➕ Upload File (.txt, .pdf, .docx, .png, .jpg)", expanded=False):
    uploaded_file = st.file_uploader(
        "Attach meeting document, transcript, or notes image:",
        type=["txt", "md", "pdf", "docx", "png", "jpg", "jpeg", "webp"],
        key=f"file_up_{st.session_state.current_chat_id}"
    )
    file_text, file_img_bytes, file_img_mime = None, None, None
    if uploaded_file is not None:
        file_text, file_img_bytes, file_img_mime = extract_file_data(uploaded_file)
        st.success(f"Attached `{uploaded_file.name}`. Press Enter or click submit in the chat box below.")

# 4. Gemini-Style Chat Input Box (Works with Enter key or Submit button ➔)
user_prompt = st.chat_input("Enter a meeting transcript, raw notes, or paragraph text...")

# Determine payload
has_file = (file_text is not None or file_img_bytes is not None)
text_to_process = file_text if (has_file and not user_prompt) else user_prompt
img_bytes_to_process = file_img_bytes if (has_file and not user_prompt) else None

if text_to_process or img_bytes_to_process:
    active_key = st.session_state.api_key or os.getenv("OPENAI_API_KEY")
    if not active_key:
        st.error("Please configure your API Key in Settings (⚙️ bottom left of sidebar) before processing.")
    else:
        # Update Chat Title based on first message
        if not messages or current_chat["title"] == "New Chat":
            if text_to_process:
                preview_title = text_to_process.strip().split("\n")[0][:26]
            else:
                preview_title = f"Image ({uploaded_file.name[:20]})"
            current_chat["title"] = preview_title if preview_title else "Transcript Analysis"

        # Append User Message
        if text_to_process:
            user_msg = f"**Submitted Text:**\n\n```text\n{text_to_process[:400]}{'...' if len(text_to_process)>400 else ''}\n```"
        else:
            user_msg = f"📷 **Uploaded Image Document:** `{uploaded_file.name}`"

        messages.append({
            "role": "user",
            "content": user_msg
        })

        with st.spinner("Extracting action items..."):
            try:
                result = process_transcript(
                    transcript_text=text_to_process,
                    api_key=st.session_state.api_key if st.session_state.api_key else None,
                    base_url=st.session_state.base_url if st.session_state.base_url else None,
                    model=st.session_state.model_name if st.session_state.model_name else None,
                    image_bytes=img_bytes_to_process,
                    image_mime=file_img_mime if file_img_mime else "image/png"
                )

                messages.append({
                    "role": "assistant",
                    "content": "Analysis complete.",
                    "result": result,
                    "id": str(uuid.uuid4())
                })
                st.rerun()

            except Exception as e:
                err_msg = str(e)
                st.error(f"❌ Analysis Failed: {err_msg}")
