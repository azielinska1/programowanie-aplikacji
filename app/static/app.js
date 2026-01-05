const form = document.getElementById('chat-form');
const input = document.getElementById('message');
const answerEl = document.getElementById('answer');
const tracePanel = document.getElementById('trace-panel');
const traceEl = document.getElementById('trace');
const sendBtn = document.getElementById('send');

function setBusy(busy) {
  sendBtn.disabled = busy;
  input.disabled = busy;
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const message = input.value.trim();
  if (!message) return;

  answerEl.textContent = '...';
  tracePanel.hidden = true;
  traceEl.textContent = '';
  setBusy(true);

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });

    const data = await res.json();
    answerEl.textContent = data.answer ?? '';

    if (data.tool_trace) {
      tracePanel.hidden = false;
      traceEl.textContent = JSON.stringify(data.tool_trace, null, 2);
    }
  } catch (err) {
    answerEl.textContent = String(err);
  } finally {
    setBusy(false);
  }
});
