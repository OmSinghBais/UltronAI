document.addEventListener("DOMContentLoaded", () => {
    const cmdInput = document.getElementById("cmd-input");
    const sendBtn = document.getElementById("send-btn");
    const micBtn = document.getElementById("mic-btn");
    const voiceOrb = document.getElementById("voice-orb");
    const orbStatus = document.getElementById("orb-status");
    const responseText = document.getElementById("response-text");
    const responseTag = document.getElementById("response-tag");
    const metricRoute = document.getElementById("metric-route");
    const metricLatency = document.getElementById("metric-latency");
    const auditLogBox = document.getElementById("audit-log-box");
    const auditCount = document.getElementById("audit-count");
    const controlIndicator = document.getElementById("control-indicator");
    const phoneStatusBadge = document.getElementById("phone-status-badge");

    // Modal elements
    const confirmModal = document.getElementById("confirm-modal");
    const modalPromptText = document.getElementById("modal-prompt-text");
    const btnCancel = document.getElementById("btn-cancel");
    const btnConfirm = document.getElementById("btn-confirm");

    let auditCounter = 0;
    let isListening = false;
    let pendingConfirmResolve = null;

    const voiceSelect = document.getElementById("voice-select");

    // Phonetic & Mishearing Correction Map
    function cleanSpeechTranscript(raw) {
        let text = raw.trim();
        
        // Strip wake word prefixes
        text = text.replace(/^(hey|play|pay|hi|ok|hello|open)?\s*(atlas|ultron)\b\s*/i, "").trim();

        // Common phonetic corrections
        const phoneticFixes = [
            [/\bsea screen\b/gi, "see screen"],
            [/\bc screen\b/gi, "see screen"],
            [/\bshe screen\b/gi, "see screen"],
            [/\bnote pad\b/gi, "notepad"],
            [/\bnote-pad\b/gi, "notepad"],
            [/\bchrom\b/gi, "chrome"],
            [/\bchrome browser\b/gi, "chrome"],
            [/\bsetting\b/gi, "settings"],
            [/\bscreen shot\b/gi, "screenshot"],
        ];

        for (const [pattern, replacement] of phoneticFixes) {
            text = text.replace(pattern, replacement);
        }

        return text.trim();
    }

    // Natural Voice Picker (populates #voice-select dropdown)
    let selectedVoice = null;
    function loadVoices() {
        if (!("speechSynthesis" in window)) return;
        const voices = window.speechSynthesis.getVoices();
        if (!voices.length) return;

        if (voiceSelect) {
            voiceSelect.innerHTML = "";
            voices.forEach((v, idx) => {
                const opt = document.createElement("option");
                opt.value = idx;
                opt.textContent = `${v.name} (${v.lang})`;
                voiceSelect.appendChild(opt);
            });
        }

        // Preferred voice priority list
        const priorities = [
            "Google US English",
            "Microsoft Jenny Online (Natural)",
            "Microsoft Guy Online (Natural)",
            "Google UK English Female",
            "Microsoft Zira",
            "Samantha",
            "Alex"
        ];

        for (const pref of priorities) {
            const foundIdx = voices.findIndex(v => v.name.includes(pref) || v.name.toLowerCase().includes(pref.toLowerCase()));
            if (foundIdx !== -1) {
                selectedVoice = voices[foundIdx];
                if (voiceSelect) voiceSelect.value = foundIdx;
                break;
            }
        }
        if (!selectedVoice) {
            selectedVoice = voices.find(v => v.lang.startsWith("en")) || voices[0];
        }
    }

    if ("speechSynthesis" in window) {
        window.speechSynthesis.onvoiceschanged = loadVoices;
        loadVoices();
    }

    if (voiceSelect) {
        voiceSelect.addEventListener("change", (e) => {
            const voices = window.speechSynthesis.getVoices();
            selectedVoice = voices[e.target.value] || selectedVoice;
        });
    }

    // Execute Command
    async function executeCommand(cmd, confirmChoice = null) {
        if (!cmd || !cmd.trim()) return;

        // Instant visual feedback: thinking spinner animation
        orbStatus.textContent = "⚡ Thinking & Executing...";
        voiceOrb.className = "voice-orb thinking";

        // Show active control indicator if control command
        const isControlCmd = ["open", "type", "click", "screenshot", "tap", "scroll", "read phone", "delete"].some(k => cmd.toLowerCase().includes(k));
        if (isControlCmd) {
            controlIndicator.classList.remove("hidden");
        }

        const startTime = performance.now();

        try {
            const payload = { command: cmd };
            if (confirmChoice !== null) {
                payload.confirmed = confirmChoice;
            }

            const res = await fetch("/api/execute", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            const latency = Math.round(performance.now() - startTime);

            // Handle Sensitive Action Gating Prompt
            if (data.status === "requires_confirmation") {
                modalPromptText.textContent = data.prompt || `Action '${cmd}' is sensitive. Confirm execution?`;
                confirmModal.classList.remove("hidden");

                const choice = await new Promise(resolve => {
                    pendingConfirmResolve = resolve;
                });

                confirmModal.classList.add("hidden");
                return executeCommand(cmd, choice);
            }

            // Update UI with response
            metricLatency.textContent = `${latency} ms`;
            metricRoute.textContent = (data.route || "CORE-ENGINE").toUpperCase();

            let textToSpeak = "";
            if (data.status === "ok") {
                responseTag.textContent = "SUCCESS";
                responseTag.style.background = "rgba(0, 230, 118, 0.15)";
                responseTag.style.color = "#00e676";
                textToSpeak = data.response || data.action || "Action executed successfully.";
                responseText.textContent = textToSpeak;
            } else if (data.status === "cancelled") {
                responseTag.textContent = "CANCELLED";
                responseTag.style.background = "rgba(255, 82, 82, 0.15)";
                responseTag.style.color = "#ff5252";
                textToSpeak = "Action cancelled by security gate.";
                responseText.textContent = textToSpeak;
            } else {
                responseTag.textContent = "ERROR";
                responseTag.style.background = "rgba(255, 82, 82, 0.15)";
                responseTag.style.color = "#ff5252";
                textToSpeak = data.error || data.reason || "Execution failed.";
                responseText.textContent = textToSpeak;
            }

            // Speak response out loud & trigger continuous auto-voice loop
            speakResponseAndListenNext(textToSpeak);

            // Append Audit Entry
            appendAuditLog(cmd, data.intent_type || "action", data.route || "core", data.status === "cancelled", data.response || JSON.stringify(data));

        } catch (err) {
            responseText.textContent = `Error connecting to ATLAS engine: ${err.message}`;
            voiceOrb.className = "voice-orb";
            orbStatus.textContent = 'Listening paused. Click Mic to resume.';
        } finally {
            setTimeout(() => controlIndicator.classList.add("hidden"), 1500);
        }
    }

    // Speech Synthesis (TTS) & Continuous Voice Loop
    let continuousVoice = true; // Continuous listening by default
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition = null;

    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = false;

        recognition.onspeechstart = () => {
            // Speech Interruption / Barge-in: Cut off Ultron immediately when user starts speaking!
            if ("speechSynthesis" in window && window.speechSynthesis.speaking) {
                window.speechSynthesis.cancel();
                voiceOrb.className = "voice-orb listening";
                orbStatus.textContent = "🎙️ Listening to you...";
            }
        };

        recognition.onresult = (event) => {
            // Cut off any ongoing speech synthesis immediately
            if ("speechSynthesis" in window && window.speechSynthesis.speaking) {
                window.speechSynthesis.cancel();
            }

            const raw = event.results[event.results.length - 1][0].transcript;
            const cleaned = cleanSpeechTranscript(raw);

            if (!cleaned || cleaned.toLowerCase() === "atlas" || cleaned.toLowerCase() === "hey atlas" || cleaned.toLowerCase() === "play atlas") {
                cmdInput.value = raw;
                speakResponseAndListenNext("Yes, I am listening. What would you like me to do?");
            } else {
                cmdInput.value = cleaned;
                executeCommand(cleaned);
            }
        };

        recognition.onend = () => {
            isListening = false;
            if (continuousVoice && !window.speechSynthesis.speaking) {
                try { recognition.start(); } catch(e) {}
            } else if (!window.speechSynthesis.speaking) {
                voiceOrb.className = "voice-orb";
                orbStatus.textContent = 'Listening for "Hey Atlas" or click Mic...';
            }
        };

        recognition.onerror = (e) => {
            if (continuousVoice && e.error !== "aborted") {
                setTimeout(() => { try { recognition.start(); } catch(err) {} }, 1000);
            }
        };
    }

    function speakResponseAndListenNext(text) {
        if (!("speechSynthesis" in window) || !text) return;

        window.speechSynthesis.cancel(); // Stop prior speech
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;

        if (selectedVoice) {
            utterance.voice = selectedVoice;
        }

        voiceOrb.className = "voice-orb speaking";
        orbStatus.textContent = `🔊 Ultron Speaking: "${text.substring(0, 35)}..."`;

        utterance.onend = () => {
            voiceOrb.className = "voice-orb listening";

            if (continuousVoice && recognition) {
                orbStatus.textContent = "🎙️ Listening for your voice command...";
                isListening = true;
                try { recognition.start(); } catch(e) {}
            } else {
                orbStatus.textContent = 'Click Mic or say command...';
            }
        };

        window.speechSynthesis.speak(utterance);
    }

    // Append Log to Audit Box
    function appendAuditLog(cmd, intent, route, blocked, result) {
        auditCounter++;
        auditCount.textContent = `${auditCounter} Entries Logged`;

        const line = document.createElement("div");
        line.className = "log-line";
        const ts = new Date().toLocaleTimeString();

        line.innerHTML = `[<span class="ts">${ts}</span>] [<span class="intent">${intent.toUpperCase()}</span>] [<span class="route">${route.toUpperCase()}</span>] ${blocked ? '<span class="blocked">[BLOCKED]</span>' : ''} "${cmd}" -> ${typeof result === 'string' ? result.substring(0, 60) : JSON.stringify(result)}`;

        auditLogBox.appendChild(line);
        auditLogBox.scrollTop = auditLogBox.scrollHeight;
    }

    // Modal Action Listeners
    btnCancel.addEventListener("click", () => {
        if (pendingConfirmResolve) pendingConfirmResolve(false);
    });

    btnConfirm.addEventListener("click", () => {
        if (pendingConfirmResolve) pendingConfirmResolve(true);
    });

    // Event Listeners
    sendBtn.addEventListener("click", () => {
        const text = cmdInput.value;
        cmdInput.value = "";
        executeCommand(text);
    });

    cmdInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            const text = cmdInput.value;
            cmdInput.value = "";
            executeCommand(text);
        }
    });

    // Quick Command Chips
    document.querySelectorAll(".chip").forEach(chip => {
        chip.addEventListener("click", () => {
            const cmd = chip.getAttribute("data-cmd");
            executeCommand(cmd);
        });
    });

    function startMic() {
        if (recognition && !isListening) {
            try {
                recognition.start();
                isListening = true;
                continuousVoice = true;
                if (micBtn) micBtn.style.background = "linear-gradient(135deg, #00e676, #00b0ff)";
                orbStatus.textContent = "Continuous Voice Active. Listening...";
                voiceOrb.classList.add("listening");
            } catch(e) {}
        }
    }

    // Auto-start listening on first click anywhere
    document.body.addEventListener("click", () => {
        startMic();
    }, { once: true });

    // Mic Button Listener
    if (micBtn && recognition) {
        micBtn.style.background = "linear-gradient(135deg, #00e676, #00b0ff)";
        micBtn.addEventListener("click", () => {
            continuousVoice = !continuousVoice;
            if (continuousVoice) {
                startMic();
            } else {
                micBtn.style.background = "";
                continuousVoice = false;
                isListening = false;
                try { recognition.stop(); } catch(e) {}
                window.speechSynthesis.cancel();
                voiceOrb.classList.remove("listening");
                orbStatus.textContent = 'Listening paused. Click Mic to resume.';
            }
        });
    } else if (micBtn) {
        micBtn.title = "Web Speech API not supported in this browser. Use text bar.";
    }
});
