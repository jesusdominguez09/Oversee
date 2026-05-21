/* ═══════════════════════════════════════════════════════════════
   OVERSEE DASHBOARD — app.js v2
   Arquitectura: SPA con navegación, WebSocket en vivo,
   sincronización bidireccional de config con el bot.
═══════════════════════════════════════════════════════════════ */

const API = '/api';
let ws = null;
let wsReconnectTimer = null;

// ── ROUTER SPA ──────────────────────────────────────────────────
function initNav() {
    document.querySelectorAll('.nav-link[data-target]').forEach(link => {
        link.addEventListener('click', e => {
            e.preventDefault();
            navigateTo(link.dataset.target);
        });
    });
}

function navigateTo(targetId) {
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));

    const link = document.querySelector(`.nav-link[data-target="${targetId}"]`);
    const view = document.getElementById(targetId);
    if (link) link.classList.add('active');
    if (view) view.classList.add('active');
}

// ── WEBSOCKET ────────────────────────────────────────────────────
function connectWS() {
    const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
    ws = new WebSocket(`${protocol}://${location.host}/ws`);

    ws.onopen = () => {
        setWsStatus(true);
        clearTimeout(wsReconnectTimer);
        console.log('WebSocket connected');
    };

    ws.onmessage = ({ data }) => {
        try {
            const msg = JSON.parse(data);
            handleWsEvent(msg);
        } catch (err) {
            console.error('WS Parse Error:', err);
        }
    };

    ws.onclose = () => {
        setWsStatus(false);
        console.log('WebSocket disconnected, reconnecting in 4s...');
        wsReconnectTimer = setTimeout(connectWS, 4000);
    };

    ws.onerror = (err) => {
        console.error('WebSocket error:', err);
        ws.close();
    };
}

function setWsStatus(online) {
    const dot   = document.getElementById('ws-dot');
    const label = document.getElementById('ws-label');
    if (!dot) return;
    dot.className = `pulse-dot ${online ? 'online' : 'offline'}`;
    label.textContent = online ? 'En vivo' : 'Reconectando';
}

function handleWsEvent(msg) {
    switch (msg.type) {
        case 'security_alert':
            pushLog('alert', `[AUTOMOD] ${msg.data.threat} — ${msg.data.user}`);
            break;
        case 'system':
            pushLog('system', `[SISTEMA] ${msg.data.message}`);
            break;
        case 'chat_activity':
            pushLog('info', `[MSG] #${msg.data.channel} — ${msg.data.user}: ${msg.data.content}`);
            break;
        case 'stats_update':
            updateStats(msg.data);
            break;
    }
}

// ── LIVE LOG FEED ────────────────────────────────────────────────
function pushLog(type, text) {
    const el = document.getElementById('live-logs');
    if (!el) return;

    const ts = new Date().toLocaleTimeString('es-ES', { hour12: false });
    const div = document.createElement('div');
    div.className = `log-entry ${type}`;
    div.innerHTML = `<span class="ts">${ts}</span>${escHtml(text)}`;
    el.appendChild(div);
    el.scrollTop = el.scrollHeight;

    // cap a 60 entradas
    while (el.children.length > 60) el.removeChild(el.firstChild);
}

function startMockLogs() {
    const events = [
        ['info',   '[MSG] #general — Carlos: ¿alguien sabe cuándo es el evento?'],
        ['alert',  '[AUTOMOD] Spam detectado — timeout 5min a User#7821'],
        ['system', '[TICKETS] Ticket #TK-8904 abierto por nexo_dev'],
        ['ok',     '[AUTOMOD] Link malicioso bloqueado — discord.gift'],
        ['system', '[VOICE] Canal temporal creado por Zack#1029'],
        ['info',   '[BOT] Comando /reglas usado por Maria_Dev en #comandos'],
    ];
    setInterval(() => {
        const [type, msg] = events[Math.floor(Math.random() * events.length)];
        pushLog(type, msg);
    }, 5000);
}

// ── STATS ────────────────────────────────────────────────────────
async function loadStats() {
    try {
        const data = await apiFetch('/api/stats');
        if (!data) {
            console.log('Stats unavailable, bot may be offline');
            setOfflineState();
            return;
        }
        updateStats(data);

        const gdEl = document.getElementById('guild-id-display');
        if (data.guild_id && gdEl) gdEl.textContent = `ID: ${data.guild_id}`;

        const pingEl = document.getElementById('val-ping');
        if (pingEl) pingEl.textContent = `${data.bot_ping ?? '--'} ms`;

        const statusDot   = document.getElementById('status-dot');
        const statusLabel = document.getElementById('status-label');
        if (statusDot)  { statusDot.className = 'pulse-dot online'; }
        if (statusLabel) { statusLabel.textContent = 'Operativo'; }

    } catch (err) {
        console.error('Stats error:', err);
        setOfflineState();
    }
}

