import os
import sys
import json
from openai import OpenAI

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def _clean_str(val: str) -> str:
    if val:
        val = val.strip().strip('"').strip("'")
    return val if val else None

import base64

def process_transcript(
    transcript_text: str = None, 
    api_key: str = None, 
    base_url: str = None, 
    model: str = None,
    image_bytes: bytes = None,
    image_mime: str = "image/png"
) -> dict:
    """
    Processes a raw meeting transcript string or document/notes image using OpenAI/Groq/compatible APIs
    and extracts a structured summary along with assigned action items.
    """
    resolved_api_key = _clean_str(api_key) or _clean_str(os.getenv("OPENAI_API_KEY"))
    resolved_base_url = _clean_str(base_url) or _clean_str(os.getenv("OPENAI_BASE_URL"))
    resolved_model = _clean_str(model) or _clean_str(os.getenv("LLM_MODEL")) or _clean_str(os.getenv("OPENAI_MODEL"))

    if not resolved_api_key:
        raise ValueError("OPENAI_API_KEY is missing. Please set it in your environment variables or sidebar.")

    # Auto-detect provider settings based on key format if not specified
    if resolved_api_key.startswith("gsk_"):
        if not resolved_base_url or "openrouter.ai" in resolved_base_url:
            resolved_base_url = "https://api.groq.com/openai/v1"
        if image_bytes:
            resolved_model = "llama-3.2-11b-vision-preview"
        elif not resolved_model or resolved_model in ["gpt-4o-mini", "openrouter/free"]:
            resolved_model = "llama-3.3-70b-versatile"
    elif resolved_api_key.startswith("sk-or-v1-"):
        if not resolved_base_url:
            resolved_base_url = "https://openrouter.ai/api/v1"
        if not resolved_model or resolved_model == "gpt-4o-mini":
            resolved_model = "meta-llama/llama-3.3-70b-instruct:free"
    
    if not resolved_model:
        resolved_model = "gpt-4o-mini"

    client_kwargs = {"api_key": resolved_api_key}
    if resolved_base_url:
        client_kwargs["base_url"] = resolved_base_url
        if "openrouter.ai" in resolved_base_url:
            client_kwargs["default_headers"] = {
                "HTTP-Referer": "https://github.com/actionpulse-ai",
                "X-Title": "ActionPulse AI"
            }

    client = OpenAI(**client_kwargs)
    
    system_prompt = (
        "You are an expert Executive Assistant specializing in extracting key insights and action items "
        "from meeting transcripts and document images. Analyze the provided content carefully and produce a valid JSON object strictly formatted with:\n"
        "1. 'summary': A concise executive summary paragraph highlighting key decisions made, milestone dates, and major outcomes.\n"
        "2. 'action_items': A list of action item objects where each object contains:\n"
        "   - 'task': Clear, concise action item description.\n"
        "   - 'owner': Name of the assigned individual.\n"
        "   - 'due_date': Explicit due date or timeline mentioned in the text (e.g. YYYY-MM-DD or specific date string).\n\n"
        "Do not include any text outside the JSON object."
    )
    
    if image_bytes:
        b64_img = base64.b64encode(image_bytes).decode("utf-8")
        user_content = [
            {"type": "text", "text": "Extract executive summary and action items from this meeting notes/document image:"},
            {"type": "image_url", "image_url": {"url": f"data:{image_mime};base64,{b64_img}"}}
        ]
    else:
        user_content = f"Here is the meeting transcript:\n\n---\n{transcript_text}\n---"

    # Try with json_object response format first, fallback without it if unsupported
    try:
        try:
            response = client.chat.completions.create(
                model=resolved_model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.2
            )
        except Exception as fmt_err:
            # Fallback for models/providers that don't support response_format
            if "response_format" in str(fmt_err).lower() or "schema" in str(fmt_err).lower() or "supported" in str(fmt_err).lower():
                response = client.chat.completions.create(
                    model=resolved_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.2
                )
            else:
                raise fmt_err
    except Exception as err:
        err_type = type(err).__name__
        err_str = str(err)
        if "APIConnectionError" in err_type or "ConnectionError" in err_type or "connect" in err_str.lower():
            raise RuntimeError(
                f"Connection error reaching API endpoint ({resolved_base_url or 'api.openai.com'}). "
                f"Please check your internet connection or proxy. Details: {err_str}"
            )
        elif "AuthenticationError" in err_type or "401" in err_str or "auth" in err_str.lower() or "key" in err_str.lower():
            raise RuntimeError(
                f"Authentication failed. Please verify that your API key is valid and formatted without quotes. Details: {err_str}"
            )
        else:
            raise RuntimeError(f"API request failed for model '{resolved_model}' ({err_type}): {err_str}")

    content = response.choices[0].message.content.strip()
    
    # Strip markdown code fences if present (e.g. ```json ... ```)
    if content.startswith("```"):
        lines = content.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        content = "\n".join(lines).strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse model response as JSON: {e}\nRaw Content:\n{content}")


if __name__ == '__main__':
    filepath = sys.argv[1] if len(sys.argv) > 1 else 'sample_transcript.txt'
    
    if not os.path.exists(filepath):
        print(f"Error: Transcript file '{filepath}' not found.")
        sys.exit(1)

    print(f"📂 Reading transcript from: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        transcript_content = f.read()

    print("⚡ Requesting ActionPulse AI analysis via gpt-4o-mini...")
    try:
        result = process_transcript(transcript_content)
        
        output_filename = 'output.json'
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
            
        print("\n" + "=" * 50)
        print("📌 EXECUTIVE SUMMARY")
        print("=" * 50)
        print(result.get("summary", "No summary provided."))
        
        print("\n" + "=" * 50)
        print("✅ ACTION ITEMS")
        print("=" * 50)
        action_items = result.get("action_items", [])
        if action_items:
            for i, item in enumerate(action_items, 1):
                task = item.get("task", "N/A")
                owner = item.get("owner", "Unassigned")
                due = item.get("due_date", "No due date")
                print(f"  {i}. [Task]     {task}")
                print(f"     [Owner]    {owner}")
                print(f"     [Due Date] {due}\n")
        else:
            print("No action items found.")
            
        print("=" * 50)
        print(f"💾 Analysis saved to {output_filename} successfully!")

    except Exception as err:
        print(f"❌ Error during processing: {err}")
        sys.exit(1)
