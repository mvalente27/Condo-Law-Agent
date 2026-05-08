"""
Senior New England Common Interest Counsel — Flask Web Interface
================================================================
A lightweight web UI for the Condo Law Agent.

Usage
-----
    python app.py
    # then open http://localhost:5000

Environment
-----------
    OPENAI_API_KEY   Required.  Your OpenAI API key.
    FLASK_SECRET_KEY Optional.  Set a strong value in production.
    PORT             Optional.  Defaults to 5000.
"""

from __future__ import annotations

import os

from flask import Flask, Response, jsonify, render_template_string, request, session

from agent import CondoLawAgent, detect_jurisdiction, extract_pdf_text

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(32))

# One agent per process (suitable for development / single-user use).
# For production, use a per-session agent backed by a persistent store.
_agent_store: dict[str, CondoLawAgent] = {}


def _get_agent(session_id: str) -> CondoLawAgent:
    if session_id not in _agent_store:
        _agent_store[session_id] = CondoLawAgent()
    return _agent_store[session_id]


# ---------------------------------------------------------------------------
# HTML template (single-file SPA — no external dependencies)
# ---------------------------------------------------------------------------

_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Senior NE Common Interest Counsel</title>
<style>
  :root {
    --bg: #0f1117;
    --surface: #1a1d27;
    --border: #2e3147;
    --accent: #4a6cf7;
    --text: #e2e8f0;
    --muted: #8892a4;
    --user-bubble: #1e3a5f;
    --agent-bubble: #1a2438;
    --danger: #e74c3c;
    --success: #27ae60;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: 'Segoe UI', system-ui, sans-serif; display: flex; flex-direction: column; height: 100vh; }

  header { background: var(--surface); border-bottom: 1px solid var(--border); padding: 12px 20px; display: flex; align-items: center; gap: 12px; }
  header h1 { font-size: 1rem; font-weight: 600; letter-spacing: .02em; }
  .jurisdiction-badge { margin-left: auto; background: var(--accent); color: #fff; padding: 3px 10px; border-radius: 20px; font-size: .75rem; font-weight: 600; display: none; }
  .jurisdiction-badge.visible { display: inline-block; }

  #chat { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 14px; }
  .bubble { max-width: 82%; padding: 12px 16px; border-radius: 12px; line-height: 1.6; font-size: .9rem; white-space: pre-wrap; }
  .bubble.user { align-self: flex-end; background: var(--user-bubble); border-bottom-right-radius: 4px; }
  .bubble.agent { align-self: flex-start; background: var(--agent-bubble); border: 1px solid var(--border); border-bottom-left-radius: 4px; }
  .bubble.agent strong { color: var(--accent); }
  .bubble.system { align-self: center; color: var(--muted); font-size: .8rem; font-style: italic; }

  footer { background: var(--surface); border-top: 1px solid var(--border); padding: 12px 16px; }
  .input-row { display: flex; gap: 8px; align-items: flex-end; }
  #msg { flex: 1; background: var(--bg); border: 1px solid var(--border); color: var(--text); border-radius: 8px; padding: 10px 14px; font-size: .9rem; resize: none; min-height: 44px; max-height: 160px; line-height: 1.5; }
  #msg:focus { outline: none; border-color: var(--accent); }
  .btn { background: var(--accent); color: #fff; border: none; border-radius: 8px; padding: 10px 18px; cursor: pointer; font-size: .875rem; font-weight: 600; white-space: nowrap; }
  .btn:disabled { opacity: .5; cursor: not-allowed; }
  .btn.secondary { background: var(--border); }
  .pdf-row { margin-top: 8px; display: flex; align-items: center; gap: 8px; font-size: .8rem; color: var(--muted); }
  #pdf-label { cursor: pointer; text-decoration: underline; color: var(--accent); }
  #pdf-file { display: none; }
  #pdf-name { font-style: italic; }
  .typing-indicator { display: none; align-self: flex-start; padding: 10px 14px; }
  .typing-indicator.visible { display: flex; gap: 4px; }
  .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--muted); animation: bounce 1.2s infinite; }
  .dot:nth-child(2) { animation-delay: .2s; }
  .dot:nth-child(3) { animation-delay: .4s; }
  @keyframes bounce { 0%,60%,100%{transform:translateY(0)} 30%{transform:translateY(-8px)} }
</style>
</head>
<body>
<header>
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#4a6cf7" stroke-width="2"><path d="M3 6h18M3 12h18M3 18h18"/></svg>
  <h1>Senior New England Common Interest Counsel</h1>
  <span class="jurisdiction-badge" id="jur-badge"></span>
</header>

<div id="chat">
  <div class="bubble system">
    Jurisdictions covered: MA · CT · RI · NH · VT · ME &nbsp;|&nbsp;
    Capabilities: Document Intake · Statutory Retrieval · Case Law · Strategic Argumentation
  </div>
</div>
<div class="typing-indicator" id="typing"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>

<footer>
  <div class="input-row">
    <textarea id="msg" rows="1" placeholder="Describe your legal issue…"></textarea>
    <button class="btn" id="send-btn" onclick="sendMessage()">Send</button>
    <button class="btn secondary" onclick="resetChat()">Reset</button>
  </div>
  <div class="pdf-row">
    📄 <label id="pdf-label" for="pdf-file">Upload governing document (PDF)</label>
    <input type="file" id="pdf-file" accept=".pdf" onchange="pdfSelected()" />
    <span id="pdf-name"></span>
    <span id="pdf-status"></span>
  </div>
</footer>

<script>
const chat = document.getElementById('chat');
const msgEl = document.getElementById('msg');
const sendBtn = document.getElementById('send-btn');
const typing = document.getElementById('typing');
const jurBadge = document.getElementById('jur-badge');
let pdfText = null;

function addBubble(role, text) {
  const div = document.createElement('div');
  div.className = `bubble ${role}`;
  div.textContent = text;
  chat.appendChild(div);
  return div;
}

function scrollDown() { chat.scrollTop = chat.scrollHeight; }

function setLoading(on) {
  sendBtn.disabled = on;
  typing.classList.toggle('visible', on);
  scrollDown();
}

async function pdfSelected() {
  const file = document.getElementById('pdf-file').files[0];
  if (!file) return;
  document.getElementById('pdf-name').textContent = file.name;
  document.getElementById('pdf-status').textContent = '⏳ Extracting…';
  const form = new FormData();
  form.append('pdf', file);
  try {
    const res = await fetch('/upload_pdf', { method: 'POST', body: form });
    const data = await res.json();
    if (data.text) {
      pdfText = data.text;
      document.getElementById('pdf-status').textContent = `✓ ${data.chars.toLocaleString()} chars`;
    } else {
      document.getElementById('pdf-status').textContent = '✗ Error';
      console.error(data.error);
    }
  } catch(e) {
    document.getElementById('pdf-status').textContent = '✗ Error';
  }
}

async function sendMessage() {
  const text = msgEl.value.trim();
  if (!text) return;
  msgEl.value = '';
  addBubble('user', text);
  scrollDown();
  setLoading(true);

  const agentBubble = addBubble('agent', '');
  let collected = '';

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, pdf_text: pdfText }),
    });
    pdfText = null; // consume once

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      // Strip SSE framing if present
      chunk.split('\n').forEach(line => {
        if (line.startsWith('data: ')) {
          collected += line.slice(6);
          agentBubble.textContent = collected;
          scrollDown();
        }
      });
    }

    // Update jurisdiction badge
    const jurRes = await fetch('/jurisdiction');
    const jurData = await jurRes.json();
    if (jurData.jurisdiction) {
      jurBadge.textContent = jurData.jurisdiction;
      jurBadge.classList.add('visible');
    }
  } catch(e) {
    agentBubble.textContent = '⚠ Network error. Please try again.';
  } finally {
    setLoading(false);
  }
}

