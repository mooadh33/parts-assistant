"""Step 12: speech-to-text. OpenAI Whisper API if key present, else local faster-whisper if installed, else mock."""
import io
import os


def transcribe(audio_bytes, filename="audio.wav", language="de"):
    if os.getenv("OPENAI_API_KEY"):
        from openai import OpenAI
        f = io.BytesIO(audio_bytes); f.name = filename
        return OpenAI().audio.transcriptions.create(model="whisper-1", file=f, language=language).text
    try:
        from faster_whisper import WhisperModel  # pip install faster-whisper
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav") as t:
            t.write(audio_bytes); t.flush()
            segs, _ = WhisperModel("small", compute_type="int8").transcribe(t.name, language=language)
            return " ".join(s.text for s in segs).strip()
    except ImportError:
        return "[MOCK-Transkription] Welcher Stoßdämpfer passt zum Golf VII?"
