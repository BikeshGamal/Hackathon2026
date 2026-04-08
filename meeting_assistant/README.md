# 🎙️ MeetMind — AI Meeting Assistant

> **100% local · zero cloud · full privacy**
> Built with Whisper + Ollama + Streamlit

---

## What it does

MeetMind turns any meeting recording into structured, actionable notes — entirely on your machine. No API keys, no subscriptions, no data leaving your device.

| Feature | Detail |
|---|---|
| 🎤 Audio/Video input | MP3, MP4, WAV, M4A, OGG, WEBM, MKV, AVI, MOV |
| 📝 Transcription | OpenAI Whisper (5 model sizes) |
| 🧠 AI summarization | Ollama with Llama 3, Mistral, Gemma2, etc. |
| 📋 Output | Summary · Decisions · Action items · Keywords · Sentiment |
| 💾 Export | Markdown · Plain text · Raw transcript |

---

## Prerequisites

### 1. Python 3.10+
```bash
python --version
```

### 2. FFmpeg
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows (Chocolatey)
choco install ffmpeg
```

### 3. Ollama
Download from [ollama.com](https://ollama.com) then pull a model:
```bash
ollama pull llama3
# or
ollama pull mistral
```

---

## Installation

```bash
# Clone or download the project
cd meeting_assistant

# Install Python dependencies
pip install -r requirements.txt
```

---

## Running the app

```bash
# Make sure Ollama is running in the background
ollama serve   # (usually starts automatically)

# Launch MeetMind
streamlit run app.py
```

Open your browser at **http://localhost:8501**

---

## Project Structure

```
meeting_assistant/
├── app.py                  # Main Streamlit UI
├── requirements.txt
├── README.md
└── utils/
    ├── __init__.py
    ├── transcriber.py      # Whisper transcription
    ├── summarizer.py       # Ollama summarization
    ├── audio_recorder.py   # Browser mic recorder component
    └── exporter.py         # Markdown / TXT export
```

---

## Model Guide

### Whisper models (transcription)

| Model | Size | Speed | Accuracy |
|---|---|---|---|
| tiny | 39 MB | Fastest | Basic |
| base | 74 MB | Fast | Good ✓ |
| small | 244 MB | Medium | Better |
| medium | 769 MB | Slow | Great |
| large | 1.5 GB | Slowest | Best |

### Ollama models (summarization)

| Model | Pull command | Notes |
|---|---|---|
| Llama 3 | `ollama pull llama3` | Best overall ✓ |
| Mistral | `ollama pull mistral` | Fast, efficient |
| Gemma 2 | `ollama pull gemma2` | Good for structured output |
| Phi-3 | `ollama pull phi3` | Lightweight |

---

## Tips

- **For CPU-only machines**: Use `tiny` or `base` Whisper + Mistral/Phi3
- **For GPU machines**: Use `medium` or `large` Whisper + Llama3 for best results
- **Long meetings**: The `base` Whisper model handles 1-hour meetings well on CPU
- **Video files**: FFmpeg extracts audio automatically — just upload the video

---

## Hackathon Notes

This project demonstrates:
- Local AI inference with no cloud dependency
- Full audio/video pipeline: input → transcription → NLP → structured output
- Clean, production-quality Streamlit UI
- Modular architecture for easy extension

**Possible extensions:**
- Speaker diarization (identify who said what)
- Real-time live transcription
- Calendar integration (auto-create follow-up events)
- Notion/Obsidian export plugin
- Multi-language support (Whisper supports 99 languages)

---

## License

MIT — free to use, modify, and distribute.
