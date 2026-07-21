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
is_light_mode = (st.session_state.theme_mode == "Light Theme")

if is_light_mode:
    theme_css = """
    .stApp, 
    [data-testid="stAppViewContainer"], 
    [data-testid="stHeader"], 
    [data-testid="stBottom"], 
    [data-testid="stBottom"] > div {
        background-color: #f8fafc !important;
        color: #0f172a !important;
        font-family: 'Google Sans', 'Inter', sans-serif !important;
    }
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0 !important;
        color: #0f172a !important;
    }
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] div, 
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #0f172a !important;
    }
    div[data-baseweb="input"], input, textarea {
        background-color: #f1f5f9 !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
        -webkit-text-fill-color: #0f172a !important;
    }
    div[data-baseweb="input"] input::placeholder, textarea::placeholder {
        color: #64748b !important;
        -webkit-text-fill-color: #64748b !important;
    }
    .header-card {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        padding: 20px 24px;
        border-radius: 16px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04) !important;
    }
    .header-title { color: #0f172a !important; }
    .header-subtitle { color: #475569 !important; }
    .summary-box {
        background: #eff6ff !important;
        border-left: 4px solid #2563eb !important;
        padding: 16px 20px;
        border-radius: 10px;
        color: #1e3a8a !important;
        font-size: 0.98rem;
        line-height: 1.6;
        margin-bottom: 16px;
    }
    h1, h2, h3, h4, h5, h6, .stMarkdown, p, span, label {
        color: #0f172a !important;
    }
    .recent-header { color: #64748b !important; }

    /* Popover Body & Window (Settings Window) */
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div,
    div[data-baseweb="popover"] [data-baseweb="menu"],
    div[data-testid="stPopoverBody"],
    [data-testid="stPopoverBody"] {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.12) !important;
    }
    div[data-baseweb="popover"] *,
    div[data-testid="stPopoverBody"] * {
        color: #0f172a !important;
    }
    div[data-baseweb="popover"] [data-baseweb="tab"] p,
    div[data-testid="stPopoverBody"] [data-baseweb="tab"] p {
        color: #64748b !important;
    }
    div[data-baseweb="popover"] [aria-selected="true"] p,
    div[data-testid="stPopoverBody"] [aria-selected="true"] p {
        color: #2563eb !important;
        font-weight: 600 !important;
    }
    div[data-baseweb="popover"] textarea,
    div[data-testid="stPopoverBody"] textarea {
        background-color: #f8fafc !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
        -webkit-text-fill-color: #0f172a !important;
    }
    div[data-baseweb="popover"] button,
    div[data-testid="stPopoverBody"] button,
    [data-testid="stPopoverBody"] button {
        background-color: #f1f5f9 !important;
        border: 1px solid #cbd5e1 !important;
        color: #0f172a !important;
        border-radius: 8px !important;
        -webkit-text-fill-color: #0f172a !important;
    }
    div[data-baseweb="popover"] button:hover,
    div[data-testid="stPopoverBody"] button:hover,
    [data-testid="stPopoverBody"] button:hover {
        background-color: #e2e8f0 !important;
        border-color: #94a3b8 !important;
    }

    /* Expanders */
    [data-testid="stExpander"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 12px !important;
    }
    [data-testid="stExpander"] summary {
        background-color: #f1f5f9 !important;
        color: #0f172a !important;
        border-radius: 12px !important;
    }
    [data-testid="stExpander"] * {
        color: #0f172a !important;
    }

    /* Chat Messages & Chat Input Box */
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
    }
    div[data-testid="stChatInput"],
    div[data-testid="stChatInput"] > div,
    div[data-testid="stChatInput"] div[data-baseweb="base-input"],
    div[data-testid="stChatInput"] div[data-baseweb="textarea"],
    div[data-testid="stChatInputTextArea"],
    textarea[data-testid="stChatInputTextArea"] {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border-color: #cbd5e1 !important;
        -webkit-text-fill-color: #0f172a !important;
    }
    div[data-testid="stChatInput"] textarea::placeholder {
        color: #64748b !important;
        -webkit-text-fill-color: #64748b !important;
    }
    div[data-testid="stChatInput"] button {
        color: #2563eb !important;
    }

    /* File Uploader Dropzone */
    [data-testid="stFileUploaderDropzone"],
    div[data-testid="stFileUploaderDropzone"] {
        background-color: #f1f5f9 !important;
        border: 2px dashed #cbd5e1 !important;
        color: #0f172a !important;
        border-radius: 12px !important;
    }
    [data-testid="stFileUploaderDropzone"] * {
        color: #0f172a !important;
    }
    [data-testid="stFileUploaderDropzone"] button {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        color: #0f172a !important;
    }

    /* Code Blocks & Pre Blocks */
    [data-testid="stCodeBlock"], code, pre {
        background-color: #f1f5f9 !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        -webkit-text-fill-color: #0f172a !important;
    }
    [data-testid="stCodeBlock"] * {
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
    }

    /* Download Buttons & Secondary Form Action Buttons */
    [data-testid="stDownloadButton"] button,
    div[data-testid="stAppViewContainer"] button[kind="secondary"],
    button[data-testid="baseButton-secondary"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        color: #0f172a !important;
        border-radius: 8px !important;
    }
    [data-testid="stDownloadButton"] button:hover,
    button[data-testid="baseButton-secondary"]:hover {
        background-color: #f1f5f9 !important;
        border-color: #94a3b8 !important;
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
    """
