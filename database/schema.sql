CREATE TABLE IF NOT EXISTS guild_config (
    guild_id TEXT PRIMARY KEY,
    anti_spam BOOLEAN DEFAULT 1,
    anti_raid BOOLEAN DEFAULT 1,
    anti_links BOOLEAN DEFAULT 1,
    log_channel_id TEXT,
    ticket_category_id TEXT
);

CREATE TABLE IF NOT EXISTS security_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT,
    user_id TEXT,
    action TEXT,
    reason TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tickets (
    ticket_id TEXT PRIMARY KEY,
    user_id TEXT,
    channel_id TEXT,
    status TEXT DEFAULT 'open',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS custom_commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT,
    trigger_name TEXT,
    description TEXT,
    reply_text TEXT,
    embed_title TEXT,
    embed_color TEXT DEFAULT '#3b82f6'
);

-- Configuración del bot por guild (sistema key-value)
CREATE TABLE IF NOT EXISTS guild_config_kv (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT,
    UNIQUE(guild_id, key)
);