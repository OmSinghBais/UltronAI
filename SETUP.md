# ATLAS — WINDOWS SETUP GUIDE (Phase 1)

This guide provides step-by-step instructions to set up the environment for **ATLAS** on Windows 10/11.

---

## 1. Prerequisites Checklist

Before running ATLAS, ensure you have the following installed on Windows:

1. **Python 3.11+**:
   - Download from [python.org](https://www.python.org/downloads/) or via Windows Package Manager (`winget`):
     ```powershell
     winget install Python.Python.3.11
     ```
   - Make sure **"Add Python to PATH"** is checked during installation.

2. **Google Gemini API Key**:
   - Obtain a free API key from [Google AI Studio](https://aistudio.google.com/).
   - Copy your key into a `.env` file created from `.env.example`:
     ```powershell
     Copy-Item .env.example .env
     ```

3. **Ollama (for local offline LLM fallback)**:
   - Download installer for Windows from [ollama.com](https://ollama.com/download/windows).
   - Once installed, pull the recommended small model in PowerShell:
     ```powershell
     ollama pull qwen2.5:3b
     ```

4. **Android SDK / ADB & scrcpy (for Phase 6 phone companion setup)**:
   - Install via `winget` or Chocolatey:
     ```powershell
     winget install Google.PlatformTools
     winget install Genymobile.scrcpy
     ```
   - Ensure `adb` and `scrcpy` are on your PowerShell PATH.

5. **Audio Input/Output**:
   - Working microphone and speakers connected and set as default recording/playback devices in Windows Settings.

---

## 2. Setting Up Python Virtual Environment

In PowerShell, inside the project directory:

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Install required dependencies
pip install -r requirements.txt
```

---

## 3. Environment Variables Configuration

Copy `.env.example` to `.env` and fill in your keys:

```powershell
Copy-Item .env.example .env
```

Edit `.env`:
- Set `GEMINI_API_KEY=AIzaSy...` with your actual Gemini API key.
- Adjust `OLLAMA_MODEL` if you pulled a different model (e.g. `phi3:mini`).

---

## 4. Verification

Run the Phase 1 test suite and verification demo script:

```powershell
# Run automated tests
pytest tests/core/test_config_and_audit.py

# Run Phase 1 live demo script
python demo_phase1.py
```
