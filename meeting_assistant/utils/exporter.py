def export_to_markdown(transcript: str, notes: dict, meeting_time: str) -> str:
    """Generate a polished Markdown export of the meeting notes."""

    lines = [
        "# Meeting Notes",
        f"> {meeting_time}",
        "",
        "---",
        "",
    ]

    # Summary
    if notes.get("summary"):
        lines += ["## Summary", "", notes["summary"], ""]

    # Key Decisions
    if notes.get("decisions"):
        lines += ["## Key Decisions", ""]
        for d in notes["decisions"]:
            lines.append(f"- {d}")
        lines.append("")

    # Action Items
    if notes.get("action_items"):
        lines += ["## Action Items", ""]
        for i, a in enumerate(notes["action_items"], 1):
            lines.append(f"- [ ] {a}")
        lines.append("")

    # Key Topics
    if notes.get("keywords"):
        lines += ["## Key Topics", ""]
        lines.append(", ".join(f"`{k}`" for k in notes["keywords"]))
        lines.append("")

    # Sentiment
    if notes.get("sentiment"):
        lines += ["## Meeting Sentiment", "", f"> {notes['sentiment']}", ""]

    # Follow-up Questions
    if notes.get("followup_questions"):
        lines += ["## Follow-up Questions", ""]
        for q in notes["followup_questions"]:
            lines.append(f"- {q}")
        lines.append("")

    # Full Transcript
    lines += [
        "---",
        "",
        "## Full Transcript",
        "",
        transcript,
        "",
    ]

    return "\n".join(lines)


def export_to_txt(transcript: str, notes: dict, meeting_time: str) -> str:
    """Generate a plain text export of the meeting notes."""

    sep = "=" * 60
    thin = "-" * 40
    lines = [
        sep,
        "MEETING NOTES",
        meeting_time,
        sep,
        "",
    ]

    if notes.get("summary"):
        lines += ["SUMMARY", thin, notes["summary"], ""]

    if notes.get("decisions"):
        lines += ["KEY DECISIONS", thin]
        for d in notes["decisions"]:
            lines.append(f"  • {d}")
        lines.append("")

    if notes.get("action_items"):
        lines += ["ACTION ITEMS", thin]
        for a in notes["action_items"]:
            lines.append(f"  → {a}")
        lines.append("")

    if notes.get("keywords"):
        lines += ["KEY TOPICS", thin, "  " + ", ".join(notes["keywords"]), ""]

    if notes.get("sentiment"):
        lines += ["SENTIMENT", thin, f"  {notes['sentiment']}", ""]

    if notes.get("followup_questions"):
        lines += ["FOLLOW-UP QUESTIONS", thin]
        for q in notes["followup_questions"]:
            lines.append(f"  ? {q}")
        lines.append("")

    lines += [sep, "FULL TRANSCRIPT", thin, "", transcript]

    return "\n".join(lines)
