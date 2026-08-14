import pyttsx3
import tempfile
import os

class TextToSpeech:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 175)

    def speak(self, text):
        if not text:
            return None

        path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                path = tmp.name

            self.engine.save_to_file(text, path)
            self.engine.runAndWait()

            with open(path, "rb") as f:
                return f.read()
        finally:
            if path and os.path.exists(path):
                os.remove(path)