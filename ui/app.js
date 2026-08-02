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

    // Execute Command
    async function executeCommand(cmd, confirmChoice = null) {
        if (!cmd || !cmd.trim()) return;

        orbStatus.textContent = "Processing command...";
        voiceOrb.classList.add("listening");

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
        } finally {
            voiceOrb.classList.remove("listening");
            setTimeout(() => controlIndicator.classList.add("hidden"), 1500);
        }
    }

    // Speech Synthesis (TTS) & Continuous Voice Loop
    let continuousVoice = false;
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition = null;

    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            cmdInput.value = transcript;
            executeCommand(transcript);
        };

        recognition.onend = () => {
            isListening = false;
            if (!window.speechSynthesis.speaking) {
                voiceOrb.classList.remove("listening");
                orbStatus.textContent = 'Listening for "Hey Atlas" or click Mic...';
            }
        };
    }

    function speakResponseAndListenNext(text) {
        if (!("speechSynthesis" in window) || !text) return;

        window.speechSynthesis.cancel(); // Stop prior speech
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;

        voiceOrb.classList.add("listening");
        orbStatus.textContent = "Ultron Speaking Response...";

        utterance.onend = () => {
            voiceOrb.classList.remove("listening");

            // Hands-free continuous loop: Ask next command and start listening automatically if continuous mode active
            if (continuousVoice && recognition) {
                orbStatus.textContent = "Asking: What would you like to do next?...";
                const followUp = new SpeechSynthesisUtterance("What would you like me to do next?");
                followUp.onend = () => {
                    orbStatus.textContent = "Listening for your voice command...";
                    voiceOrb.classList.add("listening");
                    isListening = true;
                    try { recognition.start(); } catch(e) {}
                };
                window.speechSynthesis.speak(followUp);
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

    // Mic Button Listener
    if (micBtn && recognition) {
        micBtn.addEventListener("click", () => {
            continuousVoice = !continuousVoice;
            if (continuousVoice) {
                micBtn.style.background = "linear-gradient(135deg, #00e676, #00b0ff)";
                orbStatus.textContent = "Continuous Voice Mode Active. Listening...";
                voiceOrb.classList.add("listening");
                isListening = true;
                try { recognition.start(); } catch(e) {}
            } else {
                micBtn.style.background = "";
                continuousVoice = false;
                isListening = false;
                try { recognition.stop(); } catch(e) {}
                window.speechSynthesis.cancel();
                voiceOrb.classList.remove("listening");
                orbStatus.textContent = 'Listening for "Hey Atlas" or click Mic...';
            }
        });
    } else if (micBtn) {
        micBtn.title = "Web Speech API not supported in this browser. Use text bar.";
    }
});
