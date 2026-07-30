import pytest
import tempfile
import numpy as np
from pathlib import Path
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


def test_stt_transcribe():
    """Verify SpeechToText transcribe returns tuple of (text, language)."""
    stt = SpeechToText(model_size="small")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        temp_wav_path = f.name

    # Create dummy WAV for testing
    tts = TextToSpeech()
    tts.speak("Testing speech recognition", output_wav_path=temp_wav_path)

    text, lang = stt.transcribe(temp_wav_path)
    assert isinstance(text, str)
    assert isinstance(lang, str)

    # Cleanup
    if Path(temp_wav_path).exists():
        Path(temp_wav_path).unlink()


def test_tts_generation():
    """Verify TextToSpeech synthesizes text and writes a WAV file."""
    tts = TextToSpeech()

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_tts.wav"
        result_path = tts.speak("Hello Atlas voice test", output_wav_path=output_path)

        assert result_path is not None
        assert result_path.exists()
        assert result_path.stat().st_size > 0
