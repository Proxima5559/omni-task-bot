import logging
from functools import lru_cache
from typing import Protocol

from google import genai
from google.genai import types, errors

from app.config import settings
from app.utils.errors import PermanentError, TransientError

log = logging.getLogger(__name__)


class Transcriber(Protocol):
    def transcribe(self, audio: bytes, filename: str) -> str: ...


class GeminiTranscriber:
    def __init__(self) -> None:
        if not settings.gemini_api_key:
            log.error("Initialization failed: GEMINI_API_KEY is missing from configuration")
            raise PermanentError("GEMINI_API_KEY is not configured")
        
        self.client = genai.Client(api_key=settings.gemini_api_key)
        log.info("GeminiTranscriber client successfully initialized")

    def transcribe(self, audio: bytes, filename: str) -> str:
        log.info("Starting transcription for file: %s (%d bytes)", filename, len(audio))
        
        try:
            ext = filename.split(".")[-1].lower()
            mime_type = f"audio/{ext}" if ext in ["mp3", "wav", "ogg", "m4a", "webm"] else "audio/mp3"
            log.debug("Determined MIME type: %s", mime_type)

            result = self.client.models.generate_content(
                model=settings.whisper_model,  
                contents=[
                    types.Part.from_bytes(
                        data=audio,
                        mime_type=mime_type,
                    ),
                    "Transcribe the audio file to text. Return only the transcribed text, without any additional commentary or formatting."
                ]
            )
        except errors.APIError as exc:
            log.warning("Gemini API error occurred. Code: %s, Message: %s", exc.code, exc)
            if exc.code in [500, 502, 503, 504]:
                raise TransientError(f"Gemini temporarily unavailable: {exc}") from exc
            raise PermanentError(f"Gemini rejected the request ({exc.code}): {exc}") from exc
        except Exception as exc:
            log.exception("Unexpected system exception during Gemini API call")
            raise PermanentError(f"Unexpected system error: {exc}") from exc

        text = (result.text or "").strip()
        if not text:
            log.error("Transcription output is empty for file: %s", filename)
            raise PermanentError("No speech detected in the voice message")
            
        log.info("Successfully transcribed %s. Character count: %d", filename, len(text))
        return text


class FakeTranscriber:

    def transcribe(self, audio: bytes, filename: str) -> str:
        return f"[fake transcription of {len(audio)} bytes]"


@lru_cache
def get_transcriber() -> Transcriber:
    if settings.transcriber == "fake":
        log.warning("Using FakeTranscriber")
        return FakeTranscriber()
    return GeminiTranscriber()