else:
    theme_css = """
    .stApp, 
    [data-testid="stAppViewContainer"], 
    [data-testid="stHeader"], 
    [data-testid="stBottom"], 
    [data-testid="stBottom"] > div {
        background-color: #131314 !important;
        color: #e3e3e3 !important;
        font-family: 'Google Sans', 'Inter', sans-serif !important;
    }
    [data-testid="stSidebar"] {
        background-color: #1e1f20 !important;
        border-right: 1px solid #2e2f31 !important;
        color: #e3e3e3 !important;
    }
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] div, 
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #e3e3e3 !important;
    }
    div[data-baseweb="input"], input, textarea {
        background-color: #1e1f20 !important;
        color: #e3e3e3 !important;
        border: 1px solid #374151 !important;
        -webkit-text-fill-color: #e3e3e3 !important;
    }
    div[data-baseweb="input"] input::placeholder, textarea::placeholder {
        color: #8e918f !important;
        -webkit-text-fill-color: #8e918f !important;
    }
    .header-card {
        background: linear-gradient(135deg, #1e2022 0%, #17181a 100%) !important;
        border: 1px solid #2e3034 !important;
        padding: 20px 24px;
        border-radius: 16px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4) !important;
    }
    .header-title { color: #f3f4f6 !important; }
    .header-subtitle { color: #9ca3af !important; }
    .summary-box {
        background: rgba(37, 99, 235, 0.15) !important;
        border-left: 4px solid #3b82f6 !important;
        padding: 16px 20px;
        border-radius: 10px;
        color: #dbeafe !important;
        font-size: 0.98rem;
        line-height: 1.6;
        margin-bottom: 16px;
    }
    h1, h2, h3, h4, h5, h6, .stMarkdown, p, span, label {
        color: #e3e3e3 !important;
    }
    .recent-header { color: #8e918f !important; }

    /* Popover Body & Window (Settings Window) */
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div,
    div[data-baseweb="popover"] [data-baseweb="menu"],
    div[data-testid="stPopoverBody"],
    [data-testid="stPopoverBody"] {
        background-color: #1e1f20 !important;
        color: #e3e3e3 !important;
        border: 1px solid #2e2f31 !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5) !important;
    }
    div[data-baseweb="popover"] *,
    div[data-testid="stPopoverBody"] * {
        color: #e3e3e3 !important;
    }
    div[data-baseweb="popover"] [data-baseweb="tab"] p,
    div[data-testid="stPopoverBody"] [data-baseweb="tab"] p {
        color: #8e918f !important;
    }
    div[data-baseweb="popover"] [aria-selected="true"] p,
    div[data-testid="stPopoverBody"] [aria-selected="true"] p {
        color: #60a5fa !important;
        font-weight: 600 !important;
    }
    div[data-baseweb="popover"] button,
    div[data-testid="stPopoverBody"] button,
    [data-testid="stPopoverBody"] button {
        background-color: #282a2c !important;
        border: 1px solid #374151 !important;
        color: #e3e3e3 !important;
        border-radius: 8px !important;
        -webkit-text-fill-color: #e3e3e3 !important;
    }
    div[data-baseweb="popover"] button:hover,
    div[data-testid="stPopoverBody"] button:hover,
    [data-testid="stPopoverBody"] button:hover {
        background-color: #374151 !important;
    }

    /* Expanders */
    [data-testid="stExpander"] {
        background-color: #1e1f20 !important;
        border: 1px solid #2e2f31 !important;
        border-radius: 12px !important;
    }
    [data-testid="stExpander"] summary {
        background-color: #282a2c !important;
        color: #e3e3e3 !important;
        border-radius: 12px !important;
    }
    [data-testid="stExpander"] * {
        color: #e3e3e3 !important;
    }

    /* Chat Messages & Chat Input Box */
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
    }
    div[data-testid="stChatInput"],
    div[data-testid="stChatInput"] > div,
    div[data-testid="stChatInput"] div[data-baseweb="base-input"],
    div[data-testid="stChatInput"] div[data-baseweb="textarea"],
    div[data-testid="stChatInputTextArea"],
    textarea[data-testid="stChatInputTextArea"] {
        background-color: #1e1f20 !important;
        color: #e3e3e3 !important;
        border-color: #374151 !important;
        -webkit-text-fill-color: #e3e3e3 !important;
    }
    div[data-testid="stChatInput"] textarea::placeholder {
        color: #8e918f !important;
        -webkit-text-fill-color: #8e918f !important;
    }
    div[data-testid="stChatInput"] button {
        color: #60a5fa !important;
    }

    /* File Uploader Dropzone */
    [data-testid="stFileUploaderDropzone"],
    div[data-testid="stFileUploaderDropzone"] {
        background-color: #1e1f20 !important;
        border: 2px dashed #374151 !important;
        color: #e3e3e3 !important;
        border-radius: 12px !important;
    }
    [data-testid="stFileUploaderDropzone"] * {
        color: #e3e3e3 !important;
    }
    [data-testid="stFileUploaderDropzone"] button {
        background-color: #282a2c !important;
        border: 1px solid #374151 !important;
        color: #ffffff !important;
    }

    /* Code Blocks & Pre Blocks */
    [data-testid="stCodeBlock"], code, pre {
        background-color: #1e1f20 !important;
        color: #e3e3e3 !important;
        border: 1px solid #2e2f31 !important;
        border-radius: 8px !important;
        -webkit-text-fill-color: #e3e3e3 !important;
    }
    [data-testid="stCodeBlock"] * {
        color: #e3e3e3 !important;
        -webkit-text-fill-color: #e3e3e3 !important;
    }

    /* Download Buttons */
    [data-testid="stDownloadButton"] button {
        background-color: #282a2c !important;
        border: 1px solid #374151 !important;
        color: #ffffff !important;
        border-radius: 8px !important;
    }
    [data-testid="stDownloadButton"] button:hover {
        background-color: #374151 !important;
    }
    """