function setOfflineState() {
    const statusLabel = document.getElementById('status-label');
    const statusDot = document.getElementById('status-dot');
    if (statusLabel) statusLabel.textContent = 'Offline';
    if (statusDot) statusDot.className = 'pulse-dot offline';
}

function updateStats(data) {
    const set = (id, val) => { const el = document.getElementById(id); if (el && val !== undefined) el.textContent = val.toLocaleString(); };
    set('val-members', data.total_members);
    set('val-threats',  data.threats_blocked);
    set('val-tickets',  data.active_tickets);
    set('val-online',   data.online_members);
}

// ── CONFIG API ───────────────────────────────────────────────────
function collectConfig(section) {
    const get  = id  => document.getElementById(id);
    const val  = id  => get(id)?.value ?? null;
    const chk  = id  => get(id)?.checked ?? false;

    const configs = {
        general: {
            welcome_enabled:   chk('tog-welcome'),
            welcome_channel:   val('welcome-channel'),
            welcome_message:   val('welcome-message'),
            welcome_color:     val('welcome-color'),
            welcome_img:       val('welcome-img'),
            autorole_enabled:  chk('tog-autorole'),
            autorole_user:     val('autorole-user'),
            autorole_bot:      val('autorole-bot'),
            autorole_dm:       val('autorole-dm'),
            bye_enabled:       chk('tog-bye'),
            bye_channel:       val('bye-channel'),
            bye_message:       val('bye-message'),
            bot_prefix:        val('bot-prefix'),
            bot_lang:          val('bot-lang'),
            bot_dms:           chk('tog-dms'),
            bot_quiet:         chk('tog-quiet'),
        },
        security: {
            antispam_enabled:  chk('tog-antispam'),
            spam_limit:        parseInt(val('spam-limit')),
            spam_window:       parseInt(val('spam-window')),
            spam_action:       val('spam-action'),
            spam_timeout:      parseInt(val('spam-timeout')),
            spam_dm:           chk('spam-dm'),
            antilinks_enabled: chk('tog-antilinks'),
            links_mode:        val('links-mode'),
            links_allow_media: chk('links-allow-media'),
            links_allow_trusted: chk('links-allow-trusted'),
            wordfilter_enabled: chk('tog-wordfilter'),
            blacklist_words:   val('blacklist-words'),
            wordfilter_action: val('wordfilter-action'),
            antiraid_enabled:  chk('tog-antiraid'),
            raid_limit:        parseInt(val('raid-limit')),
            raid_window:       parseInt(val('raid-window')),
            raid_action:       val('raid-action'),
        },
        logs: {
            mod_log_enabled:     chk('log-mod-enabled'),
            mod_log_channel:     val('log-mod-channel'),
            msg_log_enabled:     chk('log-msg-enabled'),
            msg_log_channel:     val('log-msg-channel'),
            member_log_enabled:  chk('log-member-enabled'),
            member_log_channel:  val('log-member-channel'),
            server_log_enabled:  chk('log-server-enabled'),
            server_log_channel:  val('log-server-channel'),
            voice_log_enabled:   chk('log-voice-enabled'),
            voice_log_channel:   val('log-voice-channel'),
        },
        tickets: {
            ticket_category:       val('ticket-category'),
            ticket_transcripts:    val('ticket-transcripts'),
            ticket_staff_role:     val('ticket-staff-role'),
            ticket_max:            parseInt(val('ticket-max')),
            ticket_embed_title:    val('ticket-embed-title'),
            ticket_embed_body:     val('ticket-embed-body'),
            ticket_color:          val('ticket-color'),
            ticket_ping_staff:     chk('ticket-ping-staff'),
        },
    };

    return configs[section] ?? {};
}

