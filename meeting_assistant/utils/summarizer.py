import json
import re
import urllib.request
import urllib.error


def build_prompt(
    transcript: str,
    include_sentiment: bool = True,
    include_keywords: bool = True,
    include_followup: bool = False,
) -> str:
    prompt = f"""You are an expert AI meeting assistant. Analyze the following meeting transcript and extract structured information.

Respond ONLY with valid JSON. No explanation, no markdown, no extra text — just JSON.

JSON format:
{{
  "summary": "A clear 3-5 sentence paragraph summarizing the meeting purpose, main topics, and outcomes.",
  "decisions": ["Decision 1", "Decision 2"],
  "action_items": ["Action item 1 (with owner if mentioned)", "Action item 2"],
  "sentiment": "One phrase describing the tone",
  "keywords": ["topic1", "topic2", "topic3"],
  "followup_questions": ["Question 1?", "Question 2?"]
}}

If a section has no content, use an empty array [] or empty string "".

Meeting Transcript:
\"\"\"
{transcript}
\"\"\"

Respond with JSON only:"""
    return prompt


def call_ollama(prompt: str, model: str = "llama3") -> str:
    """
    Call Ollama via HTTP API (much faster than CLI subprocess).
    Ollama runs a local server at http://localhost:11434
    """
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,      # low = more consistent JSON output
            "num_predict": 1024,     # limit output tokens for speed
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = resp.read().decode("utf-8")
            data = json.loads(body)
            return data.get("response", "").strip()
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Cannot reach Ollama at localhost:11434. Make sure Ollama is running.\nError: {e}"
        )


def parse_json_response(raw: str) -> dict:
    """Extract and parse JSON from the model response."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", raw)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return {
        "summary": raw,
        "decisions": [],
        "action_items": [],
        "sentiment": "",
        "keywords": [],
        "followup_questions": [],
    }


def generate_meeting_notes(
    transcript: str,
    model: str = "llama3",
    include_sentiment: bool = True,
    include_keywords: bool = True,
    include_followup: bool = False,
) -> dict:
    """Generate structured meeting notes from a transcript using Ollama HTTP API."""
    if not transcript or len(transcript.strip()) < 20:
        return {
            "summary": "Transcript too short to analyze.",
            "decisions": [],
            "action_items": [],
            "sentiment": "",
            "keywords": [],
            "followup_questions": [],
        }

    prompt = build_prompt(
        transcript,
        include_sentiment=include_sentiment,
        include_keywords=include_keywords,
        include_followup=include_followup,
    )

    raw_response = call_ollama(prompt, model=model)
    notes = parse_json_response(raw_response)

    defaults = {
        "summary": "",
        "decisions": [],
        "action_items": [],
        "sentiment": "",
        "keywords": [],
        "followup_questions": [],
    }
    for key, default in defaults.items():
        if key not in notes:
            notes[key] = default

    return notes