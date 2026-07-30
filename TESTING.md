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

## Phase 3
- **Automated Tests**:
  - `tests/core/test_router.py`: 3 passed (`test_falls_back_to_ollama_when_offline`, `test_routes_to_gemini_when_online`, `test_falls_back_to_ollama_on_gemini_exception`).
- **Manual Demo Checklist**:
  - [x] Execute `demo_phase3.py` dual reasoning router script.
  - [x] Verify online connectivity check (`is_online()`).
  - [x] Verify Gemini API routing when online and configured.
  - [x] Verify seamless fallback to local Ollama (`qwen2.5:3b`) when offline or on Gemini failure.

## Phase 4
- **Automated Tests**:
  - `tests/core/test_orchestrator.py`: 4 passed (`test_intent_classification`, `test_query_command_execution`, `test_sensitive_action_confirmed`, `test_sensitive_action_cancelled`).
- **Manual Demo Checklist**:
  - [x] Execute `demo_phase4.py` orchestrator integration script.
  - [x] Verify intent classification (queries vs desktop actions vs sensitive actions).
  - [x] Verify autonomous execution for query & non-sensitive desktop action.
  - [x] Verify sensitive action cancellation when confirm_fn returns False.
  - [x] Verify sensitive action execution when confirm_fn returns True.
