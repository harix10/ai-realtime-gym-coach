"""Text-to-speech providers for spoken coaching feedback."""

from io import BytesIO
import os

from gtts import gTTS


class TextToSpeech:
    """Generate MP3 audio with OpenAI TTS and fall back to Google TTS.

    OpenAI is optional so the coach still works with the project's existing
    GROQ_API_KEY-only setup.  gTTS does not expose a model setting; it is a
    fallback provider rather than an invalid or missing model configuration.
    """

    DEFAULT_MODEL = "gpt-4o-mini-tts"
    DEFAULT_VOICE = "alloy"

    def __init__(self, api_key=None, model=None, voice=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_TTS_MODEL", self.DEFAULT_MODEL)
        self.voice = voice or os.getenv("OPENAI_TTS_VOICE", self.DEFAULT_VOICE)
        self.client = self._create_openai_client()
        self.last_error = None

    def _create_openai_client(self):
        if not self.api_key:
            return None

        try:
            from openai import OpenAI
            return OpenAI(api_key=self.api_key)
        except ImportError:
            # Keep the app usable when optional OpenAI support is not installed.
            return None

    def _openai_speak(self, text):
        response = self.client.audio.speech.create(
            model=self.model,
            voice=self.voice,
            input=text,
            response_format="mp3",
        )
        return response.content

    @staticmethod
    def _gtts_speak(text, lang):
        buffer = BytesIO()
        gTTS(text=text, lang=lang).write_to_fp(buffer)
        return buffer.getvalue()

    def speak(self, text, lang="en"):
        cleaned = (text or "").strip()
        if not cleaned:
            return None

        if self.client:
            try:
                return self._openai_speak(cleaned)
            except Exception as error:
                # A bad key, unavailable model, or transient API error should
                # not stop the camera/coaching loop.
                self.last_error = error

        try:
            return self._gtts_speak(cleaned, lang)
        except Exception as error:
            self.last_error = error
            return None