async function saveConfig(section) {
    const btn = document.querySelector(`[data-save="${section}"]`);
    if (btn) { btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Aplicando...'; btn.disabled = true; }

    const payload = collectConfig(section);

    try {
        const res = await apiFetch(`/api/config/${section}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        if (res) {
            showToast(`${sectionLabel(section)} aplicado al bot`, 'success');
        } else {
            showToast('Error al guardar', 'error');
        }
    } catch (_) {
        showToast('Sin conexión con el bot', 'error');
    } finally {
        if (btn) { btn.innerHTML = '<i class="fa-solid fa-cloud-arrow-up"></i> Aplicar al bot'; btn.disabled = false; }
    }
}

function sectionLabel(s) {
    return { general: 'Configuración general', security: 'Automod', logs: 'Logs', tickets: 'Tickets' }[s] || s;
}

// ── COMMAND BUILDER ──────────────────────────────────────────────
function initCommandBuilder() {
    const color   = document.getElementById('cmd-color');
    const title   = document.getElementById('cmd-title');
    const text    = document.getElementById('cmd-text');
    const embed   = document.getElementById('live-embed');
    const prevTitle = document.getElementById('preview-title');
    const prevDesc  = document.getElementById('preview-desc');
    const saveBtn   = document.getElementById('btn-save-command');
    const colorLabel= document.getElementById('cmd-color-label');

    if (!color) return;

    color.addEventListener('input', e => {
        embed.style.borderLeftColor = e.target.value;
        if (colorLabel) colorLabel.textContent = e.target.value;
    });
    title.addEventListener('input', e => {
        prevTitle.textContent = e.target.value || 'Título del Embed';
    });
    text.addEventListener('input', e => {
        let t = e.target.value || 'Descripción del mensaje...';
        t = t.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        t = t.replace(/\*(.*?)\*/g, '<em>$1</em>');
        prevDesc.innerHTML = t;
    });

    // Sync color pickers across sections
    ['welcome-color', 'ticket-color'].forEach(id => {
        const el = document.getElementById(id);
        const labelId = id + '-label';
        if (!el) return;
        el.addEventListener('input', e => {
            const lbl = document.getElementById(labelId);
            if (lbl) lbl.textContent = e.target.value;
        });
    });

    saveBtn.addEventListener('click', async () => {
        const name = document.getElementById('cmd-name').value.trim().replace('/', '');
        const desc = document.getElementById('cmd-desc').value.trim();
        const txt  = text.value.trim();

        if (!name || !txt) { showToast('Nombre y contenido son obligatorios', 'error'); return; }

        saveBtn.innerHTML = '<i class="fa-solid fa-satellite-dish fa-spin"></i> Inyectando...';
        saveBtn.disabled = true;

        const payload = {
            name, description: desc || 'Comando de Oversee',
            color: color.value,
            title: title.value,
            text: txt,
        };

        try {
            const res = await apiFetch('/api/commands', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            if (res) {
                showToast(`/${name} inyectado en Discord`, 'success');
                document.getElementById('cmd-name').value = '';
                document.getElementById('cmd-desc').value = '';
                title.value = ''; text.value = '';
                prevTitle.textContent = 'Título del Embed';
                prevDesc.textContent  = 'Descripción del mensaje...';
                loadCommandList();
            } else {
                showToast('Error al crear comando', 'error');
            }
        } catch (_) {
            showToast('Sin conexión con el bot', 'error');
        } finally {
            saveBtn.innerHTML = '<i class="fa-solid fa-satellite-dish"></i> Inyectar en Discord';
            saveBtn.disabled = false;
        }
    });

    loadCommandList();
}

async function loadCommandList() {
    const wrap = document.getElementById('cmd-list');
    if (!wrap) return;
    try {
        const cmds = await apiFetch('/api/commands');
        if (!cmds || !cmds.length) {
            wrap.innerHTML = '<div class="empty-state mono">Sin comandos creados</div>';
            return;
        }
        wrap.innerHTML = cmds.map(c => `
            <div class="cmd-item">
                <div>
                    <span class="cmd-item-name">/${c.trigger_name}</span>
                    <span class="cmd-item-desc"> — ${escHtml(c.description || '')}</span>
                </div>
                <button class="btn-danger" onclick="deleteCommand(${c.id})"><i class="fa-solid fa-trash"></i></button>
            </div>
        `).join('');
    } catch (_) {
        wrap.innerHTML = '<div class="empty-state mono">Bot desconectado</div>';
    }
}

async function deleteCommand(id) {
    await apiFetch(`/api/commands/${id}`, { method: 'DELETE' });
    loadCommandList();
    showToast('Comando eliminado', 'success');
}

// ── TICKET TABLE ─────────────────────────────────────────────────
function loadMockTickets() {
    const tbody = document.getElementById('tickets-tbody');
    if (!tbody) return;
    const tickets = [
        { id: '#TK-8901', user: 'Zack#1029',    cat: 'Soporte Técnico', status: 'open',   cls: 'open',   time: '12 min' },
        { id: '#TK-8902', user: 'Maria_Dev',     cat: 'Reporte de Raid', status: 'Urgente', cls: 'urgent', time: '2 min' },
        { id: '#TK-8899', user: 'PixelGamer',    cat: 'Apelación Ban',   status: 'Abierto', cls: 'open',   time: '1h 45m' },
    ];
    tbody.innerHTML = tickets.map(t => `
        <tr>
            <td class="mono" style="color:var(--blue)">${t.id}</td>
            <td>${t.user}</td>
            <td>${t.cat}</td>
            <td><span class="badge ${t.cls}">${t.status}</span></td>
            <td class="mono" style="color:var(--muted)">${t.time}</td>
            <td style="display:flex;gap:4px">
                <button class="btn-sm">Ver</button>
                <button class="btn-danger"><i class="fa-solid fa-lock"></i></button>
            </td>
        </tr>
    `).join('');
}

// ── CHART ────────────────────────────────────────────────────────
function initChart() {
    const ctx = document.getElementById('activityChart');
    if (!ctx) return;

    Chart.defaults.color = '#5a5a68';
    Chart.defaults.font.family = "'IBM Plex Mono', monospace";
    Chart.defaults.font.size = 10;

    const gradBlue = ctx.getContext('2d').createLinearGradient(0, 0, 0, 300);
    gradBlue.addColorStop(0, 'rgba(99,102,241,.3)');
    gradBlue.addColorStop(1, 'rgba(99,102,241,0)');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['00:00','01:00','02:00','03:00','04:00','05:00','06:00','07:00','08:00','09:00','10:00','11:00','12:00'],
            datasets: [
                {
                    label: 'Mensajes',
                    data: [42, 65, 110, 280, 520, 690, 810, 740, 600, 480, 390, 520, 610],
                    borderColor: '#6366f1', backgroundColor: gradBlue,
                    borderWidth: 1.5, tension: 0.4, fill: true,
                    pointRadius: 2, pointBackgroundColor: '#6366f1',
                },
                {
                    label: 'Amenazas',
                    data: [1, 0, 3, 8, 14, 22, 18, 12, 9, 6, 4, 7, 11],
                    borderColor: '#f87171', backgroundColor: 'transparent',
                    borderWidth: 1.5, tension: 0.4, fill: false,
                    pointRadius: 2, pointBackgroundColor: '#f87171',
                }
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#18181c',
                    borderColor: '#232328',
                    borderWidth: 1,
                    titleColor: '#e8e8ec',
                    bodyColor: '#5a5a68',
                }
            },
            scales: {
                x: { grid: { color: '#18181c' }, ticks: { maxRotation: 0 } },
                y: { grid: { color: '#18181c' }, beginAtZero: true },
            }
        }
    });
}

// ── GLOBAL SAVE BTN ──────────────────────────────────────────────
function initGlobalSave() {
    document.getElementById('btn-global-save')?.addEventListener('click', () => {
        const active = document.querySelector('.view.active');
        const viewMap = {
            'view-general':  'general',
            'view-security': 'security',
            'view-logs':     'logs',
            'view-tickets':  'tickets',
        };
        const section = viewMap[active?.id];
        if (section) saveConfig(section);
        else showToast('Usa el botón "Aplicar al bot" en cada sección', 'info');
    });

    // Save buttons per section
    document.querySelectorAll('[data-save]').forEach(btn => {
        btn.addEventListener('click', () => saveConfig(btn.dataset.save));
    });
}

// ── TOAST ────────────────────────────────────────────────────────
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const icons = { success: 'fa-circle-check', error: 'fa-circle-exclamation', info: 'fa-circle-info' };
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<i class="fa-solid ${icons[type] || icons.info}"></i><span>${escHtml(message)}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.animation = 'toast-out 200ms ease forwards';
        setTimeout(() => toast.remove(), 200);
    }, 3500);
}

// ── UTILS ────────────────────────────────────────────────────────
function escHtml(str) {
    return String(str)
        .replace(/&/g,'&amp;').replace(/</g,'&lt;')
        .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

async function apiFetch(url, opts = {}) {
    try {
        const res = await fetch(url, opts);
        if (!res.ok) {
            console.error(`API Error: ${res.status}`, res.statusText);
            return null;
        }
        try { return await res.json(); } catch (_) { return true; }
    } catch (err) {
        console.error('Fetch Error:', err);
        return null;
    }
}

// ── INIT ─────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    initNav();
    initGlobalSave();
    initChart();
    initCommandBuilder();
    loadStats();
    loadMockTickets();
    startMockLogs();
    connectWS();

    // Mostrar toast de arranque
    setTimeout(() => showToast('✨ Panel cargado — esperando conexión con el bot', 'info'), 600);

    // Refrescar stats cada 30s
    setInterval(loadStats, 30_000);
});