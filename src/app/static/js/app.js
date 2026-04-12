// 🔊 Speech state
let voicesReady = false;
let isSpeaking = false;

speechSynthesis.onvoiceschanged = () => {
    voicesReady = true;
};

/* ---------------------------
   TEXT-TO-SPEECH
----------------------------*/
function speakText(text) {
    if (!window.speechSynthesis) return;

     speechSynthesis.cancel();
     isSpeaking = false; 

    if (!voicesReady || isSpeaking) return;

   

    const tempDiv = document.createElement("div");
    tempDiv.innerHTML = text;
    const cleanText = tempDiv.innerText || tempDiv.textContent;

    const chunks = cleanText.match(/.{1,300}/g);
    let index = 0;

    function speakChunk() {
        if (index >= chunks.length) {
            isSpeaking = false;
            return;
        }

        const utterance = new SpeechSynthesisUtterance(chunks[index]);
        utterance.rate = 1;
        utterance.pitch = 1;

        utterance.onstart = () => isSpeaking = true;
        utterance.onend = () => {
            index++;
            speakChunk();
        };

        speechSynthesis.speak(utterance);
    }

    speakChunk();
}

function stopSpeaking() {
   if (window.speechSynthesis) {
        speechSynthesis.cancel();
        isSpeaking = false; 
   }     
}

/* ---------------------------
   SESSION HISTORY
----------------------------*/
let sessions = JSON.parse(localStorage.getItem("chatSessions")) || {};
let currentSessionId = null;

function saveSessions() {
    localStorage.setItem("chatSessions", JSON.stringify(sessions));
}

function loadHistoryList() {
    const list = document.getElementById("historyList");
    list.innerHTML = "";
    Object.keys(sessions).forEach(id => {
        const title = sessions[id][0]?.text || "New Chat";
        list.innerHTML += `<li onclick="openSession('${id}')">${title.slice(0,25)}</li>`;
    });
}

function startNewChat() {
    currentSessionId = "session_" + Date.now();
    sessions[currentSessionId] = [];
    saveSessions();
    loadHistoryList();
    chatContainer.innerHTML = "";
}

function openSession(id) {
    currentSessionId = id;
    chatContainer.innerHTML = "";
    sessions[id].forEach(msg => {
        addMessage(msg.text, msg.role, msg.sources);
    });
}

function saveMessage(role, text, sources = []) {
    if (!currentSessionId) startNewChat();
    sessions[currentSessionId].push({ role, text, sources });
    saveSessions();
}

function clearHistory() {
    sessions = {};
    localStorage.clear();
    loadHistoryList();
    chatContainer.innerHTML = "";
}

window.onload = loadHistoryList;

/* ---------------------------
   SEND MESSAGE
----------------------------*/
const chatContainer = document.getElementById("chat-container");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");

userInput.addEventListener("keypress", e => {
    if (e.key === "Enter") handleSend();
});
sendBtn.addEventListener("click", handleSend);

async function handleSend() {
    const text = userInput.value.trim();
    if (!text) return;

    addMessage(text, "user");
    saveMessage("user", text);

    userInput.value = "";
    sendBtn.disabled = true;

    const loadingId = addLoading();

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: text }),
        });

        const data = await response.json();
        removeMessage(loadingId);

        addMessage(data.answer, "bot", data.sources);
        saveMessage("bot", data.answer, data.sources);

    } catch {
        removeMessage(loadingId);
        addMessage("Network error", "bot");
    }

    sendBtn.disabled = false;
    userInput.focus();
}

/* ---------------------------
   VOICE INPUT
----------------------------*/
const micBtn = document.getElementById("mic-btn");

micBtn.addEventListener("click", () => {
    if (!("webkitSpeechRecognition" in window)) {
        alert("Your browser does not support voice recognition.");
        return;
    }

    micBtn.innerText = "🎙️";

    const recognition = new webkitSpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;

    recognition.onresult = (event) => {
        micBtn.innerText = "🎤";
        userInput.value = event.results[0][0].transcript;
        handleSend();
    };

    recognition.onerror = () => micBtn.innerText = "🎤";

    recognition.start();
});

/* ---------------------------
   MESSAGE RENDERING
----------------------------*/
function addMessage(text, sender, sources = []) {
    const div = document.createElement("div");
    div.className = `message ${sender}`;
    const avatar = sender === "user" ? "🧑‍💻" : "🤖";

    let sourcesHtml = "";
    if (Array.isArray(sources) && sources.length > 0) {
        sourcesHtml = `
            <div class="sources-container">
                <div class="source-title"
                     onclick="this.nextElementSibling.style.display=
                     this.nextElementSibling.style.display==='block'?'none':'block'">
                    📚 View ${sources.length} Sources ▼
                </div>
                <div class="source-content">
                    ${sources.map((s,i)=>`[${i+1}] ${s}`).join("<br><br>")}
                </div>
            </div>`;
    }

    const voiceBtn = sender === "bot" ? `
        <button class="speak-btn"
            onclick="speakText(\`${text.replace(/`/g,"\\`")}\`)">🔊 Listen</button>
        <button class="speak-btn" style="color:#dc2626;"
            onclick="stopSpeaking()">⏹ Stop</button>` : "";

    div.innerHTML = `
        <div class="avatar">${avatar}</div>
        <div class="bubble">
            ${text.replace(/\n/g,"<br>")}
            ${voiceBtn}
            ${sourcesHtml}
        </div>
    `;

    chatContainer.appendChild(div);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function addLoading() {
    const id = "loading-" + Date.now();
    const div = document.createElement("div");
    div.className = "message bot";
    div.id = id;
    div.innerHTML = `
        <div class="avatar">🤖</div>
        <div class="bubble">
            <div class="typing-indicator">
                <span></span><span></span><span></span>
            </div>
        </div>`;
    chatContainer.appendChild(div);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return id;
}

function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}
