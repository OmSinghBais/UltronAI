from pathlib import Path
from typing import Tuple, Union, Optional

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None  # type: ignore


class SpeechToText:
    """
    Local multi-lingual Speech-to-Text using faster-whisper.
    Supports English and Hindi code-switched voice inputs.
    """
    def __init__(self, model_size: str = "small", device: str = "cpu", compute_type: str = "int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None

    def _load_model(self) -> None:
        """Lazy initialization of faster-whisper model."""
        if self.model is None:
            try:
                if WhisperModel is None:
                    raise ImportError("faster_whisper not available")
                self.model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type
                )
            except Exception:
                self.model = None

    def transcribe(self, audio_path: Union[str, Path]) -> Tuple[str, str]:
        """
        Transcribe an audio file into text.
        Returns tuple of (transcribed_text, detected_language).
        """
        self._load_model()
        if self.model is None:
            return ("mock transcription", "en")

        try:
            segments, info = self.model.transcribe(str(audio_path), language=None, task="transcribe")
            text = " ".join(seg.text for seg in segments).strip()
            detected_language = getattr(info, "language", "en")
            return text, detected_language
        except Exception as e:
            return (f"Error transcribing audio: {e}", "en")
