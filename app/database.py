import sqlite3
import hashlib
import secrets
from datetime import datetime
from typing import Optional, Dict, Any
from app.config import DB_PATH, DOMAIN_SUFFIX

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        # Unified Accounts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                first_name TEXT DEFAULT '',
                last_name TEXT DEFAULT '',
                birth_date TEXT DEFAULT '1995-01-01',
                gender TEXT DEFAULT 'm',
                country TEXT DEFAULT 'IT',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                gdrive_user_folder_id TEXT DEFAULT NULL,
                status_message TEXT DEFAULT 'Online con Windows Live'
            );
        """)

        # Auto-migrate existing users table columns if needed
        cursor.execute("PRAGMA table_info(users)")
        columns = [row["name"] for row in cursor.fetchall()]
        if "first_name" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN first_name TEXT DEFAULT ''")
        if "last_name" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN last_name TEXT DEFAULT ''")
        if "birth_date" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN birth_date TEXT DEFAULT '1995-01-01'")
        if "gender" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN gender TEXT DEFAULT 'm'")
        if "country" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN country TEXT DEFAULT 'IT'")
        if "forward_email" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN forward_email TEXT DEFAULT ''")

        # User Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # SkyDrive Files cache / metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skydrive_items (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                parent_id TEXT DEFAULT 'root',
                name TEXT NOT NULL,
                is_folder INTEGER DEFAULT 0,
                mime_type TEXT DEFAULT 'application/octet-stream',
                size_bytes INTEGER DEFAULT 0,
                storage_backend TEXT DEFAULT 'local',
                external_id TEXT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        conn.commit()

def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    return hashed, salt

def normalize_email(email: str) -> str:
    email = email.strip().lower()
    if "@" not in email:
        email = f"{email}{DOMAIN_SUFFIX}"
    return email

def create_user(
    email: str,
    password: str,
    display_name: str,
    first_name: str = "",
    last_name: str = "",
    birth_date: str = "1995-01-01",
    gender: str = "m",
    country: str = "IT",
    forward_email: str = ""
) -> Optional[Dict[str, Any]]:
    norm_email = normalize_email(email)
    hashed, salt = hash_password(password)
    
    clean_display = display_name.strip() or norm_email.split('@')[0]
    if not first_name:
        parts = clean_display.split(None, 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (email, display_name, password_hash, salt, first_name, last_name, birth_date, gender, country, forward_email)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (norm_email, clean_display, hashed, salt, first_name, last_name, birth_date, gender, country, forward_email.strip()))
            user_id = cursor.lastrowid
            conn.commit()
            return get_user_by_id(user_id)
        except sqlite3.IntegrityError:
            return None

def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    norm_email = normalize_email(email)
    user = get_user_by_email(norm_email)
    if not user:
        return None
    
    check_hash, _ = hash_password(password, user['salt'])
    if check_hash == user['password_hash']:
        return user
    return None

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    norm_email = normalize_email(email)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (norm_email,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sessions (token, user_id) VALUES (?, ?)", (token, user_id))
        conn.commit()
    return token

def get_user_by_session(token: str) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.* FROM users u
            JOIN sessions s ON u.id = s.user_id
            WHERE s.token = ?
        """, (token,))
        row = cursor.fetchone()
        return dict(row) if row else None

def delete_session(token: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
