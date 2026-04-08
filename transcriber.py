import whisper
import os
import subprocess
import tempfile
from pathlib import Path


def get_audio_duration(audio_path: str) -> float:
    """Get duration of audio/video file using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                audio_path
            ],
            capture_output=True, text=True
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def extract_audio_if_video(input_path: str) -> str:
    """
    If the input is a video file, extract audio to a temp WAV file.
    Returns path to audio file (may be same as input if already audio).
    """
    video_extensions = {".mp4", ".mkv", ".avi", ".mov", ".webm"}
    suffix = Path(input_path).suffix.lower()

    if suffix in video_extensions:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tmp.close()
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", input_path,
                "-vn",                          # no video
                "-acodec", "pcm_s16le",         # wav format
                "-ar", "16000",                 # 16kHz for Whisper
                "-ac", "1",                     # mono
                tmp.name
            ],
            capture_output=True
        )
        return tmp.name
    return input_path


def transcribe_audio(audio_path: str, model_name: str = "base") -> tuple[str, float]:
    """
    Transcribe audio using OpenAI Whisper.

    Args:
        audio_path: Path to audio or video file.
        model_name: Whisper model size (tiny/base/small/medium/large).

    Returns:
        (transcript_text, duration_seconds)
    """
    duration = get_audio_duration(audio_path)

    # Extract audio from video if needed
    audio_path = extract_audio_if_video(audio_path)

    model = whisper.load_model(model_name)
    result = model.transcribe(audio_path, fp16=False, verbose=False)

    transcript = result.get("text", "").strip()
    return transcript, duration
