import os
import sys
import json
from openai import OpenAI

def process_transcript(transcript_text: str) -> dict:
    """
    Processes a raw meeting transcript string using OpenAI's gpt-4o-mini model
    and extracts a structured summary along with assigned action items.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set. Please set it before running.")

    client = OpenAI(api_key=api_key)
    
    system_prompt = (
        "You are an expert Executive Assistant specializing in extracting key insights and action items "
        "from meeting transcripts. Analyze the provided meeting transcript carefully and produce a JSON object with:\n"
        "1. 'summary': A concise executive summary paragraph highlighting key decisions made, milestone dates, and major outcomes.\n"
        "2. 'action_items': A list of action item objects where each object contains:\n"
        "   - 'task': Clear, concise action item description.\n"
        "   - 'owner': Name of the assigned individual.\n"
        "   - 'due_date': Explicit due date or timeline mentioned in the text (e.g. YYYY-MM-DD or specific date string)."
    )
    
    user_prompt = f"Here is the meeting transcript:\n\n---\n{transcript_text}\n---"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2
    )

    content = response.choices[0].message.content
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse model response as JSON: {e}\nRaw Content: {content}")


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
