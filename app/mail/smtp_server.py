import os
import asyncio
import base64
import email
from email import policy
import logging
import io
from typing import Optional, Dict, Any, List

from app.database import authenticate_user, get_user_by_email
from app.mail.db import save_email
from app.storage.manager import get_storage_backend

logger = logging.getLogger("wl_smtp")

class SMTPSession:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer
        self.authenticated_user: Optional[Dict[str, Any]] = None
        self.mail_from: str = ""
        self.rcpt_to: List[str] = []

    async def send_line(self, line: str):
        self.writer.write((line + "\r\n").encode("utf-8"))
        await self.writer.drain()

    async def run(self):
        try:
            peer = self.writer.get_extra_info('peername')
            logger.info(f"Nuova connessione SMTP da {peer}")
            await self.send_line("220 Windows Live Revival SMTP Service Ready")

            while True:
                line_bytes = await self.reader.readline()
                if not line_bytes:
                    break

                line = line_bytes.decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                logger.info(f"SMTP < {line}")
                parts = line.split(" ", 1)
                cmd = parts[0].upper()
                args = parts[1] if len(parts) > 1 else ""

                if cmd in ("HELO", "EHLO"):
                    await self.send_line("250-localhost Hello")
                    await self.send_line("250-AUTH LOGIN PLAIN")
                    await self.send_line("250 8BITMIME")

                elif cmd == "AUTH":
                    auth_type = args.upper()
                    if "PLAIN" in auth_type:
                        parts = args.split(" ")
                        if len(parts) > 1:
                            raw = base64.b64decode(parts[1]).decode("utf-8", errors="ignore")
                            pieces = raw.split("\x00")
                            username = pieces[1] if len(pieces) > 1 else pieces[0]
                            password = pieces[2] if len(pieces) > 2 else ""
                            user = authenticate_user(username, password)
                            if user:
                                self.authenticated_user = user
                                await self.send_line("235 2.7.0 Authentication successful")
                                continue
                        await self.send_line("535 5.7.8 Authentication failed")

                    elif "LOGIN" in auth_type:
                        await self.send_line("334 VXNlcm5hbWU6")
                        u_b64 = (await self.reader.readline()).decode().strip()
                        username = base64.b64decode(u_b64).decode()
                        
                        await self.send_line("334 UGFzc3dvcmQ6")
                        p_b64 = (await self.reader.readline()).decode().strip()
                        password = base64.b64decode(p_b64).decode()

                        user = authenticate_user(username, password)
                        if user:
                            self.authenticated_user = user
                            await self.send_line("235 2.7.0 Authentication successful")
                        else:
                            await self.send_line("535 5.7.8 Authentication credentials invalid")
                    else:
                        await self.send_line("504 Unrecognized authentication type")

                elif cmd == "MAIL":
                    self.mail_from = args.replace("FROM:", "").strip("<> ")
                    await self.send_line("250 2.1.0 Sender OK")

                elif cmd == "RCPT":
                    recip = args.replace("TO:", "").strip("<> ")
                    self.rcpt_to.append(recip)
                    await self.send_line("250 2.1.5 Recipient OK")

                elif cmd == "DATA":
                    await self.send_line("354 Start mail input; end with <CRLF>.<CRLF>")
                    data_lines = []
                    while True:
                        dline = await self.reader.readline()
                        if dline == b".\r\n" or dline == b".\n" or not dline:
                            break
                        data_lines.append(dline)

                    raw_mime = b"".join(data_lines)
                    await self.process_email(raw_mime)
                    await self.send_line("250 2.0.0 OK: Message accepted for delivery")

                elif cmd == "QUIT":
                    await self.send_line("221 2.0.0 Service closing transmission channel")
                    self.writer.close()
                    break

                elif cmd == "RSET":
                    self.mail_from = ""
                    self.rcpt_to = []
                    await self.send_line("250 OK Reset")

                elif cmd == "NOOP":
                    await self.send_line("250 OK")

                else:
                    await self.send_line("502 Command not implemented")

        except (ConnectionResetError, asyncio.IncompleteReadError, BrokenPipeError) as e:
            logger.info(f"Connessione SMTP chiusa: {e}")
        except Exception as e:
            logger.error(f"Errore SMTP: {e}", exc_info=True)
        finally:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception:
                pass

    async def process_email(self, raw_mime: bytes):
        parsed = email.message_from_bytes(raw_mime, policy=policy.default)
        subject = parsed.get("Subject", "(Senza oggetto)")
        sender = self.mail_from or parsed.get("From", "unknown@live.it")

        if self.authenticated_user:
            save_email(
                user_id=self.authenticated_user["id"],
                folder="Sent",
                sender=sender,
                recipient=", ".join(self.rcpt_to),
                subject=subject,
                raw_mime=raw_mime,
                flags="\\Seen"
            )

            # Check attachments and save to SkyDrive / Google Drive
            storage, _ = get_storage_backend()
            for part in parsed.iter_attachments():
                fn = part.get_filename()
                if fn:
                    payload = part.get_payload(decode=True)
                    if payload:
                        stream = io.BytesIO(payload)
                        try:
                            storage.upload_file(
                                user_email=self.authenticated_user["email"],
                                file_name=fn,
                                file_stream=stream,
                                mime_type=part.get_content_type(),
                                parent_folder_id="Allegati Live Mail"
                            )
                            logger.info(f"Allegato '{fn}' salvato in SkyDrive/Drive!")
                        except Exception as e:
                            logger.error(f"Errore salvataggio allegato su SkyDrive: {e}")

        for recip in self.rcpt_to:
            target_user = get_user_by_email(recip)
            if target_user:
                save_email(
                    user_id=target_user["id"],
                    folder="INBOX",
                    sender=sender,
                    recipient=recip,
                    subject=subject,
                    raw_mime=raw_mime,
                    flags=""
                )
                logger.info(f"Email salvata nella INBOX di {recip}")

                # Email forwarding se l'utente ha impostato una casella reale
                forward_to = target_user.get("forward_email")
                if forward_to:
                    logger.info(f"[FORWARD] Inoltro email da {sender} a {forward_to} per l'utente {recip}")
                    # Tentativo di inoltro via relay esterno se configurato
                    relay_host = os.getenv("SMTP_RELAY_HOST")
                    if relay_host:
                        try:
                            import smtplib
                            relay_port = int(os.getenv("SMTP_RELAY_PORT", "587"))
                            relay_user = os.getenv("SMTP_RELAY_USER")
                            relay_pwd = os.getenv("SMTP_RELAY_PASSWORD")
                            with smtplib.SMTP(relay_host, relay_port) as server:
                                server.starttls()
                                if relay_user and relay_pwd:
                                    server.login(relay_user, relay_pwd)
                                server.sendmail(sender, [forward_to], raw_mime)
                            logger.info(f"[FORWARD SUCCESS] Email inoltrata con successo a {forward_to}!")
                        except Exception as e:
                            logger.warning(f"[FORWARD ERROR] Impossibile inoltrare a {forward_to}: {e}")

async def start_smtp_server(host="0.0.0.0", port=587):
    server = await asyncio.start_server(
        lambda r, w: SMTPSession(r, w).run(),
        host,
        port
    )
    logger.info(f"Windows Live Mail SMTP Server in ascolto su {host}:{port}")
    return server
