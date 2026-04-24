import streamlit as st
import os
import tempfile
import time
from pathlib import Path
from utils.transcriber import transcribe_audio
from utils.summarizer import generate_meeting_notes
from utils.exporter import export_to_markdown, export_to_txt
from utils.emailer import load_team_config, save_team_config, send_meeting_email, test_smtp_connection, SMTP_PRESETS
import datetime

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MeetMind — AI Meeting Assistant",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500&display=swap');

/* Base */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    font-weight: 300;
}

/* App background */
.stApp {
    background: #0d0f14;
    color: #e8e4dc;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #111318 !important;
    border-right: 1px solid #1e2028;
}
section[data-testid="stSidebar"] * {
    color: #a0a8b8 !important;
}

/* Hero title */
.hero-title {
    font-family: 'DM Serif Display', serif;
    font-size: 3rem;
    font-weight: 400;
    color: #e8e4dc;
    letter-spacing: -0.02em;
    line-height: 1.1;
    margin: 0;
}
.hero-sub {
    font-size: 1rem;
    color: #c8d0dc;
    margin-top: 0.5rem;
    font-weight: 300;
    letter-spacing: 0.04em;
}
.accent { color: #7dd3c0; }

/* Cards */
.glass-card {
    background: #13161d;
    border: 1px solid #1e2230;
    border-radius: 16px;
    padding: 1.75rem;
    margin-bottom: 1.25rem;
}
.glass-card-accent {
    background: #0e1a1f;
    border: 1px solid #1a3030;
    border-radius: 16px;
    padding: 1.75rem;
    margin-bottom: 1.25rem;
}

/* Section label */
.section-label {
    font-size: 0.65rem;
    font-weight: 500;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #c8d0dc;
    margin-bottom: 1rem;
}

/* Transcript box */
.transcript-box {
    background: #0a0c10;
    border: 1px solid #1a1e28;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    font-size: 0.9rem;
    line-height: 1.85;
    color: #8090a8;
    max-height: 280px;
    overflow-y: auto;
    font-family: 'DM Mono', 'Courier New', monospace;
}

/* Summary sections */
.summary-section {
    margin-bottom: 1.5rem;
}
.summary-header {
    font-size: 0.65rem;
    font-weight: 500;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #7dd3c0;
    margin-bottom: 0.6rem;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid #1a2e2e;
}
.summary-body {
    font-size: 0.92rem;
    line-height: 1.8;
    color: #c8d0dc;
    font-weight: 300;
}
.action-item {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.6rem 0;
    border-bottom: 1px solid #1a1e28;
    font-size: 0.9rem;
    color: #c0c8d8;
}
.action-bullet {
    color: #7dd3c0;
    font-size: 1.2rem;
    margin-top: -2px;
    flex-shrink: 0;
}

/* Status badge */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #0e1a1a;
    border: 1px solid #1a3a3a;
    color: #7dd3c0;
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 4px 12px;
    border-radius: 100px;
}
.dot {
    width: 6px; height: 6px;
    background: #7dd3c0;
    border-radius: 50%;
    display: inline-block;
    animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}

/* Metric cards */
.metric-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin-bottom: 1.25rem;
}
.metric-card {
    background: #0e1015;
    border: 1px solid #1a1e28;
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
}
.metric-val {
    font-family: 'DM Serif Display', serif;
    font-size: 1.6rem;
    color: #e8e4dc;
}
.metric-label {
    font-size: 0.68rem;
    color: #c8d0dc;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-top: 2px;
}

/* Divider */
.teal-divider {
    border: none;
    border-top: 1px solid #1a2e2e;
    margin: 1.25rem 0;
}

/* Buttons - override streamlit */
.stButton > button {
    background: #7dd3c0 !important;
    color: #0a0c10 !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
    padding: 0.6rem 1.5rem !important;
    letter-spacing: 0.02em !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: #5bbfaa !important;
    transform: translateY(-1px) !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: #0e1015 !important;
    border: 1.5px dashed #1e2530 !important;
    border-radius: 12px !important;
}

