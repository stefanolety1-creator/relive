import asyncio
import re
import shlex
import logging
import email
from email import policy
from datetime import datetime
from typing import Optional, Dict, Any, List

from app.database import authenticate_user
from app.mail.db import (
    init_mail_db, create_welcome_email_if_empty,
    get_emails_in_folder, get_email_raw
)

logger = logging.getLogger("wl_imap")

def build_envelope(msg) -> str:
    date = msg.get('Date', '')
    subject = msg.get('Subject', '')
    msg_id = msg.get('Message-ID', '')
    
    def parse_addr(header_val):
        if not header_val:
            return "NIL"
        m = re.search(r'(?:"?([^"<]*)"?\s*)?<([^@>]+)@([^>]+)>', str(header_val))
        if m:
            name, user, host = m.group(1) or "", m.group(2), m.group(3)
            name_str = f'"{name.strip()}"' if name.strip() else "NIL"
            return f'(({name_str} NIL "{user}" "{host}"))'
        return '((NIL NIL "user" "localhost"))'

    from_addr = parse_addr(msg.get('From', ''))
    to_addr = parse_addr(msg.get('To', ''))
    clean_subj = str(subject).replace('"', '\\"')
    return f'ENVELOPE ("{date}" "{clean_subj}" {from_addr} {from_addr} {from_addr} {to_addr} NIL NIL NIL "{msg_id}")'

def matches_uid_filter(uid: int, filter_str: str) -> bool:
    if not filter_str or filter_str == "*":
        return True
    filter_str = filter_str.strip()
    if filter_str.isdigit():
        return uid == int(filter_str)
    if ":" in filter_str:
        p1, p2 = filter_str.split(":", 1)
        low = int(p1) if p1.isdigit() else 1
        high = int(p2) if p2.isdigit() else 99999999
        return low <= uid <= high
    if "," in filter_str:
        return uid in [int(x) for x in filter_str.split(",") if x.isdigit()]
    return True

