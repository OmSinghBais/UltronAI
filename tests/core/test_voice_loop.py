import pytest
import tempfile
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock, patch
from core.wake_word import WakeWordDetector
from core.stt import SpeechToText
from core.tts import TextToSpeech


def test_wake_word_detector_frame():
    """Verify WakeWordDetector processes 16kHz PCM audio chunk without error."""
    detector = WakeWordDetector(threshold=0.5)
    # Generate 100ms of synthetic 16kHz int16 PCM audio
    sample_rate = 16000
    chunk_samples = int(sample_rate * 0.1)
    synthetic_pcm = (np.random.randn(chunk_samples) * 1000).astype(np.int16).tobytes()

    result = detector.process_frame(synthetic_pcm)
    assert isinstance(result, bool)


@pytest.mark.asyncio
async def test_wake_word_async_listen():
    """Verify async listen generator processes stream and terminates cleanly."""
    detector = WakeWordDetector(threshold=0.5)

    async def mock_audio_stream():
        for _ in range(5):
            yield (np.zeros(1600, dtype=np.int16)).tobytes()

    result = await detector.listen(mock_audio_stream())
    assert isinstance(result, bool)
    assert result is False


def test_stt_transcribe_mocked():
    """Verify SpeechToText.transcribe returns (text, lang) without downloading a model."""
    # Mock WhisperModel so _load_model() never hits HuggingFace
    mock_model = MagicMock()
    mock_segment = MagicMock()
    mock_segment.text = "hello atlas"
    mock_info = MagicMock()
    mock_info.language = "en"
    mock_model.transcribe.return_value = ([mock_segment], mock_info)

    with patch("core.stt.WhisperModel", return_value=mock_model):
        stt = SpeechToText(model_size="tiny")
        # Force the import path so the patch is applied
        from faster_whisper import WhisperModel  # noqa: F401
        stt.model = mock_model

        text, lang = stt.transcribe("/fake/audio.wav")

    assert isinstance(text, str)
    assert isinstance(lang, str)
    assert text == "hello atlas"
    assert lang == "en"


def test_stt_transcribe_fallback_when_no_model():
    """Verify SpeechToText returns mock tuple when model fails to load."""
    stt = SpeechToText(model_size="tiny")
    # _load_model will fail (no real model), returning None → fallback
    with patch("core.stt.WhisperModel", side_effect=Exception("no model")):
        stt._load_model()
        assert stt.model is None
        text, lang = stt.transcribe("/nonexistent/audio.wav")
        assert text == "mock transcription"
        assert lang == "en"


def test_tts_generation():
    """Verify TextToSpeech synthesizes text and writes a WAV file using numpy fallback."""
    tts = TextToSpeech()  # No voice_model_path → always uses numpy fallback

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_tts.wav"
        result_path = tts.speak("Hello Atlas voice test", output_wav_path=output_path)

        assert result_path is not None
        assert result_path.exists()
        assert result_path.stat().st_size > 0
