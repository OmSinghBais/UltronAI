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

            if (data.status === "ok") {
                responseTag.textContent = "SUCCESS";
                responseTag.style.background = "rgba(0, 230, 118, 0.15)";
                responseTag.style.color = "#00e676";
                responseText.textContent = data.response || data.action || "Action executed successfully.";
            } else if (data.status === "cancelled") {
                responseTag.textContent = "CANCELLED";
                responseTag.style.background = "rgba(255, 82, 82, 0.15)";
                responseTag.style.color = "#ff5252";
                responseText.textContent = "Action cancelled by security gate.";
            } else {
                responseTag.textContent = "ERROR";
                responseTag.style.background = "rgba(255, 82, 82, 0.15)";
                responseTag.style.color = "#ff5252";
                responseText.textContent = data.error || data.reason || "Execution failed.";
            }

            // Append Audit Entry
            appendAuditLog(cmd, data.intent_type || "action", data.route || "core", data.status === "cancelled", data.response || JSON.stringify(data));

        } catch (err) {
            responseText.textContent = `Error connecting to ATLAS engine: ${err.message}`;
        } finally {
            voiceOrb.classList.remove("listening");
            orbStatus.textContent = 'Listening for "Hey Atlas" or click Mic...';
            setTimeout(() => controlIndicator.classList.add("hidden"), 1500);
        }
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

    // Web Speech Recognition for Mic Button
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;

        micBtn.addEventListener("click", () => {
            if (isListening) {
                recognition.stop();
            } else {
                recognition.start();
                orbStatus.textContent = "Listening to your voice...";
                voiceOrb.classList.add("listening");
                isListening = true;
            }
        });

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            cmdInput.value = transcript;
            executeCommand(transcript);
        };

        recognition.onend = () => {
            isListening = false;
            voiceOrb.classList.remove("listening");
        };
    } else {
        micBtn.title = "Web Speech API not supported in this browser. Use text bar.";
    }
});