class IMAPSession:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer
        self.authenticated_user: Optional[Dict[str, Any]] = None
        self.selected_folder: Optional[str] = None

    async def send_line(self, line: str):
        self.writer.write((line + "\r\n").encode("utf-8"))
        await self.writer.drain()

    async def send_raw(self, data: bytes):
        self.writer.write(data)
        await self.writer.drain()

    async def run(self):
        try:
            peer = self.writer.get_extra_info('peername')
            logger.info(f"Nuova connessione IMAP da {peer}")
            await self.send_line("* OK Windows Live Mail Revival IMAP4rev1 Server Ready")

            while True:
                line_bytes = await self.reader.readline()
                if not line_bytes:
                    break
                
                if len(line_bytes) >= 3 and line_bytes[0] == 0x16 and line_bytes[1] == 0x03:
                    logger.warning("Rilevato TLS/SSL su porta 143. Disattivare SSL in Windows Live Mail.")
                    break

                line = line_bytes.decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                logger.info(f"IMAP < {line}")
                parts = line.split(" ", 2)
                if len(parts) < 2:
                    continue
                
                tag = parts[0]
                cmd = parts[1].upper()
                args = parts[2] if len(parts) > 2 else ""

                await self.handle_command(tag, cmd, args)
        except (ConnectionResetError, asyncio.IncompleteReadError, BrokenPipeError) as e:
            logger.info(f"Connessione IMAP terminata dal client: {e}")
        except Exception as e:
            logger.error(f"Errore IMAP: {e}", exc_info=True)
        finally:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception:
                pass

    async def handle_command(self, tag: str, cmd: str, args: str):
        if cmd == "CAPABILITY":
            await self.send_line("* CAPABILITY IMAP4rev1 NAMESPACE AUTH=PLAIN IDLE CHILDREN")
            await self.send_line(f"{tag} OK CAPABILITY completed")

        elif cmd == "NOOP":
            await self.send_line(f"{tag} OK NOOP completed")

        elif cmd == "IDLE":
            await self.send_line("+ idling")
            while True:
                line_bytes = await self.reader.readline()
                if not line_bytes:
                    break
                if b"DONE" in line_bytes.upper():
                    break
            await self.send_line(f"{tag} OK IDLE completed")

        elif cmd == "LOGOUT":
            await self.send_line("* BYE Windows Live Mail Server logging out")
            await self.send_line(f"{tag} OK LOGOUT completed")
            self.writer.close()

        elif cmd == "LOGIN":
            match = re.match(r'^(?:"([^"]+)"|(\S+))\s+(?:"([^"]+)"|(\S+))$', args)
            if match:
                username = match.group(1) or match.group(2)
                password = match.group(3) or match.group(4)
                user = authenticate_user(username, password)
                if user:
                    self.authenticated_user = user
                    create_welcome_email_if_empty(user["id"], user["email"], user["display_name"])
                    await self.send_line(f"{tag} OK LOGIN completed")
                    return
            await self.send_line(f"{tag} NO LOGIN failed")

        elif not self.authenticated_user:
            await self.send_line(f"{tag} NO [AUTH] Please authenticate first")

        elif cmd == "NAMESPACE":
            await self.send_line('* NAMESPACE (("" "/")) NIL NIL')
            await self.send_line(f"{tag} OK NAMESPACE completed")

        elif cmd in ("LIST", "LSUB"):
            if args.strip() in ('"" ""', "'' ''"):
                await self.send_line('* LIST (\\Noselect) "/" ""')
            else:
                await self.send_line('* LIST (\\HasNoChildren) "/" "INBOX"')
                await self.send_line('* LIST (\\HasNoChildren \\Sent) "/" "Sent"')
                await self.send_line('* LIST (\\HasNoChildren \\Drafts) "/" "Drafts"')
                await self.send_line('* LIST (\\HasNoChildren \\Trash) "/" "Trash"')
            await self.send_line(f"{tag} OK {cmd} completed")

        elif cmd in ("SELECT", "EXAMINE"):
            folder_clean = args.strip().strip('"').strip("'")
            folder_map = {"INBOX": "INBOX", "SENT": "Sent", "DRAFTS": "Drafts", "TRASH": "Trash", "SENT ITEMS": "Sent", "DELETED ITEMS": "Trash"}
            self.selected_folder = folder_map.get(folder_clean.upper(), "INBOX")

            emails = get_emails_in_folder(self.authenticated_user["id"], self.selected_folder)
            count = len(emails)

            await self.send_line(f"* {count} EXISTS")
            await self.send_line("* 0 RECENT")
            await self.send_line("* FLAGS (\\Answered \\Flagged \\Deleted \\Seen \\Draft)")
            await self.send_line("* OK [PERMANENTFLAGS (\\Answered \\Flagged \\Deleted \\Seen \\Draft \\*)] Flags permitted")
            await self.send_line("* OK [UIDVALIDITY 1] UIDs valid")
            next_uid = (emails[-1]["id"] + 1) if emails else 1
            await self.send_line(f"* OK [UIDNEXT {next_uid}] Predicted next UID")
            await self.send_line(f"{tag} OK [READ-WRITE] {cmd} completed")

        elif cmd in ("SUBSCRIBE", "CREATE"):
            await self.send_line(f"{tag} OK {cmd} completed")

        elif cmd == "CLOSE":
            self.selected_folder = None
            await self.send_line(f"{tag} OK CLOSE completed")

        elif cmd == "STATUS":
            folder_match = re.match(r'^(?:"([^"]+)"|(\S+))\s+\((.*)\)', args)
            if folder_match:
                fname = folder_match.group(1) or folder_match.group(2)
                emails = get_emails_in_folder(self.authenticated_user["id"], fname)
                await self.send_line(f'* STATUS "{fname}" (MESSAGES {len(emails)} UNSEEN 0 UIDNEXT 100 UIDVALIDITY 1)')
            await self.send_line(f"{tag} OK STATUS completed")

        elif cmd == "SEARCH" or (cmd == "UID" and args.upper().startswith("SEARCH")):
            folder = self.selected_folder or "INBOX"
            emails = get_emails_in_folder(self.authenticated_user["id"], folder)
            is_uid = (cmd == "UID")
            if is_uid:
                ids_str = " ".join(str(e["id"]) for e in emails)
            else:
                ids_str = " ".join(str(i) for i in range(1, len(emails) + 1))
            
            await self.send_line(f"* SEARCH {ids_str}".strip())
            await self.send_line(f"{tag} OK SEARCH completed")

        elif cmd in ("FETCH", "UID"):
            is_uid = (cmd == "UID")
            
            # Parse parameters: e.g. "FETCH 8 (BODY.PEEK[] UID)" or "8 (BODY.PEEK[] UID)"
            fetch_str = args
            if is_uid and fetch_str.upper().startswith("FETCH "):
                fetch_str = fetch_str[6:].strip()

            m_fetch = re.match(r'^([0-9\:\*\,]+)\s+(.*)$', fetch_str, re.DOTALL)
            if m_fetch:
                uid_range = m_fetch.group(1)
                req_attrs = m_fetch.group(2).upper()
            else:
                uid_range = "*"
                req_attrs = fetch_str.upper()

            folder = self.selected_folder or "INBOX"
            all_emails = get_emails_in_folder(self.authenticated_user["id"], folder)

            # Filter emails matching requested UID range
            target_emails = []
            for seq, email_item in enumerate(all_emails, start=1):
                check_val = email_item["id"] if is_uid else seq
                if matches_uid_filter(check_val, uid_range):
                    target_emails.append((seq, email_item))

            # Check if body is requested (handles BODY.PEEK[], BODY[], RFC822, etc.)
            req_body = any(k in req_attrs for k in ("BODY[]", "BODY.PEEK[]", "RFC822", "BODY.PEEK[TEXT]", "BODY[TEXT]"))

            for seq, email_item in target_emails:
                msg_id = email_item["id"]
                flags = "\\Seen" if "\\Seen" in email_item["flags"] else ""
                size = email_item["size_bytes"]
                raw_data = get_email_raw(self.authenticated_user["id"], msg_id) or b""

                tokens = []
                tokens.append(f"UID {msg_id}")
                tokens.append(f"FLAGS ({flags})")
                tokens.append(f"RFC822.SIZE {len(raw_data)}")
                tokens.append(f'INTERNALDATE "28-Oct-2026 15:53:00 +0100"')

                if "ENVELOPE" in req_attrs:
                    try:
                        parsed_msg = email.message_from_bytes(raw_data, policy=policy.default)
                        tokens.append(build_envelope(parsed_msg))
                    except Exception:
                        pass

                peek_match = re.search(r'BODY\.PEEK\[HEADER\.FIELDS\s*\(([^)]*)\)\]', req_attrs)
                if peek_match:
                    tokens.append(f"BODY[HEADER.FIELDS ({peek_match.group(1)})] {{2}}\r\n\r\n")

                if req_body:
                    line_start = f"* {seq} FETCH (" + " ".join(t for t in tokens if not t.startswith("BODY")) + f" BODY[] {{{len(raw_data)}}}"
                    await self.send_line(line_start)
                    await self.send_raw(raw_data)
                    await self.send_line(")")
                else:
                    line_resp = f"* {seq} FETCH (" + " ".join(tokens) + ")"
                    await self.send_line(line_resp)

            await self.send_line(f"{tag} OK FETCH completed")

        elif cmd in ("STORE", "UID STORE"):
            await self.send_line(f"{tag} OK STORE completed")

        elif cmd == "EXPUNGE":
            await self.send_line(f"{tag} OK EXPUNGE completed")

        else:
            await self.send_line(f"{tag} OK {cmd} completed")


async def start_imap_server(host="0.0.0.0", port=143):
    init_mail_db()
    server = await asyncio.start_server(
        lambda r, w: IMAPSession(r, w).run(),
        host,
        port
    )
    logger.info(f"Windows Live Mail IMAP Server in ascolto su {host}:{port}")
    return server
