CREATE TABLE IF NOT EXISTS banner (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_by TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,
  content TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS task (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  assigned_by TEXT NOT NULL,
  assigned_to TEXT NOT NULL,
  deadline INTEGER NOT NULL,
  tags TEXT
);