async function resetChat() {
  await fetch('/reset', { method: 'POST' });
  chat.innerHTML = '<div class="bubble system">Conversation reset. Start a new query.</div>';
  jurBadge.textContent = '';
  jurBadge.classList.remove('visible');
  pdfText = null;
  document.getElementById('pdf-name').textContent = '';
  document.getElementById('pdf-status').textContent = '';
}

msgEl.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});

msgEl.addEventListener('input', () => {
  msgEl.style.height = 'auto';
  msgEl.style.height = Math.min(msgEl.scrollHeight, 160) + 'px';
});
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/")
def index() -> str:
    sid = _ensure_session()
    return render_template_string(_HTML, session_id=sid)


@app.route("/chat", methods=["POST"])
def chat() -> Response:
    sid = _ensure_session()
    agent = _get_agent(sid)

    data = request.get_json(force=True)
    message: str = (data.get("message") or "").strip()
    pdf_text: str | None = data.get("pdf_text") or None

    if not message:
        return jsonify({"error": "empty message"}), 400

    def generate() -> Response:
        for chunk in agent.chat(message, document_text=pdf_text, stream=True):  # type: ignore[union-attr]
            yield f"data: {chunk}\n\n"

    return Response(generate(), mimetype="text/event-stream")


@app.route("/upload_pdf", methods=["POST"])
def upload_pdf() -> Response:
    if "pdf" not in request.files:
        return jsonify({"error": "no file provided"}), 400
    pdf_file = request.files["pdf"]
    import tempfile
    import os as _os
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name
            pdf_file.save(tmp_path)
        text = extract_pdf_text(tmp_path)
        return jsonify({"text": text, "chars": len(text)})
    except RuntimeError:
        return jsonify({"error": "Failed to extract text from the uploaded PDF."}), 500
    finally:
        if tmp_path:
            try:
                _os.unlink(tmp_path)
            except OSError:
                pass


@app.route("/jurisdiction", methods=["GET"])
def jurisdiction() -> Response:
    sid = _ensure_session()
    agent = _get_agent(sid)
    return jsonify({"jurisdiction": agent.confirmed_jurisdiction})


@app.route("/reset", methods=["POST"])
def reset() -> Response:
    sid = _ensure_session()
    if sid in _agent_store:
        _agent_store[sid].reset()
    return jsonify({"status": "ok"})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ensure_session() -> str:
    if "sid" not in session:
        import uuid
        session["sid"] = str(uuid.uuid4())
    return session["sid"]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    print(f"Starting Senior New England Common Interest Counsel on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
