// AI-Powered Outbound Voice Calling System - Frontend Application Logic

document.addEventListener("DOMContentLoaded", () => {
    // --- State Variables ---
    let activeCallSessionId = null;
    let callTimerInterval = null;
    let callSeconds = 0;
    let mediaRecorder = null;
    let audioChunks = [];
    let isRecording = false;
    let animationFrameId = null;

    // --- DOM Elements ---
    const tabButtons = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");

    const startCallBtn = document.getElementById("startCallBtn");
    const endCallBtn = document.getElementById("endCallBtn");
    const callStateBadge = document.getElementById("callStateBadge");
    const activeCallScreen = document.getElementById("activeCallScreen");
    const callTimer = document.getElementById("callTimer");
    const donorSelect = document.getElementById("donorSelect");
    const callLanguageSelect = document.getElementById("callLanguageSelect");
    const activeDonorDisplay = document.getElementById("activeDonorDisplay");
    const escalationAlertBanner = document.getElementById("escalationAlertBanner");

    const micBtn = document.getElementById("micBtn");
    const micRing = document.getElementById("micRing");
    const recordingStatus = document.getElementById("recordingStatus");
    const waveformCanvas = document.getElementById("waveformCanvas");
    const textQueryInput = document.getElementById("textQueryInput");
    const submitTextBtn = document.getElementById("submitTextBtn");

    const transcriptBox = document.getElementById("transcriptBox");
    const agentAudioPlayer = document.getElementById("agentAudioPlayer");
    const playingIntentBadge = document.getElementById("playingIntentBadge");
    const playingConfBadge = document.getElementById("playingConfBadge");
    const escalationBadgeCount = document.getElementById("escalationBadgeCount");

    // --- 1. Tab Navigation Handler ---
    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            tabButtons.forEach(b => b.classList.remove("active"));
            tabContents.forEach(c => c.classList.add("hidden"));

            btn.classList.add("active");
            const tabId = btn.getAttribute("data-tab");
            document.getElementById(tabId).classList.remove("hidden");

            if (tabId === "campaignTab") loadCampaignData();
            if (tabId === "handoffTab") loadEscalationsData();
            if (tabId === "analyticsTab") loadAnalyticsData();
        });
    });

    // --- 2. Quick Tamil Preset Chips ---
    document.querySelectorAll(".chip").forEach(chip => {
        chip.addEventListener("click", () => {
            const queryText = chip.getAttribute("data-text");
            textQueryInput.value = queryText;
            sendTextTurn(queryText);
        });
    });

    // --- 3. Outbound Call Session Manager ---
    startCallBtn.addEventListener("click", async () => {
        const phone = donorSelect.value;
        const lang = callLanguageSelect.value;
        const selectedOption = donorSelect.options[donorSelect.selectedIndex];
        const donorName = selectedOption.getAttribute("data-name");

        startCallBtn.disabled = true;
        callStateBadge.textContent = "DIALING...";
        callStateBadge.className = "call-badge dialing";

        try {
            const formData = new FormData();
            formData.append("phone", phone);
            formData.append("campaign_id", "1");
            formData.append("language", lang);

            const res = await fetch("/api/v1/outbound/start", { method: "POST", body: formData });
            const data = await res.json();

            activeCallSessionId = data.session_id;
            callStateBadge.textContent = "CONNECTED";
            callStateBadge.className = "call-badge connected";

            activeCallScreen.classList.remove("hidden");
            startCallBtn.classList.add("hidden");
            endCallBtn.classList.remove("hidden");
            activeDonorDisplay.textContent = `Donor: ${donorName}`;

            startCallTimer();
            clearTranscript();
            
            // Add Greeting to Transcript
            addTranscriptTurn({
                role: "agent",
                intent: "GREETING",
                confidence: 1.0,
                text: data.greeting_text,
                audio_url: data.greeting_audio_url
            });

            playAudio(data.greeting_audio_url, "GREETING", 1.0);

        } catch (err) {
            console.error("Error starting call:", err);
            alert("Failed to connect outbound call.");
        } finally {
            startCallBtn.disabled = false;
        }
    });

    endCallBtn.addEventListener("click", () => {
        endCallSession();
    });

    function startCallTimer() {
        callSeconds = 0;
        clearInterval(callTimerInterval);
        callTimerInterval = setInterval(() => {
            callSeconds++;
            const mins = String(Math.floor(callSeconds / 60)).padStart(2, '0');
            const secs = String(callSeconds % 60).padStart(2, '0');
            callTimer.textContent = `${mins}:${secs}`;
        }, 1000);
    }

    function endCallSession() {
        clearInterval(callTimerInterval);
        activeCallSessionId = null;
        callStateBadge.textContent = "IDLE";
        callStateBadge.className = "call-badge idle";
        activeCallScreen.classList.add("hidden");
        startCallBtn.classList.remove("hidden");
        endCallBtn.classList.add("hidden");
        escalationAlertBanner.classList.add("hidden");
    }

    // --- 4. Turn Processing (Text & Voice) ---
    submitTextBtn.addEventListener("click", () => {
        const text = textQueryInput.value.trim();
        if (text) sendTextTurn(text);
    });

    textQueryInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            const text = textQueryInput.value.trim();
            if (text) sendTextTurn(text);
        }
    });

    async function sendTextTurn(text) {
        if (!activeCallSessionId) {
            alert("Please initiate an outbound call first!");
            return;
        }

        addTranscriptTurn({ role: "customer", text: text });
        textQueryInput.value = "";

        try {
            const res = await fetch(`/api/v1/outbound/turn-text?session_id=${activeCallSessionId}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: text, force_language: callLanguageSelect.value })
            });

            const data = await res.json();
            handleTurnResponse(data);
        } catch (err) {
            console.error("Error submitting turn text:", err);
        }
    }

    // --- 5. Push-to-Talk Microphone Manager (Web Speech API + MediaRecorder) ---
    let speechRecognition = null;
    let recognizedText = "";

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    micBtn.addEventListener("click", async () => {
        if (!activeCallSessionId) {
            alert("Please initiate an outbound call first!");
            return;
        }

        if (!isRecording) {
            startRecording();
        } else {
            stopRecording();
        }
    });

    async function startRecording() {
        recognizedText = "";
        const lang = callLanguageSelect.value === "ta" ? "ta-IN" : "en-IN";

        // Initialize Web Speech API if supported in browser
        if (SpeechRecognition) {
            speechRecognition = new SpeechRecognition();
            speechRecognition.continuous = false;
            speechRecognition.interimResults = true;
            speechRecognition.lang = lang;

            speechRecognition.onresult = (event) => {
                let interim = "";
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const transcript = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {
                        recognizedText += transcript;
                    } else {
                        interim += transcript;
                    }
                }
                const displayText = recognizedText || interim;
                if (displayText) {
                    textQueryInput.value = displayText;
                    recordingStatus.textContent = `Recognized: "${displayText}"`;
                }
            };

            speechRecognition.onspeechend = () => {
                recordingStatus.textContent = "Processing speech... auto-sending turn";
                setTimeout(() => { stopRecording(); }, 600);
            };

            speechRecognition.onerror = (err) => {
                console.log("Web Speech API note:", err.error);
                if (err.error === "no-speech") {
                    recordingStatus.textContent = "Listening... Speak in Tamil now";
                }
            };

            try {
                speechRecognition.start();
            } catch (e) {
                console.log("Speech recognition start note:", e);
            }
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            audioChunks = [];
            mediaRecorder = new MediaRecorder(stream);

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) audioChunks.push(event.data);
            };

            mediaRecorder.onstop = async () => {
                stream.getTracks().forEach(track => track.stop());
                
                if (recognizedText && recognizedText.trim().length > 0) {
                    sendTextTurn(recognizedText.trim());
                } else if (audioChunks.length > 0) {
                    const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
                    sendVoiceTurn(audioBlob);
                } else {
                    recordingStatus.textContent = "Tap microphone to respond in Tamil";
                }
            };

            mediaRecorder.start();
            isRecording = true;
            micBtn.classList.add("recording");
            recordingStatus.textContent = "Listening... Speak in Tamil now (Auto-sending when finished)";
            drawWaveform(stream);

        } catch (err) {
            console.error("Microphone access denied:", err);
            alert("Could not access microphone.");
        }
    }

    function stopRecording() {
        if (isRecording) {
            isRecording = false;
            micBtn.classList.remove("recording");
            recordingStatus.textContent = "Processing speech turn...";
            
            if (speechRecognition) {
                try { speechRecognition.stop(); } catch(e) {}
            }
            if (mediaRecorder && mediaRecorder.state !== "inactive") {
                mediaRecorder.stop();
            }
            if (animationFrameId) cancelAnimationFrame(animationFrameId);
        }
    }

    async function sendVoiceTurn(audioBlob) {
        try {
            const formData = new FormData();
            formData.append("file", audioBlob, "speech.wav");
            formData.append("session_id", activeCallSessionId);

            const res = await fetch("/api/v1/outbound/turn-voice", { method: "POST", body: formData });
            const data = await res.json();

            addTranscriptTurn({ role: "customer", text: data.transcription || "[Voice Audio Response]" });
            handleTurnResponse(data);

        } catch (err) {
            console.error("Error sending voice turn:", err);
            recordingStatus.textContent = "Error processing voice.";
        }
    }

    function drawWaveform(stream) {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const analyser = audioCtx.createAnalyser();
        const source = audioCtx.createMediaStreamSource(stream);
        source.connect(analyser);
        analyser.fftSize = 64;

        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        const ctx = waveformCanvas.getContext("2d");

        function draw() {
            if (!isRecording) return;
            animationFrameId = requestAnimationFrame(draw);
            analyser.getByteFrequencyData(dataArray);

            ctx.fillStyle = "rgba(0, 0, 0, 0.2)";
            ctx.fillRect(0, 0, waveformCanvas.width, waveformCanvas.height);

            const barWidth = (waveformCanvas.width / bufferLength) * 2;
            let x = 0;

            for (let i = 0; i < bufferLength; i++) {
                const barHeight = (dataArray[i] / 255) * waveformCanvas.height;
                ctx.fillStyle = "#6366f1";
                ctx.fillRect(x, waveformCanvas.height - barHeight, barWidth - 1, barHeight);
                x += barWidth;
            }
        }
        draw();
    }

    // --- 6. Handle AI Decision Response ---
    function handleTurnResponse(data) {
        addTranscriptTurn({
            role: "agent",
            intent: data.intent,
            confidence: data.confidence,
            text: data.response_text,
            audio_url: data.audio_url,
            is_tts: data.is_tts,
            is_escalated: data.is_escalated
        });

        playAudio(data.audio_url, data.intent_name, data.confidence);

        if (data.is_escalated) {
            callStateBadge.textContent = "ESCALATED";
            callStateBadge.className = "call-badge escalated";
            escalationAlertBanner.classList.remove("hidden");
            fetchEscalationsCount();
        } else {
            recordingStatus.textContent = "Tap microphone to respond in Tamil";
        }
    }

    function addTranscriptTurn(turn) {
        const div = document.createElement("div");
        div.className = `turn-bubble ${turn.role} ${turn.is_escalated ? 'escalated' : ''}`;

        if (turn.role === "customer") {
            div.innerHTML = `
                <div class="bubble-meta"><span>👤 Donor</span></div>
                <div>${turn.text}</div>
            `;
        } else {
            div.innerHTML = `
                <div class="bubble-meta">
                    <span>🤖 AI Call Agent</span>
                    <div>
                        <span class="badge-tag intent">${turn.intent}</span>
                        <span class="badge-tag conf">Conf: ${(turn.confidence * 100).toFixed(0)}%</span>
                        ${turn.is_tts ? '<span class="badge-tag tts">gTTS</span>' : ''}
                    </div>
                </div>
                <div>${turn.text}</div>
            `;
        }

        transcriptBox.appendChild(div);
        transcriptBox.scrollTop = transcriptBox.scrollHeight;
    }

    function clearTranscript() {
        transcriptBox.innerHTML = "";
    }

    function playAudio(url, intentName, conf) {
        playingIntentBadge.textContent = intentName || "RESPONSE";
        playingConfBadge.textContent = `Conf: ${(conf * 100).toFixed(0)}%`;
        agentAudioPlayer.src = url;
        agentAudioPlayer.onended = () => {
            if (activeCallSessionId && !isRecording) {
                recordingStatus.textContent = "Auto-listening... Speak now in Tamil";
                setTimeout(() => { startRecording(); }, 400);
            }
        };
        agentAudioPlayer.play().catch(e => console.log("Auto-play note:", e));
    }

    // --- 7. Fetch Campaign & Donor CRM Data ---
    async function loadCampaignData() {
        try {
            const resCamp = await fetch("/api/v1/campaigns");
            const campaigns = await resCamp.json();
            const campGrid = document.getElementById("campaignSummaryGrid");
            
            campGrid.innerHTML = campaigns.map(c => `
                <div class="campaign-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <strong style="font-size:15px; color:#fff;">${c.name}</strong>
                        <span class="status-pill active">${c.status}</span>
                    </div>
                    <p style="font-size:12px; color:#9ca3af; margin-bottom:12px;">${c.description}</p>
                    <div style="display:flex; gap:16px; font-size:12px;">
                        <div>Target Donors: <strong>${c.total_customers}</strong></div>
                        <div>Completed Calls: <strong>${c.completed_calls}</strong></div>
                        <div>Escalations: <strong style="color:#ef4444;">${c.escalated_calls}</strong></div>
                    </div>
                </div>
            `).join("");

            const resCust = await fetch("/api/v1/campaigns/1/customers");
            const customers = await resCust.json();
            const crmTable = document.getElementById("donorCrmTableBody");

            crmTable.innerHTML = customers.map(d => `
                <tr>
                    <td><code>${d.customer_id}</code></td>
                    <td><strong>${d.name_ta}</strong><br/><span style="font-size:11px; color:#9ca3af;">${d.name_en}</span></td>
                    <td>${d.phone}</td>
                    <td>${d.plan_type}</td>
                    <td>₹${d.premium_amount.toLocaleString()}</td>
                    <td>${d.due_date}</td>
                    <td><span class="badge-tag conf">${d.sum_assured}% 80G</span></td>
                    <td>
                        <button class="chip" style="background:#6366f1; color:white;" onclick="alert('Initiating outbound call to ${d.phone}')">
                            📞 Dial Now
                        </button>
                    </td>
                </tr>
            `).join("");

        } catch (err) {
            console.error("Error loading campaign data:", err);
        }
    }

    // --- 8. Fetch Human Agent Escalations ---
    async function loadEscalationsData() {
        try {
            const res = await fetch("/api/v1/agent/escalations");
            const tickets = await res.json();
            
            const queueList = document.getElementById("escalationQueueList");
            const countBadge = document.getElementById("escalationBadgeCount");

            if (tickets.length > 0) {
                countBadge.textContent = tickets.filter(t => t.status === "PENDING").length;
                countBadge.classList.remove("hidden");
            }

            queueList.innerHTML = tickets.map((t, idx) => `
                <div class="escalation-card ${idx === 0 ? 'selected' : ''}" onclick="showHandoffDetail(${t.id})">
                    <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                        <strong>${t.customer_name} (${t.phone})</strong>
                        <span class="badge-tag ${t.status === 'PENDING' ? 'intent' : 'conf'}">${t.status}</span>
                    </div>
                    <div style="font-size:12px; color:#fca5a5;">⚠️ ${t.escalation_reason}</div>
                    <div style="font-size:11px; color:#9ca3af; margin-top:4px;">Time: ${new Date(t.created_at).toLocaleTimeString()}</div>
                </div>
            `).join("");

            if (tickets.length > 0) {
                renderHandoffDetail(tickets[0]);
            }
        } catch (err) {
            console.error("Error loading escalations data:", err);
        }
    }

    window.showHandoffDetail = async function(ticketId) {
        const res = await fetch("/api/v1/agent/escalations");
        const tickets = await res.json();
        const ticket = tickets.find(t => t.id === ticketId);
        if (ticket) renderHandoffDetail(ticket);
    };

    function renderHandoffDetail(t) {
        const detailView = document.getElementById("handoffDetailView");
        detailView.innerHTML = `
            <div class="detail-section">
                <div class="detail-title">Donor & Policy Summary</div>
                <div class="detail-box">
                    <strong>${t.customer_name}</strong> | Phone: ${t.phone} | Policy ID: ${t.policy_number || 'N/A'}<br/>
                    Intent Identified: <span class="badge-tag intent">${t.intent}</span> (Conf: ${(t.confidence_score * 100).toFixed(0)}%)
                </div>
            </div>
            <div class="detail-section">
                <div class="detail-title">Reason for Transfer</div>
                <div class="detail-box" style="border-color:rgba(239,68,68,0.4); color:#fca5a5;">
                    ⚠️ ${t.escalation_reason}
                </div>
            </div>
            <div class="detail-section">
                <div class="detail-title">Conversation Summary & History</div>
                <div class="detail-box" style="white-space:pre-wrap;">${t.conversation_summary}</div>
            </div>
            <div class="detail-section">
                <div class="detail-title">Responses Provided by AI</div>
                <div class="detail-box">${t.responses_provided}</div>
            </div>
            <div style="display:flex; gap:12px; margin-top:20px;">
                <button class="btn btn-call-start" onclick="resolveEscalation(${t.id})">
                    ✅ Take Over & Mark Resolved
                </button>
            </div>
        `;
    }

    window.resolveEscalation = async function(ticketId) {
        try {
            const formData = new FormData();
            formData.append("agent_notes", "Human officer handled donor query and resolved call.");
            await fetch(`/api/v1/agent/escalations/${ticketId}/resolve`, { method: "POST", body: formData });
            alert(`Escalation ticket #${ticketId} resolved.`);
            loadEscalationsData();
        } catch (err) {
            console.error("Error resolving escalation:", err);
        }
    };

    async function fetchEscalationsCount() {
        const res = await fetch("/api/v1/agent/escalations");
        const tickets = await res.json();
        const pending = tickets.filter(t => t.status === "PENDING").length;
        if (pending > 0) {
            escalationBadgeCount.textContent = pending;
            escalationBadgeCount.classList.remove("hidden");
        }
    }

    // --- 9. Fetch Analytics Dashboard Data ---
    async function loadAnalyticsData() {
        try {
            const res = await fetch("/api/v1/analytics/dashboard");
            const data = await res.json();

            document.getElementById("statTotalCalls").textContent = data.metrics.total_outbound_calls;
            document.getElementById("statAiResolved").textContent = data.metrics.ai_resolved_calls;
            document.getElementById("statHumanEscalated").textContent = data.metrics.human_escalated_calls;
            document.getElementById("statResolutionRate").textContent = `${data.metrics.ai_resolution_rate}%`;
            document.getElementById("statAvgConf").textContent = data.metrics.avg_confidence_score;

            const logsTable = document.getElementById("analyticsLogsTableBody");
            logsTable.innerHTML = data.recent_logs.map(l => `
                <tr>
                    <td>${new Date(l.timestamp).toLocaleTimeString()}</td>
                    <td><span class="badge-tag intent">${l.source_type}</span></td>
                    <td>${l.transcription}</td>
                    <td><code>${l.classified_intent}</code></td>
                    <td>${l.detected_language.toUpperCase()}</td>
                    <td>${(l.confidence_score * 100).toFixed(0)}%</td>
                    <td>${l.processing_time_ms} ms</td>
                </tr>
            `).join("");
        } catch (err) {
            console.error("Error loading analytics:", err);
        }
    }
});
