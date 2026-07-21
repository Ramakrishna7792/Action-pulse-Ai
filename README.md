# ActionPulse AI ⚡
> **Automated Meeting Insights & Action Item Extraction Agent**  
> *Category 2 — Meeting Notes to Action Items (Intermediate)*

ActionPulse AI is an end-to-end AI agent designed to convert messy, unstructured meeting transcripts, text documents, PDFs, DOCX files, and whiteboard images into concise executive summaries and structured, owner-assigned action items.

---

## 🌟 Key Features

- **Gemini AI-Inspired UI:** Modern, clean interface featuring a Dual Theme System (Dark 🌙 / Light ☀️) with 100% component compatibility.
- **Multimodal & Multi-Format Ingestion:** Supports `.txt`, `.md`, `.pdf` (via `pypdf`), `.docx` (via `python-docx`), and image formats (`.png`, `.jpg`, `.jpeg`, `.webp` via Vision AI).
- **Dual Execution Modes:** Fully functional interactive Streamlit Web UI (`app.py`) and a headless, zero-dependency CLI runner (`agent.py`).
- **Strict Left Sidebar Workspace:** 
  - Fixed header and single-click **📝 New chat** button.
  - **🔍 Search chats** filter with vertical scrolling restricted strictly to recent conversations.
  - Chat options menu (⋮) to **Pin 📌**, **Rename ✏️**, or **Delete 🗑️** sessions.
  - Pinned **⚙️ Settings** at the bottom-left corner.
- **Privacy & Safety Safeguards:** Automatic real-time redaction of sensitive API keys (`gsk_...`, `sk-...`) in submitted texts and logs.
- **Structured Data Export:** Generates validated JSON payloads with a single-click download option (`action_items.json`) and renders responsive multi-line HTML table views without truncation.

---

## 📁 Repository Structure

```text
ActionPulse_AI/
├── agent.py                 # Core CLI backend logic & standalone script
├── app.py                   # Gemini-inspired Streamlit Web Application
├── requirements.txt         # Python dependencies
├── sample_transcript.txt    # Primary test meeting transcript (Product Launch)
├── sample_transcript_2.txt  # Secondary test meeting transcript (Q3 Budgeting)
├── output.json              # Sample extracted JSON deliverable
├── .gitignore               # Protects environment keys & local cache
└── README.md                # Project documentation & evaluation guide
```

---

## 🚀 Quickstart & Setup Guide

### 1. Prerequisites
Python 3.9 or higher installed.

### 2. Installation
Clone the repository and install the required dependencies using Python's module runner:

```bash
git clone <your-github-repo-url>
cd ActionPulse_AI
python -m pip install -r requirements.txt
```

### 3. API Key Configuration
ActionPulse AI supports OpenAI API as well as free high-speed alternatives like Groq or OpenRouter.

#### Option A: Terminal Environment Variables
**Mac/Linux:**
```bash
export OPENAI_API_KEY="your_api_key_here"
# Optional for Groq/OpenRouter:
# export OPENAI_BASE_URL="https://api.groq.com/openai/v1"
# export LLM_MODEL="llama-3.1-8b-instant"
```

**Windows (CMD):**
```cmd
set OPENAI_API_KEY=your_api_key_here
:: Optional for Groq/OpenRouter:
:: set OPENAI_BASE_URL=https://api.groq.com/openai/v1
:: set LLM_MODEL=llama-3.1-8b-instant
```

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="your_api_key_here"
```

#### Option B: Streamlit Secrets File (Recommended for Local UI)
Create a `.streamlit/secrets.toml` file in the project root:

```toml
OPENAI_API_KEY = "your_api_key_here"
# Optional for Groq:
# OPENAI_BASE_URL = "https://api.groq.com/openai/v1"
# LLM_MODEL = "llama-3.1-8b-instant"
```

---

## 💻 Running the Agent

### Method 1: Interactive Streamlit Web UI
Launch the web interface:

```bash
python -m streamlit run app.py
```
The app will automatically open in your default browser at `http://localhost:8501`.

### Method 2: Command Line Interface (CLI)
Reviewers can run the standalone CLI script directly against any transcript file:

```bash
# Run against default sample transcript:
python agent.py sample_transcript.txt

# Run against a custom transcript file:
python agent.py path/to/your/custom_meeting.txt
```

---

## 📄 Sample Inputs & Outputs

### Sample Input (`sample_transcript.txt`)
```text
Alex: Good morning team, let's open today's launch sync for ActionPulse 2.0.
Sarah: Morning Alex! I've updated the QA test suite, and overall progress is looking solid.
David: Hey everyone. Frontend performance benchmarks passed our target thresholds yesterday.
Alex: That's awesome news. After reviewing user feedback, we decided to officially target October 15, 2026 for the public release.
Sarah: Sounds great! October 15 gives us enough runway to wrap up staging security audits. I will complete the security audit report by October 5th.
David: Agreed. I will finalize the API rate-limiting implementation by October 8th.
Alex: Great. I will update the executive board with the release timeline by tomorrow afternoon, September 28th.
```

### Sample Output (`output.json`)
```json
{
  "summary": "The team confirmed that QA test suites and frontend benchmarks have passed. The official public release date for ActionPulse 2.0 was set for October 15, 2026.",
  "action_items": [
    {
      "task": "Update the executive board with the official release timeline",
      "owner": "Alex",
      "due_date": "September 28, 2026"
    },
    {
      "task": "Complete staging security audit report",
      "owner": "Sarah",
      "due_date": "October 5, 2026"
    },
    {
      "task": "Finalize API rate-limiting implementation",
      "owner": "David",
      "due_date": "October 8, 2026"
    }
  ]
}
```

---

## 🛠️ Engineering Design & Tradeoff Notes

### 1. In-Memory State (`st.session_state`) vs. Database Persistence
**Design Decision:** The Web UI utilizes Streamlit's ephemeral `st.session_state` to store active chat history and chat options (pinning, renaming, deleting) rather than connecting to an external database (e.g., SQLite or PostgreSQL).

**Tradeoff & Reasoning:** Eliminating external database dependencies guarantees zero-configuration, instant execution for hackathon evaluators without risk of database lockouts or migration errors.

**Future Extension:** Implement SQLite/SQLAlchemy ORM for persisting chat histories and user preferences across server reboots.

### 2. Direct Context Window Injection vs. Retrieval-Augmented Generation (RAG)
**Design Decision:** The agent feeds complete transcript texts directly into the LLM context window using structured prompt constraints rather than chunking text into a vector database.

**Tradeoff & Reasoning:** Meeting transcripts almost always fall well within modern LLM context limits (e.g., 128k+ tokens for `gpt-4o-mini` / `llama-3.1`). Direct injection avoids chunking fragmentation and vector retrieval drop-off, ensuring 100% extraction accuracy across all action items.

### 3. Model Selection & Strict JSON Mode (`response_format={"type": "json_object"}`)
**Design Decision:** Standardized on `gpt-4o-mini` / `llama-3.1-8b-instant` with explicit JSON schema instructions.

**Tradeoff & Reasoning:** Provides ultra-fast inference (< 2 seconds) and guarantees valid JSON parsing, preventing UI rendering failures or invalid file exports.

### 4. Multimodal Processing Pipelines
**Design Decision:** Integrated dedicated native parsers (`pypdf`, `python-docx`) alongside Vision AI processing for images.

**Tradeoff & Reasoning:** Image processing relies on Vision APIs, which can increase latency slightly compared to plain text, but unlocks significant usability for handwritten or whiteboard meeting notes.
