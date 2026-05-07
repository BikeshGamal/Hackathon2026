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
    prompt = f"""You are an expert AI meeting assistant. Your job is to extract every meaningful piece of information from a meeting transcript — nothing should be missed.

BEFORE you respond:
- Read the entire transcript from start to finish carefully.
- Do not skip, skim, or summarize prematurely.
- Only after reading the full transcript, produce your JSON output.

RULES:
- Be exhaustive. Do not omit any decision, action item, or topic — even minor ones.
- If something was agreed upon implicitly (e.g. "OK, let's do that"), treat it as a decision.
- If an action was assigned or volunteered (even informally), include it as an action item.
- The summary length must be proportional to the transcript length. A short meeting gets a short summary. A long, dense meeting gets multiple paragraphs. Do NOT arbitrarily cap the summary.
- Respond ONLY with valid JSON. No explanation, no markdown, no preamble — just raw JSON.

OUTPUT FORMAT:
{{
  "summary": "A thorough paragraph (or multiple paragraphs for long meetings) covering: the meeting's purpose, all main topics discussed, key points raised, and the overall outcome. Length scales with transcript length.",

  "decisions": [
    {{
      "decision": "What was decided (explicit or implicit)",
      "context": "Brief context or who drove the decision (if available)"
    }}
  ],

  "action_items": [
    {{
      "task": "What needs to be done",
      "owner": "Person responsible (or 'unassigned' if not mentioned)",
      "due": "Deadline or timeframe if mentioned, else null",
      "priority": "high | medium | low (infer from tone and urgency)"
    }}
  ],

  "sentiment": {{
    "overall": "One phrase describing the dominant tone of the meeting",
    "notable_moments": "Any moments of tension, disagreement, enthusiasm, or concern — or empty string if none"
  }},

  "keywords": ["topic1", "topic2", "topic3"],

  "followup_questions": [
    "Questions that came up but were left unresolved, or that should be addressed in the next meeting"
  ]
}}

IMPORTANT:
- If a section genuinely has no content, use [] for arrays or "" for strings.
- Do not invent information. Only extract what is in the transcript.
- Every decision and action item in the transcript must appear in your output — do not collapse or merge distinct items.
- keywords should include 5–10 meaningful topics, technologies, names, or themes.

---BEGIN TRANSCRIPT---
{transcript}
---END TRANSCRIPT---

Respond with JSON only:"""
    return prompt


def call_ollama(prompt: str, model: str = "gemma4") -> str:
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
        with urllib.request.urlopen(req, timeout=600) as resp:
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
    model: str = "gemma4",
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