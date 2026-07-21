import os
import json
import uuid
import streamlit as st
import pandas as pd
import pypdf
import docx
from agent import process_transcript

# Page Configuration
st.set_page_config(
    page_title="ActionPulse AI — Meeting Notes to Action Items",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Dark Theme"

if "search_query" not in st.session_state:
    st.session_state.search_query = ""

# Inject Dynamic CSS Theme (Light / Dark)
if st.session_state.theme_mode == "Light Theme":
    theme_css = """
    .stApp {
        background-color: #f8fafc;
        color: #0f172a;
        font-family: 'Google Sans', 'Inter', sans-serif;
    }
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    .header-card {
        background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
        border: 1px solid #cbd5e1;
        padding: 20px 24px;
        border-radius: 16px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    }
    .header-title { color: #0f172a; }
    .header-subtitle { color: #64748b; }
    .summary-box {
        background: rgba(59, 130, 246, 0.08);
        border-left: 4px solid #2563eb;
        padding: 16px 20px;
        border-radius: 10px;
        color: #1e3a8a;
        font-size: 0.98rem;
        line-height: 1.6;
        margin-bottom: 16px;
    }
    [data-testid="stSidebar"] button[kind="secondary"] {
        background-color: transparent !important;
        border: none !important;
        color: #334155 !important;
        text-align: left !important;
        justify-content: flex-start !important;
        font-size: 0.9rem !important;
        border-radius: 8px !important;
        padding: 6px 10px !important;
    }
    [data-testid="stSidebar"] button[kind="primary"] {
        background-color: #e2e8f0 !important;
        border: 1px solid #cbd5e1 !important;
        color: #0f172a !important;
        text-align: left !important;
        justify-content: flex-start !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        padding: 6px 10px !important;
    }
    .recent-header { color: #64748b; }
    """
else:
    theme_css = """
    .stApp {
        background-color: #131314;
        color: #e3e3e3;
        font-family: 'Google Sans', 'Inter', sans-serif;
    }
    [data-testid="stSidebar"] {
        background-color: #1e1f20;
        border-right: 1px solid #2e2f31;
    }
    .header-card {
        background: linear-gradient(135deg, #1e2022 0%, #17181a 100%);
        border: 1px solid #2e3034;
        padding: 20px 24px;
        border-radius: 16px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
    }
    .header-title { color: #f3f4f6; }
    .header-subtitle { color: #9ca3af; }
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
    .recent-header { color: #8e918f; }
    """

st.markdown(f"""
<style>
    {theme_css}

    [data-testid="stSidebar"] button:hover {{
        background-color: rgba(148, 163, 184, 0.15) !important;
    }}

    /* Popover Menu Styling */
    [data-testid="stPopover"] button {{
        background: transparent !important;
        border: none !important;
        color: #9ca3af !important;
        padding: 2px 6px !important;
    }}
    
    .recent-header {{
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 10px;
        margin-bottom: 4px;
    }}

    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)

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

# SIDEBAR (Strictly Fixed Top & Bottom Layout)
with st.sidebar:
    # 1. Fixed Header
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 2px;">
            <span style="font-size: 1.6rem;">⚡</span>
            <span style="font-size: 1.35rem; font-weight: 700;">ActionPulse AI</span>
        </div>
        <div style="font-size: 0.82rem; margin-bottom: 12px; opacity: 0.8;">
            Automated Meeting Insights & Action Extraction
        </div>
    """, unsafe_allow_html=True)

    # 2. Fixed Action Buttons
    if st.button("📝 New chat", use_container_width=True, type="primary"):
        start_new_chat()
        st.rerun()

    search_input = st.text_input("🔍 Search chats", value=st.session_state.search_query, placeholder="Filter conversations...")
    st.session_state.search_query = search_input

    # 3. Vertically Scrollable Recents Container (Height: 330px)
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

        col_title, col_opts = st.columns([0.80, 0.20])
        with col_title:
            btn_type = "primary" if is_active else "secondary"
            if st.button(title, key=f"nav_{cid}", use_container_width=True, type=btn_type):
                st.session_state.current_chat_id = cid
                st.rerun()

        with col_opts:
            with st.popover("⋮", help="Options"):
                pin_action = "Unpin" if is_pinned else "Pin"
                if st.button(f"📌 {pin_action}", key=f"pin_act_{cid}", use_container_width=True):
                    cdata["pinned"] = not is_pinned
                    st.rerun()

                with st.form(key=f"rename_form_{cid}"):
                    new_t = st.text_input("Rename:", value=title)
                    if st.form_submit_button("✏️ Save"):
                        if new_t.strip():
                            cdata["title"] = new_t.strip()
                            st.rerun()

                if st.button("🗑️ Delete", key=f"del_act_{cid}", use_container_width=True):
                    del st.session_state.chats[cid]
                    if not st.session_state.chats:
                        start_new_chat()
                    else:
                        st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
                    st.rerun()

    recents_box = st.container(height=330)
    with recents_box:
        if pinned_chats:
            st.markdown('<div class="recent-header">Pinned</div>', unsafe_allow_html=True)
            for cid, cdata in reversed(pinned_chats):
                render_chat_item(cid, cdata)

        st.markdown('<div class="recent-header">Recents</div>', unsafe_allow_html=True)
        if recent_chats:
            for cid, cdata in reversed(recent_chats):
                render_chat_item(cid, cdata)
        else:
            st.caption("No recent conversations.")

    # 4. Strictly Fixed Bottom Settings Popover (No API Keys UI)
    st.markdown("---")
    with st.popover("⚙️ Settings", use_container_width=True):
        st.markdown("### Settings")
        tab_app, tab_fb, tab_about = st.tabs(["Appearance", "Provide Feedback", "About Us & Contact"])

        with tab_app:
            st.markdown("#### Theme")
            selected_theme = st.radio(
                "Choose interface style:",
                options=["Dark Theme", "Light Theme"],
                index=0 if st.session_state.theme_mode == "Dark Theme" else 1,
                key="theme_radio_input"
            )
            if selected_theme != st.session_state.theme_mode:
                st.session_state.theme_mode = selected_theme
                st.rerun()

        with tab_fb:
            st.markdown("#### Provide Feedback")
            fb_content = st.text_area("Share your feedback or suggestions:", height=100, placeholder="Type your feedback here...")
            if st.button("Submit Feedback", key="submit_fb_action", type="primary"):
                if fb_content.strip():
                    st.success("Thank you for your feedback!")

        with tab_about:
            st.markdown("#### ActionPulse AI v2.0")
            st.markdown(
                "Transform raw meeting transcripts, notes, paragraphs, PDFs, Word docs, "
                "or handwritten screenshots into executive summaries and structured action items."
            )
            st.markdown("---")
            st.markdown("**📧 Contact Support & Inquiries:**")
            st.code("support@actionpulse.ai", language="text")

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

import textwrap

if "processed_files" not in st.session_state:
    st.session_state.processed_files = set()

# 2. Render Active Chat Messages
messages = current_chat["messages"]

import re

def mask_sensitive_keys(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'gsk_[A-Za-z0-9_]+', '[REDACTED_API_KEY]', text)
    text = re.sub(r'sk-[A-Za-z0-9_-]+', '[REDACTED_API_KEY]', text)
    return text

for message in messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            if "full_text" in message:
                full_txt = mask_sensitive_keys(message["full_text"])
                with st.expander(f"📝 Submitted Input Text ({len(full_txt)} characters)", expanded=False):
                    st.markdown(
                        f'<div style="white-space: pre-wrap; word-break: break-word; font-family: monospace; font-size: 0.9rem; background-color: #1a1b1e; color: #e3e3e3; padding: 12px; border-radius: 8px; border: 1px solid #2e3034;">{full_txt}</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.markdown(message["content"])
        else:
            data = message.get("result")
            if data:
                st.markdown("### 📌 Executive Summary")
                st.markdown(f'<div class="summary-box">{data.get("summary", "No summary extracted.")}</div>', unsafe_allow_html=True)

                st.markdown("### ✅ Extracted Action Items")
                action_items = data.get("action_items", [])
                if action_items:
                    rows_html = ""
                    for item in action_items:
                        task = item.get("task", "N/A")
                        owner = item.get("owner", "Unassigned")
                        due = item.get("due_date", "No due date")
                        rows_html += f"""<tr style="border-bottom: 1px solid rgba(255,255,255,0.08);"><td style="padding: 12px 16px; word-break: break-word; white-space: normal; line-height: 1.5; font-weight: 500;">{task}</td><td style="padding: 12px 16px; word-break: break-word; white-space: normal; color: #60a5fa; font-weight: 500;">{owner}</td><td style="padding: 12px 16px; word-break: break-word; white-space: normal; color: #f59e0b; font-weight: 500;">{due}</td></tr>"""
                    
                    table_html = textwrap.dedent(f"""
                    <div style="border: 1px solid rgba(255,255,255,0.12); border-radius: 12px; overflow: hidden; margin-bottom: 16px;">
                    <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 0.95rem;">
                    <thead>
                    <tr style="background: rgba(255,255,255,0.06); border-bottom: 1px solid rgba(255,255,255,0.12); color: #9ca3af; font-size: 0.85rem; text-transform: uppercase;">
                    <th style="padding: 12px 16px; width: 55%;">Task Description</th>
                    <th style="padding: 12px 16px; width: 25%;">Assignee / Owner</th>
                    <th style="padding: 12px 16px; width: 20%;">Due Date</th>
                    </tr>
                    </thead>
                    <tbody>
                    {rows_html}
                    </tbody>
                    </table>
                    </div>
                    """).strip()
                    st.markdown(table_html, unsafe_allow_html=True)

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

# 3. File Extractor Helper
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

# 4. File Attachment Expander
file_submit_clicked = False
file_text, file_img_bytes, file_img_mime = None, None, None

with st.expander("➕ Upload File (.txt, .pdf, .docx, .png, .jpg)", expanded=False):
    uploaded_file = st.file_uploader(
        "Attach meeting document, transcript, or notes image:",
        type=["txt", "md", "pdf", "docx", "png", "jpg", "jpeg", "webp"],
        key=f"file_up_{st.session_state.current_chat_id}"
    )
    if uploaded_file is not None:
        file_sig = f"{uploaded_file.name}_{uploaded_file.size}"
        st.info(f"File `{uploaded_file.name}` attached.")
        if st.button("⚡ Process & Extract Action Items from Attached File", type="primary", key=f"btn_file_sub_{st.session_state.current_chat_id}"):
            file_text, file_img_bytes, file_img_mime = extract_file_data(uploaded_file)
            file_submit_clicked = True
            st.session_state.processed_files.add(file_sig)

# 5. Gemini-Style Chat Input Box
user_prompt = st.chat_input("Enter a meeting transcript, raw notes, or paragraph text...")

# Determine payload
text_to_process = file_text if file_submit_clicked else user_prompt
img_bytes_to_process = file_img_bytes if file_submit_clicked else None

if text_to_process or img_bytes_to_process:
    # Update Chat Title based on first message
    if not messages or current_chat["title"] == "New Chat":
        if text_to_process:
            preview_title = text_to_process.strip().split("\n")[0][:26]
        else:
            preview_title = f"Image ({uploaded_file.name[:20]})"
        current_chat["title"] = preview_title if preview_title else "Transcript Analysis"

    # Append User Message with Expandable full_text
    if text_to_process:
        user_msg = {
            "role": "user",
            "content": f"📝 Submitted Input Text ({len(text_to_process)} characters)",
            "full_text": text_to_process
        }
    else:
        user_msg = {
            "role": "user",
            "content": f"📷 **Uploaded Image Document:** `{uploaded_file.name}`"
        }

    messages.append(user_msg)

    with st.spinner("Extracting action items..."):
        try:
            result = process_transcript(
                transcript_text=text_to_process,
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
