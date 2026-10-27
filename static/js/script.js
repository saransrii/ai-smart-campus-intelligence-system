/* ==========================================================================
   AI Smart Campus – Intelligence System
   Global Frontend Script (Theme toggle, floating chat, notifications)
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initFloatingChat();
    initAlertsAutoDismiss();
});

/* ---------------- Theme Management ---------------- */
function initTheme() {
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    const themeIcon = document.getElementById('themeIcon');
    if (!themeToggleBtn) return;

    const savedTheme = localStorage.getItem('smartCampusTheme') || 'theme-light';
    document.body.className = savedTheme;
    updateThemeIcon(savedTheme);

    themeToggleBtn.addEventListener('click', () => {
        const isDark = document.body.classList.contains('theme-dark');
        const newTheme = isDark ? 'theme-light' : 'theme-dark';
        document.body.className = newTheme;
        localStorage.setItem('smartCampusTheme', newTheme);
        updateThemeIcon(newTheme);
    });
}

function updateThemeIcon(theme) {
    const icon = document.getElementById('themeIcon');
    if (!icon) return;
    if (theme === 'theme-dark') {
        icon.className = 'fa-solid fa-sun text-warning';
    } else {
        icon.className = 'fa-solid fa-moon text-secondary';
    }
}

/* ---------------- Alerts Auto-Dismiss ---------------- */
function initAlertsAutoDismiss() {
    const alerts = document.querySelectorAll('.campus-alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 6000);
    });
}

/* ---------------- Floating AI Chatbot Widget ---------------- */
function initFloatingChat() {
    const trigger = document.getElementById('floatingChatTrigger');
    const windowEl = document.getElementById('floatingChatWindow');
    const closeBtn = document.getElementById('closeFloatingChat');

    if (!trigger || !windowEl) return;

    trigger.addEventListener('click', () => {
        windowEl.classList.toggle('d-none');
        if (!windowEl.classList.contains('d-none')) {
            const input = document.getElementById('floatingChatInput');
            if (input) input.focus();
        }
    });

    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            windowEl.classList.add('d-none');
        });
    }
}

function handleFloatingKey(e) {
    if (e.key === 'Enter') {
        submitFloatingChat();
    }
}

function sendFloatingQuery(query) {
    const input = document.getElementById('floatingChatInput');
    if (input) {
        input.value = query;
        submitFloatingChat();
    }
}

async function submitFloatingChat() {
    const input = document.getElementById('floatingChatInput');
    const text = input ? input.value.trim() : '';
    if (!text) return;

    input.value = '';
    const messages = document.getElementById('floatingChatMessages');

    // Append User Message
    const userDiv = document.createElement('div');
    userDiv.className = 'chat-msg user-msg text-end mb-2';
    userDiv.innerHTML = `<span class="badge bg-primary text-white p-2 text-wrap text-start rounded-3" style="max-width: 85%;">${escapeHtml(text)}</span>`;
    messages.appendChild(userDiv);
    messages.scrollTop = messages.scrollHeight;

    // Append AI Typing indicator
    const typingDiv = document.createElement('div');
    typingDiv.className = 'chat-msg ai-msg mb-2';
    typingDiv.innerHTML = `<span class="badge bg-light text-muted p-2 rounded-3"><i class="fa-solid fa-spinner fa-spin me-1"></i> Thinking...</span>`;
    messages.appendChild(typingDiv);
    messages.scrollTop = messages.scrollHeight;

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        });
        const data = await res.json();
        typingDiv.remove();

        const aiDiv = document.createElement('div');
        aiDiv.className = 'chat-msg ai-msg mb-2';
        
        let answerText = data.answer || "I could not retrieve an answer at this time.";
        let formatted = answerText
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');

        aiDiv.innerHTML = `
            <div class="msg-bubble p-2 bg-soft-primary rounded-3 text-dark">
                ${formatted}
            </div>
        `;
        messages.appendChild(aiDiv);
        messages.scrollTop = messages.scrollHeight;
    } catch (err) {
        typingDiv.remove();
        const errDiv = document.createElement('div');
        errDiv.className = 'chat-msg ai-msg mb-2';
        errDiv.innerHTML = `<span class="badge bg-danger text-white p-2 rounded-3">Connection error.</span>`;
        messages.appendChild(errDiv);
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.innerText = text;
    return div.innerHTML;
}
