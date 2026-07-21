# ActionPulse AI ⚡

**ActionPulse AI** is an intelligent meeting transcript processor that turns raw, unstructured conversation logs into concise executive summaries and structured, actionable tasks with assigned owners and due dates. Built with both a modern Streamlit Web UI and a standalone CLI backend.

---

## 🚀 Quickstart Guide

### 1. Prerequisites & Installation

Ensure you have Python 3.9+ installed. Clone or navigate to the repository directory and install dependencies:

```bash
pip install -r requirements.txt
```

### 2. OpenAI API Key Setup

Set your OpenAI API key in your terminal environment:

* **Linux / macOS:**
  ```bash
  export OPENAI_API_KEY="your_openai_api_key_here"
  ```
* **Windows (Command Prompt):**
  ```cmd
  set OPENAI_API_KEY=your_openai_api_key_here
  ```
* **Windows (PowerShell):**
  ```powershell
  $env:OPENAI_API_KEY="your_openai_api_key_here"
  ```

---

### 3. Launching the Web UI

To launch the interactive Streamlit web application:

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501` to use the chat interface, upload transcripts, or test preloaded sample transcripts.

---

### 4. Running the CLI Backend

To process a transcript directly from the terminal:

```bash
# Process default sample transcript (sample_transcript.txt)
python agent.py

# Or specify a custom transcript file path
python agent.py sample_transcript_2.txt
```

The output summary and action items will display in the terminal and automatically save to `output.json`.

---

## ✨ Features Overview

- **Sleek Streamlit Web UI:** Modern interface featuring real-time state management, glassmorphism design, and formatted data tables.
- **Dual Input Modes:** Upload `.txt` files directly, load pre-configured sample transcripts, or paste raw text.
- **Structured Extraction:** Extracts concise executive summaries alongside structured action items (`task`, `owner`, `due_date`).
- **Export Capabilities:** One-click JSON download button in the web app (`action_items.json`) and automated CLI output (`output.json`).
- **Interactive Chat History:** Maintains chat session history across multiple transcript analyses.

---

## 📄 Sample JSON Output

Below is an example of the structured JSON schema returned by ActionPulse AI:

```json
{
  "summary": "The team conducted a launch sync for ActionPulse 2.0. Following successful QA and frontend performance tests, October 15, 2026 was officially set as the public release date. The team also agreed to retain the Tiered Enterprise pricing structure.",
  "action_items": [
    {
      "task": "Finalize and publish complete API documentation and developer guides.",
      "owner": "David",
      "due_date": "2026-10-01"
    },
    {
      "task": "Perform end-to-end load testing on staging environment and deliver reports.",
      "owner": "Sarah",
      "due_date": "2026-10-05"
    },
    {
      "task": "Draft and finalize the launch press release and social campaign.",
      "owner": "Alex",
      "due_date": "2026-10-08"
    }
  ]
}
```

---

## 🛠️ Engineering Design & Tradeoffs

### 1. Model Choice: `gpt-4o-mini`
- **Rationale:** We selected `gpt-4o-mini` with native JSON mode (`response_format={"type": "json_object"}`).
- **Tradeoffs:** `gpt-4o-mini` offers sub-second latency and ultra-low cost per turn while delivering high fidelity for structured extraction tasks. Native JSON mode guarantees syntactically valid JSON output, preventing downstream parsing failures.

### 2. Context Strategy: Direct Injection over RAG
- **Rationale:** Typical meeting transcripts range between 500 and 5,000 tokens, which easily fit inside `gpt-4o-mini`'s 128k context window.
- **Tradeoffs:** Performing Retrieval-Augmented Generation (RAG) or vector chunking on meeting transcripts risks splitting speaker turns or separating task assignments from their contextual due dates. Direct context injection passes the complete conversation flow to the LLM, preserving crucial relational context.

### 3. Future Improvements
- **Integration Webhooks:** Automated triggers pushing extracted tasks directly to **Slack**, **Trello**, **Jira**, or **Asana**.
- **Calendar Integration:** Syncing extracted due dates automatically to **Google Calendar** or **Outlook**.
- **Multi-Speaker Diarization:** Integration with Whisper AI / AssemblyAI speech-to-text APIs to convert raw meeting audio directly into transcripts.
