-- ThreadHunter database schema
-- Based on idea/06-architecture/memory-model.md

CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY,
    telegram_id TEXT UNIQUE NOT NULL,
    name TEXT,
    added_at DATETIME DEFAULT (datetime('now')),
    last_parsed DATETIME
);

CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY,
    channel_id INTEGER NOT NULL,
    telegram_post_id TEXT UNIQUE NOT NULL,
    raw_text TEXT,
    published_at DATETIME,
    parsed_at DATETIME DEFAULT (datetime('now')),
    processed_at DATETIME,
    has_photo BOOLEAN DEFAULT 0,
    status TEXT DEFAULT 'active',
    FOREIGN KEY (channel_id) REFERENCES channels(id)
);

CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY,
    post_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    value TEXT NOT NULL,
    UNIQUE(type, value, post_id),
    FOREIGN KEY (post_id) REFERENCES posts(id)
);

CREATE TABLE IF NOT EXISTS post_contacts (
    post_id INTEGER NOT NULL,
    contact_id INTEGER NOT NULL,
    PRIMARY KEY (post_id, contact_id),
    FOREIGN KEY (post_id) REFERENCES posts(id),
    FOREIGN KEY (contact_id) REFERENCES contacts(id)
);

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY,
    post_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    value TEXT NOT NULL,
    FOREIGN KEY (post_id) REFERENCES posts(id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_posts_telegram_post_id ON posts(telegram_post_id);
CREATE INDEX IF NOT EXISTS idx_posts_channel_id ON posts(channel_id);
CREATE INDEX IF NOT EXISTS idx_tags_value ON tags(value);
CREATE INDEX IF NOT EXISTS idx_contacts_value ON contacts(value);
CREATE INDEX IF NOT EXISTS idx_posts_published_at ON posts(published_at);
