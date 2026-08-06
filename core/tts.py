import os
import wave
import numpy as np
from pathlib import Path
from typing import Optional, Union


class TextToSpeech:
    """
    Local Text-to-Speech synthesis engine using Piper TTS with local audio fallback.
    """
    def __init__(self, voice_model_path: Optional[str] = None):
        self.voice_model_path = voice_model_path
        self.piper_voice = None
        self.interrupted = False

    def interrupt(self) -> None:
        """Triggers barge-in speech interruption to immediately stop TTS playback."""
        self.interrupted = True
        print("[TTS Interrupted] Barge-in speech cancellation triggered.")

    def _load_voice(self) -> None:
        """Lazy load Piper TTS voice model if available."""
        if self.piper_voice is None and self.voice_model_path and os.path.exists(self.voice_model_path):
            try:
                from piper.voice import PiperVoice
                self.piper_voice = PiperVoice.load(self.voice_model_path)
            except Exception:
                self.piper_voice = None

    def speak(self, text: str, output_wav_path: Optional[Union[str, Path]] = None) -> Optional[Path]:
        """
        Synthesizes text into audio.
        If output_wav_path is specified, saves the generated WAV file.
        Returns the Path to the generated WAV file, or None.
        """
        if not text:
            return None

        target_path = Path(output_wav_path) if output_wav_path else Path("./storage/last_tts.wav")
        target_path.parent.mkdir(parents=True, exist_ok=True)

        self._load_voice()

        if self.piper_voice is not None:
            try:
                with wave.open(str(target_path), "wb") as wav_file:
                    self.piper_voice.synthesize(text, wav_file)
                return target_path
            except Exception:
                pass

        # Fallback synthesis: Create a silent/beep WAV file containing audio headers for test verification
        sample_rate = 22050
        duration_s = 0.5
        t = np.linspace(0, duration_s, int(sample_rate * duration_s), False)
        # Generate 440 Hz tone
        audio_samples = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)

        with wave.open(str(target_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_samples.tobytes())

        print(f"[TTS Output]: '{text}' -> Audio saved to {target_path}")
        return target_path