st.markdown(f"""
<style>
    {theme_css}

    /* Lock sidebar top-level container from scrolling */
    section[data-testid="stSidebar"] {{
        overflow: hidden !important;
    }}

    [data-testid="stSidebarUserContent"] {{
        display: flex !important;
        flex-direction: column !important;
        height: calc(100vh - 24px) !important;
        max-height: 100vh !important;
        overflow: hidden !important;
        justify-content: space-between !important;
        padding-bottom: 12px !important;
    }}

    /* Only Recents container scrolls vertically */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        border-color: {'#cbd5e1' if is_light_mode else 'rgba(255, 255, 255, 0.08)'} !important;
        border-radius: 12px !important;
        max-height: calc(100vh - 330px) !important;
        flex: 1 1 auto !important;
    }}

    [data-testid="stSidebar"] button:hover {{
        background-color: {'#cbd5e1' if is_light_mode else 'rgba(148, 163, 184, 0.15)'} !important;
    }}

    /* Popover Menu Styling */
    [data-testid="stPopover"] button {{
        background: transparent !important;
        border: none !important;
        color: {'#64748b' if is_light_mode else '#9ca3af'} !important;
        padding: 2px 6px !important;
    }}
    
    .recent-header {{
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 6px;
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
                c_bg = "#f8fafc" if is_light_mode else "#1a1b1e"
                c_txt = "#0f172a" if is_light_mode else "#e3e3e3"
                c_bdr = "#cbd5e1" if is_light_mode else "#2e3034"
                with st.expander(f"📝 Submitted Input Text ({len(full_txt)} characters)", expanded=False):
                    st.markdown(
                        f'<div style="white-space: pre-wrap; word-break: break-word; font-family: monospace; font-size: 0.9rem; background-color: {c_bg}; color: {c_txt}; padding: 12px; border-radius: 8px; border: 1px solid {c_bdr};">{full_txt}</div>',
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
                    r_border = "#e2e8f0" if is_light_mode else "rgba(255,255,255,0.08)"
                    t_color = "#0f172a" if is_light_mode else "#e3e3e3"
                    o_color = "#2563eb" if is_light_mode else "#60a5fa"
                    d_color = "#d97706" if is_light_mode else "#f59e0b"
                    
                    rows_html = ""
                    for item in action_items:
                        task = item.get("task", "N/A")
                        owner = item.get("owner", "Unassigned")
                        due = item.get("due_date", "No due date")
                        rows_html += f"""<tr style="border-bottom: 1px solid {r_border};"><td style="padding: 12px 16px; word-break: break-word; white-space: normal; line-height: 1.5; font-weight: 500; color: {t_color};">{task}</td><td style="padding: 12px 16px; word-break: break-word; white-space: normal; color: {o_color}; font-weight: 500;">{owner}</td><td style="padding: 12px 16px; word-break: break-word; white-space: normal; color: {d_color}; font-weight: 500;">{due}</td></tr>"""
                    
                    tbl_border = "#cbd5e1" if is_light_mode else "rgba(255,255,255,0.12)"
                    th_bg = "#f1f5f9" if is_light_mode else "rgba(255,255,255,0.06)"
                    th_text = "#475569" if is_light_mode else "#9ca3af"

                    table_html = textwrap.dedent(f"""
                    <div style="border: 1px solid {tbl_border}; border-radius: 12px; overflow: hidden; margin-bottom: 16px; background-color: {'#ffffff' if is_light_mode else 'transparent'};">
                    <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 0.95rem;">
                    <thead>
                    <tr style="background: {th_bg}; border-bottom: 1px solid {tbl_border}; color: {th_text}; font-size: 0.85rem; text-transform: uppercase;">
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
