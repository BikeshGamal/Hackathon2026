import streamlit as st
import os
import tempfile
import time
from pathlib import Path
from utils.transcriber import transcribe_audio
from utils.summarizer import generate_meeting_notes
from utils.audio_recorder import record_audio_component
from utils.exporter import export_to_markdown, export_to_txt
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
    color: #5a6070;
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
    color: #3d4455;
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
    color: #3d4455;
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
        index=1,
        help="Larger = more accurate but slower. 'base' is good for most meetings."
    )

    ollama_model = st.selectbox(
        "Ollama model",
        ["llama3", "llama3.1", "mistral", "gemma2", "phi3"],
        index=0,
        help="Must be pulled via: ollama pull <model>"
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
# ══════════════════════════════════════════════════════════════════════════════
with left_col:
    st.markdown('<div class="section-label">Input</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Upload File", "Record Audio"])

    audio_path = None

    # ── Tab 1: Upload ──────────────────────────────────────────────────────────
    with tab1:
        st.markdown('<div style="height:0.75rem"></div>', unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "Drop your meeting file here",
            type=["mp3", "mp4", "wav", "m4a", "ogg", "webm", "mkv", "avi", "mov"],
            label_visibility="collapsed"
        )
        st.markdown("""
        <div style='font-size:0.75rem; color:#3d4455; margin-top:0.5rem; text-align:center;'>
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
                        <div style='font-size:0.85rem; color:#c0c8d8; font-weight:500;'>{name}</div>
                        <div style='font-size:0.72rem; color:#3d4455;'>{size} KB · Ready to process</div>
                    </div>
                </div>
            </div>
            """.format(
                name=uploaded.name,
                size=round(uploaded.size / 1024)
            ), unsafe_allow_html=True)

            # Show audio player
            with open(audio_path, "rb") as f:
                st.audio(f.read(), format=f"audio/{suffix.strip('.')}")

    # ── Tab 2: Record ─────────────────────────────────────────────────────────
    with tab2:
        st.markdown('<div style="height:0.75rem"></div>', unsafe_allow_html=True)
        st.markdown("""
        <div class='glass-card' style='text-align:center; padding:2rem;'>
            <div style='font-size:2.5rem; margin-bottom:1rem;'>🎙️</div>
            <div style='font-size:0.85rem; color:#8090a8; margin-bottom:1rem; line-height:1.6;'>
                Use the recorder below to capture your meeting directly in the browser.
            </div>
        </div>
        """, unsafe_allow_html=True)

        recorded = record_audio_component()
        if recorded:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            tmp.write(recorded)
            tmp.flush()
            audio_path = tmp.name
            st.audio(recorded, format="audio/wav")
            st.success("Recording saved! Click 'Process Meeting' below.")

    # ── Process Button ─────────────────────────────────────────────────────────
    st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)

    if audio_path:
        if st.button("⚡ Process Meeting", use_container_width=True):
            st.session_state.processing_done = False
            st.session_state.transcript = ""
            st.session_state.meeting_notes = {}
            st.session_state.meeting_time = datetime.datetime.now().strftime("%B %d, %Y · %H:%M")

            # Step 1: Transcribe
            with st.spinner("Transcribing audio with Whisper…"):
                try:
                    transcript, duration = transcribe_audio(audio_path, model_name=whisper_model)
                    st.session_state.transcript = transcript
                    st.session_state.audio_duration = duration
                    st.session_state.word_count = len(transcript.split())
                except Exception as e:
                    st.error(f"Transcription failed: {e}")
                    st.stop()

            # Step 2: Summarize
            with st.spinner("Generating meeting notes with Llama 3…"):
                try:
                    notes = generate_meeting_notes(
                        transcript,
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

        st.markdown(f"""
        <div style='font-size:0.72rem; color:#2a3040; margin-bottom:1rem; letter-spacing:0.05em;'>
            Processed {st.session_state.meeting_time}
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

        ecol1, ecol2, ecol3 = st.columns(3)
        with ecol1:
            md_content = export_to_markdown(
                st.session_state.transcript,
                notes,
                st.session_state.meeting_time
            )
            st.download_button(
                "⬇ Markdown",
                data=md_content,
                file_name="meeting_notes.md",
                mime="text/markdown",
                use_container_width=True
            )
        with ecol2:
            txt_content = export_to_txt(
                st.session_state.transcript,
                notes,
                st.session_state.meeting_time
            )
            st.download_button(
                "⬇ Plain Text",
                data=txt_content,
                file_name="meeting_notes.txt",
                mime="text/plain",
                use_container_width=True
            )
        with ecol3:
            st.download_button(
                "⬇ Transcript",
                data=st.session_state.transcript,
                file_name="transcript.txt",
                mime="text/plain",
                use_container_width=True
            )