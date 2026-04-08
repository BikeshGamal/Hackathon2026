import whisper
import subprocess
import tempfile
from pathlib import Path
import streamlit as st
import torch


@st.cache_resource(show_spinner=False)
def load_whisper_model(model_name: str):
    """Load and cache Whisper model — loads once, reused every time."""
    return whisper.load_model(model_name)


def get_device():
    """Auto-detect best available device."""
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def get_audio_duration(audio_path: str) -> float:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error",
             "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1",
             audio_path],
            capture_output=True, text=True
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def extract_audio_if_video(input_path: str) -> str:
    video_extensions = {".mp4", ".mkv", ".avi", ".mov", ".webm"}
    suffix = Path(input_path).suffix.lower()
    if suffix in video_extensions:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tmp.close()
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path,
             "-vn", "-acodec", "pcm_s16le",
             "-ar", "16000", "-ac", "1",
             tmp.name],
            capture_output=True
        )
        return tmp.name
    return input_path


def transcribe_audio(
    audio_path: str,
    model_name: str = "tiny",
    language: str = None,
    translate_to_english: bool = False,
) -> tuple[str, float, str]:
    """
    Transcribe audio using OpenAI Whisper — optimized for speed.
    """
    duration = get_audio_duration(audio_path)
    audio_path = extract_audio_if_video(audio_path)
    device = get_device()
    model = load_whisper_model(model_name)

    task = "translate" if translate_to_english else "transcribe"

    result = model.transcribe(
        audio_path,
        fp16=device == "cuda",          # fp16 only on GPU
        verbose=False,
        condition_on_previous_text=False,  # faster
        temperature=0,                     # greedy = fastest
        language=language,
        task=task,
        beam_size=1,                       # no beam search = much faster
        best_of=1,                         # no sampling = faster
        compression_ratio_threshold=2.4,
        no_speech_threshold=0.6,
    )

    transcript = result.get("text", "").strip()
    detected_lang = result.get("language", "unknown")
    return transcript, duration, detected_lang