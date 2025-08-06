-- init_db.sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    vanity TEXT NOT NULL UNIQUE,
    display_name TEXT,
    avatar_url TEXT,
    bio TEXT,
    card_size TEXT,
    twitter TEXT,
    github TEXT,
    website TEXT
);

INSERT INTO users (email, password, vanity)
VALUES ('admin@example.com', 'adminpassplaceholder', 'admin');
