import subprocess
import json
import re


def build_prompt(
    transcript: str,
    include_sentiment: bool = True,
    include_keywords: bool = True,
    include_followup: bool = False,
) -> str:
    """Build the structured prompt for meeting note generation."""

    optional_sections = ""
    if include_sentiment:
        optional_sections += """
6. SENTIMENT: One phrase describing the overall meeting tone (e.g. "Positive and productive", "Tense with unresolved conflicts", "Neutral and informational").
"""
    if include_keywords:
        optional_sections += """
7. KEYWORDS: A comma-separated list of 5-10 key topics or terms from the meeting.
"""
    if include_followup:
        optional_sections += """
8. FOLLOWUP: 2-4 follow-up questions that should be addressed in the next meeting.
"""

    prompt = f"""You are an expert AI meeting assistant. Analyze the following meeting transcript and extract structured information.

Respond ONLY with valid JSON. No explanation, no markdown, no extra text — just JSON.

JSON format:
{{
  "summary": "A clear 3-5 sentence paragraph summarizing the meeting purpose, main topics, and outcomes.",
  "decisions": ["Decision 1", "Decision 2", "..."],
  "action_items": ["Action item 1 (with owner if mentioned)", "Action item 2", "..."],
  "sentiment": "One phrase describing the tone" ,
  "keywords": ["topic1", "topic2", "..."],
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
    """Call Ollama CLI and return the response text."""
    result = subprocess.run(
        ["ollama", "run", model],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Ollama error: {result.stderr}")
    return result.stdout.strip()


def parse_json_response(raw: str) -> dict:
    """Extract and parse JSON from the model response."""
    # Try direct parse first
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Try extracting JSON block
    match = re.search(r"\{[\s\S]*\}", raw)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Fallback: return raw text as summary
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
    """
    Generate structured meeting notes from a transcript using Ollama.

    Args:
        transcript: The full meeting transcript text.
        model: Ollama model name to use.
        include_sentiment: Whether to include sentiment analysis.
        include_keywords: Whether to extract key topics.
        include_followup: Whether to generate follow-up questions.

    Returns:
        Dictionary with keys: summary, decisions, action_items,
        sentiment, keywords, followup_questions
    """
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

    # Ensure all expected keys exist
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
