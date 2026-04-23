let currentSessionId = null;

async function init() {
    await loadSessions();
    if (document.querySelector('.session-item')) {
        currentSessionId = document.querySelector('.session-item').dataset.id;
        document.querySelector('.session-item').classList.add('active');
    }
}

async function loadSessions() {
    const res = await fetch('/api/sessions');
    const sessions = await res.json();
    const list = document.getElementById('session-list');
    list.innerHTML = '';
    sessions.forEach(s => {
        const item = document.createElement('div');
        item.className = 'session-item';
        item.dataset.id = s.id;
        item.textContent = s.name;
        item.onclick = () => selectSession(s.id);
        if (currentSessionId == s.id) item.classList.add('active');
        list.prepend(item);
    });
}

async function createSession() {
    const name = prompt('Enter session name:');
    if (!name) return;
    const res = await fetch('/api/sessions', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name})
    });
    const session = await res.json();
    currentSessionId = session.id;
    await loadSessions();
    // Clear messages
    document.getElementById('chat-messages').innerHTML = '';
}

async function selectSession(id) {
    currentSessionId = id;
    document.querySelectorAll('.session-item').forEach(el => el.classList.remove('active'));
    document.querySelector(`[data-id="${id}"]`).classList.add('active');
    // Optionally load messages, but for simplicity we just clear
    document.getElementById('chat-messages').innerHTML = '';
}

async function sendMessage() {
    const input = document.getElementById('message-input');
    const msg = input.value.trim();
    if (!msg || !currentSessionId) return;
    input.value = '';
    displayMessage('user', msg);
    // Show typing indicator
    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.innerHTML = '<span></span><span></span><span></span>';
    document.getElementById('chat-messages').appendChild(indicator);
    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({session_id: currentSessionId, message: msg})
        });
        const data = await res.json();
        indicator.remove();
        displayMessage('assistant', data.response, data.code);
    } catch (e) {
        indicator.remove();
        displayMessage('assistant', 'Error: ' + e.message);
    }
}

function displayMessage(role, text, code = null) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `message ${role}`;
    let html = text.replace(/\n/g, '<br>');
    if (code) {
        html += `<code>${escapeHtml(code)}<button class="copy-btn" onclick="copyCode(this)">Copy</button></code>`;
    }
    div.innerHTML = html;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function copyCode(btn) {
    const code = btn.parentElement.textContent.replace('Copy', '').trim();
    navigator.clipboard.writeText(code).then(() => {
        btn.textContent = 'Copied!';
        setTimeout(() => btn.textContent = 'Copy', 2000);
    });
}

function showPushModal() {
    if (!currentSessionId) {
        alert('Please select a session first.');
        return;
    }
    document.getElementById('repo-modal').style.display = 'flex';
}

async function confirmPush() {
    const repoName = document.getElementById('repo-name').value.trim();
    if (!repoName) {
        alert('Please enter a repository name.');
        return;
    }
    document.getElementById('repo-modal').style.display = 'none';
    try {
        const res = await fetch('/api/push-to-github', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({session_id: currentSessionId, repo_name: repoName})
        });
        const data = await res.json();
        if (res.ok) {
            displayMessage('assistant', `Code pushed to GitHub: <a href="${data.repo_url}" target="_blank">${data.repo_url}</a>`);
        } else {
            displayMessage('assistant', 'Error: ' + data.detail);
        }
    } catch (e) {
        displayMessage('assistant', 'Error: ' + e.message);
    }
}

document.getElementById('send-btn').addEventListener('click', sendMessage);
document.getElementById('message-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') sendMessage();
});
document.getElementById('push-btn').addEventListener('click', showPushModal);
document.querySelector('.new-session-btn').addEventListener('click', createSession);

init();
