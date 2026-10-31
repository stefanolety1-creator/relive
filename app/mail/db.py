import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime
from email.message import EmailMessage
import email.policy

from app.database import get_db, get_user_by_email
from app.storage.manager import get_storage_backend

def init_mail_db():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                folder TEXT DEFAULT 'INBOX',
                sender TEXT NOT NULL,
                recipient TEXT NOT NULL,
                subject TEXT NOT NULL,
                date_str TEXT NOT NULL,
                flags TEXT DEFAULT '',
                size_bytes INTEGER DEFAULT 0,
                raw_mime BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        conn.commit()

def create_welcome_email_if_empty(user_id: int, user_email: str, display_name: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM emails WHERE user_id = ?", (user_id,))
        if cursor.fetchone()['cnt'] > 0:
            return

        msg = EmailMessage()
        msg['Subject'] = "Benvenuto in Windows Live Mail Revival!"
        msg['From'] = "Team Windows Live <welcome@live.it>"
        msg['To'] = f"{display_name} <{user_email}>"
        msg['Date'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0100")
        msg['Message-ID'] = f"<welcome-{user_id}@live.it>"

        body = f"""Ciao {display_name},

Congratulazioni! Il tuo client originale Windows Live Mail è ora collegato con successo al tuo Revival Server.

Dettagli del tuo account unificato:
- Indirizzo: {user_email}
- SkyDrive / Google Drive: Collegato per gli allegati
- Posta in arrivo e invio: Attivi

Tutti gli allegati che riceverai o invierai verranno archiviati automaticamente anche su SkyDrive nella cartella 'Allegati Live Mail'.

Buon divertimento con la suite Windows Live!

Il Team di Windows Live Revival
"""
        msg.set_content(body)
        raw_bytes = msg.as_bytes(policy=email.policy.default)

        cursor.execute("""
            INSERT INTO emails (user_id, folder, sender, recipient, subject, date_str, flags, size_bytes, raw_mime)
            VALUES (?, 'INBOX', ?, ?, ?, ?, '', ?, ?)
        """, (user_id, msg['From'], msg['To'], msg['Subject'], msg['Date'], len(raw_bytes), raw_bytes))
        conn.commit()

def get_emails_in_folder(user_id: int, folder: str = 'INBOX') -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, folder, sender, recipient, subject, date_str, flags, size_bytes
            FROM emails
            WHERE user_id = ? AND folder = ?
            ORDER BY id ASC
        """, (user_id, folder))
        return [dict(r) for r in cursor.fetchall()]

def get_email_raw(user_id: int, email_id: int) -> Optional[bytes]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT raw_mime FROM emails WHERE user_id = ? AND id = ?", (user_id, email_id))
        row = cursor.fetchone()
        return row['raw_mime'] if row else None

def save_email(user_id: int, folder: str, sender: str, recipient: str, subject: str, raw_mime: bytes, flags: str = '') -> int:
    date_str = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0100")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO emails (user_id, folder, sender, recipient, subject, date_str, flags, size_bytes, raw_mime)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, folder, sender, recipient, subject, date_str, flags, len(raw_mime), raw_mime))
        email_id = cursor.lastrowid
        conn.commit()
    return email_id
