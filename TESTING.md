# Testing Log

## Phase 1
- **Automated Tests**:
  - `tests/core/test_config_and_audit.py`: 2 passed in 0.40s.
- **Manual Demo Checklist**:
  - [x] Execute `demo_phase1.py` successfully.
  - [x] Confirm Pydantic settings load correctly.
  - [x] Confirm `storage/audit.jsonl` is created with valid JSON entry.
  - [x] Confirm Gemini API key check logic.

## Phase 2
- **Automated Tests**:
  - `tests/core/test_voice_loop.py`: 4 passed (`test_wake_word_detector_frame`, `test_wake_word_async_listen`, `test_stt_transcribe`, `test_tts_generation`).
- **Manual Demo Checklist**:
  - [x] Execute `demo_phase2.py` voice pipeline echo test.
  - [x] Confirm WakeWordDetector processes audio stream.
  - [x] Confirm SpeechToText transcribes audio to text + language tuple.
  - [x] Confirm TextToSpeech synthesizes WAV file.
  - [x] Confirm AuditLogger logs voice echo action.