/* Progress / spinner */
.stSpinner > div {
    border-top-color: #7dd3c0 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    background: #13161d !important;
    border: 1px solid #1e2230 !important;
    border-radius: 8px !important;
    color: #5a6070 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase;
}
.stTabs [aria-selected="true"] {
    background: #0e1a1f !important;
    border-color: #1a3030 !important;
    color: #7dd3c0 !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #2a3040; border-radius: 4px; }

/* Hide streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ─────────────────────────────────────────────────────────
if "transcript" not in st.session_state:
    st.session_state.transcript = ""
if "meeting_notes" not in st.session_state:
    st.session_state.meeting_notes = {}
if "processing_done" not in st.session_state:
    st.session_state.processing_done = False
if "audio_duration" not in st.session_state:
    st.session_state.audio_duration = 0
if "word_count" not in st.session_state:
    st.session_state.word_count = 0
if "meeting_time" not in st.session_state:
    st.session_state.meeting_time = ""
if "detected_language" not in st.session_state:
    st.session_state.detected_language = ""
if "show_team_editor" not in st.session_state:
    st.session_state.show_team_editor = False
if "email_sent" not in st.session_state:
    st.session_state.email_sent = False
if "email_message" not in st.session_state:
    st.session_state.email_message = ""
if "manual_text" not in st.session_state:
    st.session_state.manual_text = ""

# ─── Load team config ──────────────────────────────────────────────────────────
team_config = load_team_config()

# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='margin-bottom:2rem;'>
        <div style='font-family: DM Serif Display, serif; font-size:1.3rem; color:#e8e4dc;'>MeetMind</div>
        <div style='font-size:0.7rem; color:#3d4455; letter-spacing:0.1em; text-transform:uppercase;'>AI Meeting Assistant</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-label">Model Settings</div>', unsafe_allow_html=True)

    whisper_model = st.selectbox(
        "Whisper model",
        ["tiny", "base", "small", "medium", "large"],
        index=0,
        help="tiny = fastest (recommended). base = balanced. small/medium = better accuracy for non-English."
    )

    SPEED_LABELS = {
        "tiny":   ("⚡⚡⚡ Fastest", "#7dd3c0"),
        "base":   ("⚡⚡  Balanced", "#a0c8a0"),
        "small":  ("⚡    Slower",  "#c8c080"),
        "medium": ("🐢   Slow",     "#c89060"),
        "large":  ("🐢🐢 Slowest", "#c86060"),
    }
    spd_text, spd_color = SPEED_LABELS.get(whisper_model, ("", "#888"))
    st.markdown(f'''
    <div style="font-size:0.75rem; color:{spd_color}; margin-top:-0.5rem; margin-bottom:0.5rem;">
        {spd_text}
    </div>''', unsafe_allow_html=True)

    ollama_model = st.selectbox(
        "Ollama model",
        ["llama3", "llama3.1", "mistral", "gemma2", "phi3"],
        index=0,
        help="Must be pulled via: ollama pull <model>"
    )

    st.markdown('<hr style="border-color:#1e2028; margin:1.5rem 0;">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Language</div>', unsafe_allow_html=True)

    LANGUAGES = {
        "Auto-detect": None,
        "English": "en",
        "Nepali (नेपाली)": "ne",
        "Hindi (हिन्दी)": "hi",
        "Chinese (中文)": "zh",
        "Spanish (Español)": "es",
        "French (Français)": "fr",
        "Arabic (العربية)": "ar",
        "Portuguese (Português)": "pt",
        "Russian (Русский)": "ru",
        "German (Deutsch)": "de",
        "Japanese (日本語)": "ja",
        "Korean (한국어)": "ko",
        "Italian (Italiano)": "it",
        "Turkish (Türkçe)": "tr",
        "Bengali (বাংলা)": "bn",
        "Urdu (اردو)": "ur",
        "Vietnamese (Tiếng Việt)": "vi",
        "Thai (ภาษาไทย)": "th",
        "Indonesian": "id",
        "Malay": "ms",
    }

    selected_lang_label = st.selectbox(
        "Meeting language",
        list(LANGUAGES.keys()),
        index=0,
        help="Select the language spoken in the meeting. Auto-detect works well for most languages."
    )
    selected_language = LANGUAGES[selected_lang_label]

    translate_to_english = st.toggle(
        "Translate to English",
        value=False,
        help="Transcribe in original language AND translate output to English. Useful for non-English meetings."
    )

    st.markdown('<hr style="border-color:#1e2028; margin:1.5rem 0;">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Summary Options</div>', unsafe_allow_html=True)

    include_sentiment = st.toggle("Sentiment analysis", value=True)
    include_keywords = st.toggle("Key topics", value=True)
    include_followup = st.toggle("Follow-up questions", value=False)

    st.markdown('<hr style="border-color:#1e2028; margin:1.5rem 0;">', unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size:0.72rem; color:#2a3040; line-height:1.8;'>
        100% local · no internet<br>
        Whisper + Ollama + Streamlit<br>
        <span style='color:#3d4455;'>Built for hackathon 2025</span>
    </div>
    """, unsafe_allow_html=True)

# ─── Hero Header ───────────────────────────────────────────────────────────────
col_title, col_badge = st.columns([4, 1])
with col_title:
    st.markdown("""
    <div style='padding: 2rem 0 1rem;'>
        <div class='hero-title'>Meet<span class='accent'>Mind</span></div>
        <div class='hero-sub'>Local AI · Zero cloud · Full privacy</div>
    </div>
    """, unsafe_allow_html=True)
with col_badge:
    st.markdown("""
    <div style='padding: 2.5rem 0 1rem; text-align:right;'>
        <span class='status-badge'><span class='dot'></span>Offline</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<hr style="border:none;border-top:1px solid #1a1e28;margin:0 0 1.5rem;">', unsafe_allow_html=True)

# ─── Main Layout ───────────────────────────────────────────────────────────────
left_col, right_col = st.columns([1, 1.3], gap="large")

# ══════════════════════════════════════════════════════════════════════════════
# LEFT COLUMN — Input
# ══════════════════════════════════════════════════════════════════════════════════════
with left_col:
    st.markdown('<div class="section-label">Upload Meeting File</div>', unsafe_allow_html=True)

    audio_path = None

    st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Drop your meeting file here",
        type=["mp3", "mp4", "wav", "m4a", "ogg", "webm", "mkv", "avi", "mov"],
        label_visibility="collapsed"
    )
    st.markdown("""
    <div style='font-size:0.75rem; color:#c8d0dc; margin-top:0.5rem; text-align:center;'>
        Supports MP3, MP4, WAV, M4A, OGG, WEBM, MKV, AVI, MOV
    </div>
    """, unsafe_allow_html=True)

    if uploaded:
        suffix = Path(uploaded.name).suffix
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(uploaded.read())
        tmp.flush()
        audio_path = tmp.name

        st.markdown("""
        <div class='glass-card' style='margin-top:1rem; padding:1rem;'>
            <div style='display:flex; align-items:center; gap:10px;'>
                <div style='font-size:1.5rem;'>🎵</div>
                <div>
                    <div style='font-size:0.85rem; color:#c8d0dc; font-weight:500;'>{name}</div>
                    <div style='font-size:0.72rem; color:#c8d0dc;'>{size} KB · Ready to process</div>
                </div>
            </div>
        </div>
        """.format(
            name=uploaded.name,
            size=round(uploaded.size / 1024)
        ), unsafe_allow_html=True)

        with open(audio_path, "rb") as f:
            st.audio(f.read(), format=f"audio/{suffix.strip('.')}")

    st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Paste Meeting Text</div>', unsafe_allow_html=True)

    text_area_key = "manual_text" if not uploaded else "manual_text_uploaded"
    text_area_value = "" if uploaded else st.session_state.get("manual_text", "")

    st.text_area(
        "Your meeting transcript",
        value=text_area_value,
        height=180,
        placeholder="Paste your meeting transcript or notes here to skip transcription...",
        key=text_area_key
    )

    # ── Process Button ─────────────────────────────────────────────────────────
    st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)

    manual_text = "" if audio_path else st.session_state.get("manual_text", "").strip()
    has_input = bool(audio_path or manual_text)

    if has_input:
        if st.button("⚡ Process Meeting", use_container_width=True):
            st.session_state.processing_done = False
            st.session_state.transcript = ""
            st.session_state.meeting_notes = {}
            st.session_state.email_sent = False
            st.session_state.email_message = ""
            st.session_state.meeting_time = datetime.datetime.now().strftime("%B %d, %Y · %H:%M")

            if manual_text:
                transcript = manual_text
                duration = 0
                detected_lang = selected_language or ""
                st.session_state.transcript = transcript
                st.session_state.audio_duration = duration
                st.session_state.word_count = len(transcript.split())
                st.session_state.detected_language = detected_lang
            else:
                # Step 1: Transcribe
                lang_label = selected_lang_label if selected_lang_label != "Auto-detect" else "auto-detecting language"
                with st.spinner(f"Transcribing audio with Whisper ({lang_label})…"):
                    try:
                        transcript, duration, detected_lang = transcribe_audio(
                            audio_path,
                            model_name=whisper_model,
                            language=selected_language,
                            translate_to_english=translate_to_english,
                        )
                        st.session_state.transcript = transcript
                        st.session_state.audio_duration = duration
                        st.session_state.word_count = len(transcript.split())
                        st.session_state.detected_language = detected_lang
                    except Exception as e:
                        st.error(f"Transcription failed: {e}")
                        st.stop()

            # Step 2: Summarize
            with st.spinner("Generating meeting notes with Llama 3…"):
                try:
                    notes = generate_meeting_notes(
                        st.session_state.transcript,
                        model=ollama_model,
                        include_sentiment=include_sentiment,
                        include_keywords=include_keywords,
                        include_followup=include_followup,
                    )
                    st.session_state.meeting_notes = notes
                    st.session_state.processing_done = True
                except Exception as e:
                    st.error(f"Summarization failed: {e}")
                    st.stop()

            st.rerun()

    # ── Transcript Preview ─────────────────────────────────────────────────────
    if st.session_state.transcript:
        st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Raw Transcript</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class='transcript-box'>{st.session_state.transcript}</div>
        """, unsafe_allow_html=True)

    # ── Mail Service Panel ─────────────────────────────────────────────────────
    if st.session_state.processing_done:
        st.markdown('<div style="height:1.5rem"></div>', unsafe_allow_html=True)
        tc = load_team_config()
        members_left = tc.get("team_members", [])
        s_email = tc.get("sender_email", "")
        s_name  = tc.get("sender_name", "")
        s_provider = tc.get("smtp_provider", "—")
        configured = bool(s_email)

        dot_color  = "#7dd3c0" if configured else "#3d4455"
        dot_status = "Configured" if configured else "Not configured"

        # Build members rows html
        rows_html = ""
        for m in members_left[:5]:
            initials = "".join(w[0].upper() for w in m["name"].split()[:2])
            rows_html += f"""<div style="display:flex;align-items:center;gap:8px;
                padding:6px 0;border-bottom:1px solid #1a1e28;">
                <div style="width:28px;height:28px;border-radius:50%;background:#0e1a1f;
                    border:1px solid #1a3030;display:flex;align-items:center;
                    justify-content:center;font-size:0.62rem;font-weight:500;
                    color:#7dd3c0;flex-shrink:0;">{initials}</div>
                <div style="min-width:0;">
                    <div style="font-size:0.8rem;color:#c0c8d8;white-space:nowrap;
                        overflow:hidden;text-overflow:ellipsis;">{m['name']}</div>
                    <div style="font-size:0.66rem;color:#3d4455;white-space:nowrap;
                        overflow:hidden;text-overflow:ellipsis;">{m['email']}</div>
                </div></div>"""

        extra = f"<div style='font-size:0.68rem;color:#3d4455;padding-top:6px;'>+{len(members_left)-5} more</div>" if len(members_left) > 5 else ""
        no_members = "<div style='font-size:0.78rem;color:#3d4455;padding:0.5rem 0;'>No recipients added yet</div>" if not members_left else ""

        st.markdown(f"""<div style="background:#0e1015;border:1px solid #1a1e28;
            border-radius:16px;padding:1.25rem 1.5rem;">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem;">
                <div style="font-size:0.6rem;font-weight:500;letter-spacing:0.15em;
                    text-transform:uppercase;color:#c8d0dc;">Mail Service</div>
                <div style="display:flex;align-items:center;gap:5px;">
                    <div style="width:6px;height:6px;border-radius:50%;background:{dot_color};"></div>
                    <span style="font-size:0.65rem;color:{dot_color};">{dot_status}</span>
                </div>
            </div>
            <div style="display:flex;align-items:center;gap:10px;padding-bottom:1rem;
                margin-bottom:1rem;border-bottom:1px solid #1a1e28;">
                <div style="width:38px;height:38px;border-radius:10px;background:#0d9488;
                    display:flex;align-items:center;justify-content:center;
                    font-size:1.1rem;flex-shrink:0;">✉</div>
                <div style="min-width:0;">
                    <div style="font-size:0.84rem;color:#c8d0dc;font-weight:500;
                        white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                        {s_name if s_name else "Not configured"}</div>
                    <div style="font-size:0.68rem;color:#c8d0dc;white-space:nowrap;
                        overflow:hidden;text-overflow:ellipsis;">
                        {s_email if s_email else "Set up email to send notes"}</div>
                </div>
            </div>
            <div style="font-size:0.6rem;font-weight:500;letter-spacing:0.1em;
                text-transform:uppercase;color:#c8d0dc;margin-bottom:0.5rem;">
                Recipients · {len(members_left)}</div>
            {rows_html}{extra}{no_members}
            <div style="margin-top:1rem;padding-top:0.75rem;border-top:1px solid #1a1e28;
                display:flex;justify-content:space-between;align-items:center;">
                <div style="font-size:0.65rem;color:#c8d0dc;">Provider</div>
                <div style="font-size:0.7rem;color:#c8d0dc;font-weight:500;">{s_provider}</div>
            </div>
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# RIGHT COLUMN — Results
# ══════════════════════════════════════════════════════════════════════════════
with right_col:
    st.markdown('<div class="section-label">Meeting Notes</div>', unsafe_allow_html=True)

    if not st.session_state.processing_done:
        st.markdown("""
        <div class='glass-card' style='text-align:center; padding:3rem 2rem; min-height:400px; display:flex; flex-direction:column; align-items:center; justify-content:center;'>
            <div style='font-size:3rem; margin-bottom:1rem; opacity:0.3;'>📋</div>
            <div style='font-size:0.9rem; color:#3d4455; font-weight:300; line-height:1.8;'>
                Upload or record a meeting,<br>then click <strong style='color:#5a6070;'>Process Meeting</strong><br>to generate AI-powered notes.
            </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        notes = st.session_state.meeting_notes

        # Metrics row
        dur = st.session_state.audio_duration
        dur_fmt = f"{int(dur // 60)}m {int(dur % 60)}s" if dur else "—"
        st.markdown(f"""
        <div class='metric-row'>
            <div class='metric-card'>
                <div class='metric-val'>{dur_fmt}</div>
                <div class='metric-label'>Duration</div>
            </div>
            <div class='metric-card'>
                <div class='metric-val'>{st.session_state.word_count:,}</div>
                <div class='metric-label'>Words</div>
            </div>
            <div class='metric-card'>
                <div class='metric-val'>{len(notes.get("action_items", []))}</div>
                <div class='metric-label'>Actions</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        lang_display = st.session_state.detected_language.upper() if st.session_state.detected_language else "—"
        st.markdown(f"""
        <div style='font-size:0.72rem; color:#c8d0dc; margin-bottom:1rem; letter-spacing:0.05em; display:flex; gap:1rem;'>
            <span>Processed {st.session_state.meeting_time}</span>
            <span style='color:#c8d0dc;'>Language detected: <span style='color:#7dd3c0;'>{lang_display}</span></span>
        </div>
        """, unsafe_allow_html=True)

        # ── Summary ────────────────────────────────────────────────────────────
        if notes.get("summary"):
            st.markdown("""
            <div class='glass-card-accent'>
                <div class='summary-section'>
                    <div class='summary-header'>Summary</div>
                    <div class='summary-body'>{}</div>
                </div>
            </div>
            """.format(notes["summary"].replace("\n", "<br>")), unsafe_allow_html=True)

        # ── Key Decisions ──────────────────────────────────────────────────────
        if notes.get("decisions"):
            st.markdown("""
            <div class='glass-card'>
                <div class='summary-header'>Key Decisions</div>
                {}
            </div>
            """.format("".join([
                f"<div class='action-item'><span class='action-bullet'>◆</span><span>{d}</span></div>"
                for d in notes["decisions"]
            ])), unsafe_allow_html=True)

        # ── Action Items ───────────────────────────────────────────────────────
        if notes.get("action_items"):
            st.markdown("""
            <div class='glass-card'>
                <div class='summary-header'>Action Items</div>
                {}
            </div>
            """.format("".join([
                f"<div class='action-item'><span class='action-bullet'>→</span><span>{a}</span></div>"
                for a in notes["action_items"]
            ])), unsafe_allow_html=True)

        # ── Keywords ───────────────────────────────────────────────────────────
        if include_keywords and notes.get("keywords"):
            keywords_html = "".join([
                f"<span style='background:#0e1a1f;border:1px solid #1a3030;color:#7dd3c0;font-size:0.75rem;padding:3px 10px;border-radius:100px;margin:3px;display:inline-block;'>{k}</span>"
                for k in notes["keywords"]
            ])
            st.markdown(f"""
            <div class='glass-card'>
                <div class='summary-header'>Key Topics</div>
                <div style='margin-top:0.25rem;'>{keywords_html}</div>
            </div>
            """, unsafe_allow_html=True)

        # ── Sentiment ─────────────────────────────────────────────────────────
        if include_sentiment and notes.get("sentiment"):
            s = notes["sentiment"].lower()
            s_color = "#7dd3c0" if "positive" in s else "#e8a87c" if "neutral" in s else "#e87c7c"
            s_icon = "↑" if "positive" in s else "→" if "neutral" in s else "↓"
            st.markdown(f"""
            <div class='glass-card' style='padding:1rem 1.5rem;'>
                <div class='summary-header'>Meeting Sentiment</div>
                <div style='display:flex; align-items:center; gap:10px;'>
                    <span style='font-size:1.4rem; color:{s_color};'>{s_icon}</span>
                    <span style='font-size:0.92rem; color:{s_color}; font-weight:500;'>{notes["sentiment"]}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Follow-up Questions ────────────────────────────────────────────────
        if include_followup and notes.get("followup_questions"):
            st.markdown("""
            <div class='glass-card'>
                <div class='summary-header'>Follow-up Questions</div>
                {}
            </div>
            """.format("".join([
                f"<div class='action-item'><span class='action-bullet'>?</span><span>{q}</span></div>"
                for q in notes["followup_questions"]
            ])), unsafe_allow_html=True)

        # ── Export Buttons ─────────────────────────────────────────────────────
        st.markdown('<hr class="teal-divider">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Export</div>', unsafe_allow_html=True)

        md_content = export_to_markdown(st.session_state.transcript, notes, st.session_state.meeting_time)
        txt_content = export_to_txt(st.session_state.transcript, notes, st.session_state.meeting_time)

        ecol1, ecol2, ecol3 = st.columns(3)
        with ecol1:
            st.download_button("⬇ Markdown", data=md_content, file_name="meeting_notes.md",
                mime="text/markdown", use_container_width=True)
        with ecol2:
            st.download_button("⬇ Plain Text", data=txt_content, file_name="meeting_notes.txt",
                mime="text/plain", use_container_width=True)
        with ecol3:
            st.download_button("⬇ Transcript", data=st.session_state.transcript,
                file_name="transcript.txt", mime="text/plain", use_container_width=True)

        # ══════════════════════════════════════════════════════════════════════
        # EMAIL SECTION — added below export, UI unchanged above
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<hr class="teal-divider">', unsafe_allow_html=True)

        email_hdr_col, edit_btn_col = st.columns([3, 1])
        with email_hdr_col:
            st.markdown('<div class="section-label">Email to Team</div>', unsafe_allow_html=True)
        with edit_btn_col:
            if st.button("⚙ Edit Setup", use_container_width=True):
                st.session_state.show_team_editor = not st.session_state.show_team_editor
                # reset so editor always loads fresh from disk
                if "edit_members" in st.session_state:
                    del st.session_state["edit_members"]
                st.rerun()

        # ── Setup Editor ───────────────────────────────────────────────────────
        is_first_time = not team_config.get("sender_email")
        if st.session_state.show_team_editor or is_first_time:
            with st.expander("⚙ Email Setup — set once, saved automatically", expanded=True):
                providers = list(SMTP_PRESETS.keys())
                saved_provider = team_config.get("smtp_provider", "Gmail")
                provider = st.selectbox(
                    "Email provider", providers,
                    index=providers.index(saved_provider) if saved_provider in providers else 0,
                    key="cfg_provider",
                    help="Gmail, Outlook, Office 365, Yahoo, Zoho, or Custom SMTP"
                )
                preset = SMTP_PRESETS[provider]

                s_col1, s_col2 = st.columns(2)
                with s_col1:
                    st.text_input("Your name",  value=team_config.get("sender_name", ""),
                        placeholder="Ram Sharma",    key="cfg_sender_name")
                    st.text_input("Your email", value=team_config.get("sender_email", ""),
                        placeholder="ram@company.com", key="cfg_sender_email")
                with s_col2:
                    st.text_input("Email password", value=team_config.get("smtp_password", ""),
                        type="password", placeholder="Your email password", key="cfg_smtp_password")
                    if provider == "Custom":
                        st.text_input("SMTP host", value=team_config.get("smtp_host", ""),
                            placeholder="mail.company.com", key="cfg_smtp_host")
                    else:
                        st.session_state["cfg_smtp_host"] = preset["host"]
                        st.markdown(f"<div style='font-size:0.72rem;color:#5a6070;margin-top:0.5rem;'>SMTP: <code>{preset['host']}</code> · Port 587</div>", unsafe_allow_html=True)

                # Provider hints
                hints = {
                    "Gmail":           ("Gmail needs an App Password — enable 2FA first", "https://myaccount.google.com/apppasswords"),
                    "Outlook/Hotmail": ("Use your normal Outlook/Hotmail password", None),
                    "Office 365":      ("Use your work email password (IT may need to enable SMTP AUTH)", None),
                    "Yahoo":           ("Yahoo needs an App Password from Settings → Security", None),
                }
                if provider in hints:
                    hint_text, hint_link = hints[provider]
                    link_part = f' <a href="{hint_link}" style="color:#7dd3c0;" target="_blank">Setup →</a>' if hint_link else ""
                    st.markdown(f"<div style='font-size:0.72rem;color:#7dd3c0;background:#0a1a18;border:1px solid #1a3530;border-radius:6px;padding:6px 10px;margin:0.25rem 0 0.75rem;'>{hint_text}{link_part}</div>", unsafe_allow_html=True)

                # Test connection button
                if st.button("🔌 Test Connection", use_container_width=True):
                    with st.spinner("Testing…"):
                        ok, msg = test_smtp_connection({
                            "sender_email": st.session_state.get("cfg_sender_email", ""),
                            "smtp_password": st.session_state.get("cfg_smtp_password", ""),
                            "smtp_host": st.session_state.get("cfg_smtp_host", preset["host"]),
                            "smtp_port": 587,
                        })
                    if ok:
                        st.success(f"✓ {msg}")
                    else:
                        st.error(f"✗ {msg}")

                st.markdown('<hr style="border-color:#1e2028;margin:0.75rem 0;">', unsafe_allow_html=True)
                st.markdown("<div style='font-size:0.72rem;font-weight:500;color:#7dd3c0;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:0.5rem;'>Team Members</div>", unsafe_allow_html=True)

                # Use session state list so Add/Remove work instantly
                if "edit_members" not in st.session_state:
                    st.session_state.edit_members = [dict(m) for m in team_config.get("team_members", [])]

                # Show existing members with remove button
                to_remove = None
                for i, m in enumerate(st.session_state.edit_members):
                    mc1, mc2, mc3 = st.columns([2, 3, 0.5])
                    with mc1:
                        st.session_state.edit_members[i]["name"] = st.text_input(
                            "n", value=m["name"], key=f"mn_{i}",
                            label_visibility="collapsed", placeholder="Name")
                    with mc2:
                        st.session_state.edit_members[i]["email"] = st.text_input(
                            "e", value=m["email"], key=f"me_{i}",
                            label_visibility="collapsed", placeholder="email@company.com")
                    with mc3:
                        st.markdown('<div style="height:1.75rem"></div>', unsafe_allow_html=True)
                        if st.button("✕", key=f"rm_{i}", help="Remove"):
                            to_remove = i

                if to_remove is not None:
                    st.session_state.edit_members.pop(to_remove)
                    st.rerun()

                # Add new member row
                st.markdown('<div style="height:0.25rem"></div>', unsafe_allow_html=True)
                nc1, nc2, nc3 = st.columns([2, 3, 0.8])
                with nc1:
                    new_name = st.text_input("nn", label_visibility="collapsed",
                        placeholder="Name", key="new_name")
                with nc2:
                    new_email = st.text_input("ne", label_visibility="collapsed",
                        placeholder="email@company.com", key="new_email")
                with nc3:
                    st.markdown('<div style="height:1.75rem"></div>', unsafe_allow_html=True)
                    if st.button("＋", use_container_width=True, key="add_member", help="Add member"):
                        if new_name.strip() and new_email.strip():
                            st.session_state.edit_members.append(
                                {"name": new_name.strip(), "email": new_email.strip()})
                            st.rerun()

                if st.button("💾 Save Settings", use_container_width=True):
                    new_config = {
                        "sender_name":   st.session_state.get("cfg_sender_name", ""),
                        "sender_email":  st.session_state.get("cfg_sender_email", ""),
                        "smtp_password": st.session_state.get("cfg_smtp_password", ""),
                        "smtp_provider": st.session_state.get("cfg_provider", "Gmail"),
                        "smtp_host":     st.session_state.get("cfg_smtp_host", preset["host"]),
                        "smtp_port":     587,
                        "team_members":  st.session_state.edit_members,
                    }
                    save_team_config(new_config)
                    # reset editor state
                    for k in ["edit_members", "cfg_sender_name", "cfg_sender_email",
                              "cfg_smtp_password", "cfg_provider", "cfg_smtp_host"]:
                        st.session_state.pop(k, None)
                    st.session_state.show_team_editor = False
                    st.success("✓ Settings saved!")
                    st.rerun()

        # ── Send Panel ─────────────────────────────────────────────────────────
        members = team_config.get("team_members", [])

        if not team_config.get("sender_email"):
            st.markdown("<div style='font-size:0.82rem;color:#c8d0dc;padding:0.25rem 0;'>Click ⚙ Edit Setup to configure your email and team members.</div>", unsafe_allow_html=True)

        elif not members:
            st.markdown("<div style='font-size:0.82rem;color:#c8d0dc;padding:0.25rem 0;'>No team members yet. Click ⚙ Edit Setup to add recipients.</div>", unsafe_allow_html=True)

        else:
            st.markdown("<div style='font-size:0.75rem;color:#c8d0dc;margin-bottom:0.4rem;'>Select recipients:</div>", unsafe_allow_html=True)
            selected_recipients = []
            for m in members:
                if st.checkbox(f"{m['name']}   ·   {m['email']}", value=True, key=f"chk_{m['email']}"):
                    selected_recipients.append(m["email"])

            st.markdown('<div style="height:0.4rem"></div>', unsafe_allow_html=True)
            custom_subject = st.text_input(
                "subj", label_visibility="collapsed",
                value=f"Meeting Notes — {st.session_state.meeting_time}",
                placeholder="Email subject", key="email_subject"
            )

            if st.button("📧 Send Meeting Notes", use_container_width=True):
                if not selected_recipients:
                    st.warning("Select at least one recipient.")
                else:
                    with st.spinner(f"Sending to {len(selected_recipients)} recipient(s)…"):
                        success, msg = send_meeting_email(
                            config=team_config,
                            notes=notes,
                            meeting_time=st.session_state.meeting_time,
                            recipient_emails=selected_recipients,
                            subject=custom_subject,
                        )
                    st.session_state.email_sent = success
                    st.session_state.email_message = msg
                    st.rerun()

            if st.session_state.email_sent:
                st.success(f"✓ {st.session_state.email_message}")
            elif st.session_state.email_message:
                st.error(st.session_state.email_message)