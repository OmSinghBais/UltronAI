import asyncio
from typing import AsyncGenerator, Optional
import numpy as np


class WakeWordDetector:
    """
    Offline wake-word detection engine using openwakeword.
    Processes continuous 16kHz mono int16 PCM audio chunks.
    """
    def __init__(self, model_path: Optional[str] = None, threshold: float = 0.5):
        self.model_path = model_path
        self.threshold = threshold
        self.model = None

    def load_model(self) -> None:
        """Lazy load openwakeword model."""
        if self.model is None:
            try:
                from openwakeword.model import Model
                if self.model_path:
                    self.model = Model(wakeword_models=[self.model_path])
                else:
                    self.model = Model()
            except Exception:
                # Model loading fallback for environments without default weights/onnx file
                self.model = None

    def process_frame(self, frame: bytes) -> bool:
        """
        Process a single int16 PCM audio frame chunk (16kHz mono).
        Returns True if wake word score exceeds threshold.
        """
        if self.model is None:
            self.load_model()

        if self.model is None:
            return False

        audio_data = np.frombuffer(frame, dtype=np.int16)
        scores = self.model.predict(audio_data)
        for wakeword, score in scores.items():
            if score > self.threshold:
                return True
        return False

    async def listen(self, audio_stream: AsyncGenerator[bytes, None]) -> bool:
        """
        Consumes an async audio frame generator.
        Yields control back the moment the wake word is detected.
        """
        async for frame in audio_stream:
            if self.process_frame(frame):
                return True
        return False
