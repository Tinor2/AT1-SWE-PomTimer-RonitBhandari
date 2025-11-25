CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE lists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT 0,
    pomo_session INTEGER DEFAULT 25,
    pomo_short_break INTEGER DEFAULT 5,
    pomo_long_break INTEGER DEFAULT 15,
    pomo_current_time INTEGER DEFAULT 0
, user_id INTEGER);
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    list_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    is_done BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, tags TEXT DEFAULT '', user_id INTEGER, position INTEGER DEFAULT 0, parent_id INTEGER DEFAULT NULL, level INTEGER DEFAULT 0, path TEXT DEFAULT NULL,
    FOREIGN KEY (list_id) REFERENCES lists (id) ON DELETE CASCADE
);
CREATE INDEX idx_tasks_list_id ON tasks(list_id);
CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            );
CREATE INDEX idx_tasks_parent_id ON tasks(parent_id);
CREATE INDEX idx_tasks_level ON tasks(level);
CREATE INDEX idx_tasks_path ON tasks(path);
