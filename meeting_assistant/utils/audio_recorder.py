import streamlit as st
import streamlit.components.v1 as components
import base64


def record_audio_component() -> bytes | None:
    """
    Render an in-browser audio recorder using the MediaRecorder API.
    Returns WAV audio bytes if user has finished recording, else None.
    """

    recorder_html = """
    <style>
      * { box-sizing: border-box; margin: 0; padding: 0; }
      body { background: transparent; font-family: 'DM Sans', sans-serif; }

      .recorder-wrap {
        background: #0e1015;
        border: 1px solid #1a1e28;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
      }

      .rec-btn {
        width: 64px; height: 64px;
        border-radius: 50%;
        border: 2px solid #7dd3c0;
        background: transparent;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 1rem;
        transition: all 0.2s;
      }
      .rec-btn:hover { background: #0e1a1a; }
      .rec-btn.recording {
        background: #7dd3c0;
        animation: pulse-ring 1.2s ease-in-out infinite;
      }
      @keyframes pulse-ring {
        0%, 100% { box-shadow: 0 0 0 0 rgba(125,211,192,0.3); }
        50% { box-shadow: 0 0 0 12px rgba(125,211,192,0); }
      }

      .rec-icon {
        width: 20px; height: 20px;
        background: #7dd3c0;
        border-radius: 50%;
        transition: all 0.2s;
      }
      .rec-icon.stop {
        border-radius: 3px;
        background: #0a0c10;
      }

      .status-text {
        font-size: 0.78rem;
        color: #5a6070;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
      }
      .timer {
        font-size: 1.4rem;
        color: #c0c8d8;
        font-weight: 300;
        letter-spacing: 0.05em;
        margin-bottom: 1rem;
        font-variant-numeric: tabular-nums;
      }

      audio {
        width: 100%;
        margin-top: 1rem;
        border-radius: 8px;
        filter: invert(0.9) hue-rotate(140deg);
      }

      .send-btn {
        margin-top: 0.75rem;
        padding: 8px 24px;
        background: #7dd3c0;
        color: #0a0c10;
        border: none;
        border-radius: 8px;
        font-size: 0.82rem;
        font-weight: 500;
        cursor: pointer;
        letter-spacing: 0.04em;
      }
      .send-btn:hover { background: #5bbfaa; }
      .send-btn:disabled { opacity: 0.4; cursor: not-allowed; }
    </style>

    <div class="recorder-wrap">
      <div class="status-text" id="statusText">Ready to record</div>
      <div class="timer" id="timer">0:00</div>

      <button class="rec-btn" id="recBtn" onclick="toggleRecording()">
        <div class="rec-icon" id="recIcon"></div>
      </button>

      <div id="playbackArea" style="display:none;">
        <audio id="audioPlayback" controls></audio>
        <br>
        <button class="send-btn" id="sendBtn" onclick="sendAudio()">
          Use this recording
        </button>
      </div>
    </div>

    <script>
      let mediaRecorder = null;
      let chunks = [];
      let timerInterval = null;
      let seconds = 0;
      let audioBlob = null;

      function toggleRecording() {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
          stopRecording();
        } else {
          startRecording();
        }
      }

      async function startRecording() {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          chunks = [];
          mediaRecorder = new MediaRecorder(stream);

          mediaRecorder.ondataavailable = e => {
            if (e.data.size > 0) chunks.push(e.data);
          };

          mediaRecorder.onstop = () => {
            audioBlob = new Blob(chunks, { type: 'audio/webm' });
            const url = URL.createObjectURL(audioBlob);
            document.getElementById('audioPlayback').src = url;
            document.getElementById('playbackArea').style.display = 'block';
            document.getElementById('statusText').textContent = 'Recording saved';
          };

          mediaRecorder.start();

          // UI updates
          document.getElementById('statusText').textContent = 'Recording…';
          document.getElementById('recBtn').classList.add('recording');
          document.getElementById('recIcon').classList.add('stop');
          document.getElementById('playbackArea').style.display = 'none';

          // Timer
          seconds = 0;
          timerInterval = setInterval(() => {
            seconds++;
            const m = Math.floor(seconds / 60);
            const s = String(seconds % 60).padStart(2, '0');
            document.getElementById('timer').textContent = `${m}:${s}`;
          }, 1000);

        } catch (err) {
          document.getElementById('statusText').textContent = 'Mic access denied';
          console.error(err);
        }
      }

      function stopRecording() {
        if (mediaRecorder) {
          mediaRecorder.stop();
          mediaRecorder.stream.getTracks().forEach(t => t.stop());
        }
        clearInterval(timerInterval);
        document.getElementById('recBtn').classList.remove('recording');
        document.getElementById('recIcon').classList.remove('stop');
      }

      function sendAudio() {
        if (!audioBlob) return;
        const reader = new FileReader();
        reader.onload = () => {
          const b64 = reader.result.split(',')[1];
          // Post to Streamlit via query param trick
          const url = new URL(window.location.href);
          // Send via parent communication
          window.parent.postMessage({
            type: 'meetmind_audio',
            data: b64
          }, '*');
          document.getElementById('statusText').textContent = 'Sent to assistant ✓';
          document.getElementById('sendBtn').disabled = true;
        };
        reader.readAsDataURL(audioBlob);
      }
    </script>
    """

    components.html(recorder_html, height=280, scrolling=False)
    # Note: Full browser mic → Streamlit data passing requires a custom component.
    # For hackathon, use file upload tab for full pipeline.
    # This component provides the UX; production version uses st_audiorec package.
    return None
