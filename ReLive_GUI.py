import os
import sys
import ssl
import time
import winreg
import ctypes
import platform
import subprocess
import threading
import tempfile
import webbrowser
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

REMOTE_SERVER = os.getenv("RELIVE_REMOTE", "https://relive-ki2f.onrender.com")
DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")
LOG_FILE_PATH = os.path.join(DESKTOP_PATH, "ReLive_Network_Log.txt")
BRIDGE_LOG_PATH = os.path.join(os.path.expanduser("~"), "bridge_activity.log")

EMBEDDED_CRT = """-----BEGIN CERTIFICATE-----
MIIF9jCCBN6gAwIBAgIUT4VC9IaMqEQUNILhxM7eGbnf7tswDQYJKoZIhvcNAQEL
BQAwRjElMCMGA1UEAwwcV2luZG93cyBMaXZlIFJldml2YWwgUm9vdCBDQTEdMBsG
A1UECgwUV2luZG93cyBMaXZlIFJldml2YWwwHhcNMjYxMDMwMTgzNzA5WhcNMzYx
MDI4MTgzNzA5WjBGMSUwIwYDVQQDDBxXaW5kb3dzIExpdmUgUmV2aXZhbCBSb290
IENBMR0wGwYDVQQKDBRXaW5kb3dzIExpdmUgUmV2aXZhbDCCASIwDQYJKoZIhvcN
AQEBBQADggEPADCCAQoCggEBANhIURkZpurlAUuHHZybPMVjrQ1mhz7aCmZhNZhy
+4oXM2HIjDl7xP/6CuWhsaQkFOapBKuQJMznUBOhX/pxqJBrrP9IRQ0T0eXbexXl
mRh9DBPaFS0v7mKYw3i3Lj/622RPuZMgijvizMS9qX8IVbV1eTnDF+GImF9h57Ca
nbD3GutcZxdbIzzH/jEyLjRuwMB5n88gKRjtS7/fMlq31yklPxfP9OkxQ9hUPXoe
O00j9g7rUl5wQYD/pTZ3+LFwkCfNiRJyU8gz5jD1gWDx4MqtSvc6qzm+BvNFW33p
+hk0lUNJMvu7YCXtq9khBb/Bk4WYjGVHLgU4QZjxFjIrfvMCAwEAAaOCAtowggLW
MA8GA1UdEwEB/wQFMAMBAf8wggLBBgNVHREEggK4MIICtIIObG9naW4ubGl2ZS5j
b22CEm5leHVzLnBhc3Nwb3J0LmNvbYIPc3BhY2VzLmxpdmUuY29tghRzcGFjZXMt
YmV0YS5saXZlLmNvbYIVcGhvdG9nYWxsZXJ5LmxpdmUuY29tgg9waG90b3MubGl2
ZS5jb22CCmcubGl2ZS5jb22CCWcubXNuLmNvbYIQc3RvcmFnZS5saXZlLmNvbYIP
c3RvcmFnZS5tc24uY29tghV0a3Jkci5zdG9yYWdlLm1zbi5jb22CFWJ5cmRyLnN0
b3JhZ2UubXNuLmNvbYIXYnlyZHIubGl2ZWZpbGVzdG9yZS5jb22CEGNvbnRhY3Rz
Lm1zbi5jb22CG2RpcmVjdG9yeS5zZXJ2aWNlcy5saXZlLmNvbYIQcHJvZmlsZS5s
aXZlLmNvbYIPcGVvcGxlLmxpdmUuY29tghBhY2NvdW50LmxpdmUuY29tgg1zeW5j
LmxpdmUuY29tggxhcGkubGl2ZS5jb22CDHN1cC5saXZlLmNvbYIPc29hcGJveC5t
c24uY29tghtpNjR4LnVzZXJzLnN0b3JhZ2UubGl2ZS5jb22CJGNpZC1kNDQ0NWQw
NmQxNWE4NDY2LnNwYWNlcy5saXZlLmNvbYImY2lkLWQ0NDQ1ZDA2ZDE1YTg0NjYu
c2t5ZHJpdmUubGl2ZS5jb22CK2NpZC1kNDQ0NWQwNmQxNWE4NDY2LnVzZXJzLnN0
b3JhZ2UubGl2ZS5jb22CCioubGl2ZS5jb22CCSoubXNuLmNvbYIOKi5wYXNzcG9y
dC5jb22CEyoubGl2ZWZpbGVzdG9yZS5jb22CEyouc2t5ZHJpdmUubGl2ZS5jb22C
ESouc3BhY2VzLmxpdmUuY29tghEqLnN0b3JhZ2UubXNuLmNvbYIJbG9jYWxob3N0
hwR/AAABMA0GCSqGSIb3DQEBCwUAA4IBAQB1x7HB1G3UzcvyMMlJQBifTe/4MH5K
MYEIcuKH8NvQNUKFfgMJcCmKLZUX6du/IvgPuXIghDMr9dNGwVoIOUFYk40S9y8F
PgIDF0mMzJNBEwaUUG7MSHAfLCQJ5wD0o01gJ0bkdyvKeQW68OpYOmlOt2derAxB
xepagIwbzQBBWuzxrxdW73uQibqDa6O+el0OgW9PGga3vUBjLmPTCsZEbXGN4I3V
LgsJsq0KZhHBIzDbRbdUu1a4GTxp0CNEfCyYCJs1Wv2ZK+BPxVBWcAQDOayL/sds
KZ0TsiqCRiyXka6vInsXHpkwDQDFE5JEN162LSrjXNnKMdYio4jqJdzE
-----END CERTIFICATE-----"""

EMBEDDED_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA2EhRGRmm6uUBS4cdnJs8xWOtDWaHPtoKZhE1mHL7ihczYciM
OXvE//oK5aGxpCQU5qkEq5AkzOdQE6Ff+nGokGus/0hFDRPR5dt7FeWZGH0ME9oV
LS/uYpjDeLcuP/rbZE+5kyCKO+LMxL2pfwhVtXV5OcMX4YiYX2HnsJqdsPca61xn
F1sjPMf+MTIuNG7AwHmfzyApGO1Lv98yWrfXKSU/F8/06TFD2FQ9eh47TSP2DutS
XnBBgP+lNnf4sXCQJ82JEnJTyDPmMPWBYPHgyq1K9zqrOb4G80Vbfen6GTSVQ0ky
+7tgJe2r2SEFv8GThZiMZUcuBThBmPEWMit+8wIDAQABAoIBAAJ65c8rX6Ie6SJk
FL9YelxrFa9rJw7d8jOVVsd+Pgsp0/GBmrYICMzEob5bWc2fikvQ0VhkST++QUlQ
Vujox72MNoog2oXZXdVMbH9mSBijSnGp1QdVHt8rkEZAl3utVTmzvlWFEIC6S43P
/PMTdeQkSjUS2yG/brvdRApe44MFdPiRJ6ztRgv0u3tdwEk1JGbOiFJkGsgqKb5r
xlAKDg/RsEYWJ6clGtZJ3ZsARVpfRbPKDuZwPRcKprrsuXlOSX4EsrWCn0avdcmw
6g6gw5gx7G0/Hq1LII5uUTxKPf+zCGxrBkTnZhYxGnlqXZwdqJeoKqJ9G+1r2kv+
fv5ALNECgYEA68xGxvabziA+L1pMAb2BUYCithw3cHPvHlmu1P3mHDBQGWiLlz8C
rb41TlNqp13jxB5awyWg97/jqBRHKWmUE6kHj9FiKyS8Rp2M6AULFS8AXfoX/6H9
ztBWvfBiIt+P1yGtb4DZWaXFOZjdu8DFpGPloQqAa6FGvlqH4spyhDECgYEA6tAC
ov7ernRU25SQG3IuzXUA8Im3GPUQmoytIlKlEg0vuqBNe16jxtoCWwNQ1qdUm9yM
PJ1s1Hl9fjb8YkMA1aRZvTp6WDmdRkYDAA0Z/NilY9GEH3GqIMgw/GNMINNv5lhN
AlrN7hz2p45/PDS3OMZ8fGtiot6nLRxqkVdQYGMCgYEAyZ4YYqWYoU42fbzCwrYr
7emEtxw3VyL6McRTVnFmoXG5+4/F0+QfwTmjUL7IsiT4zMd7qeLx2QUtfpkgI8vP
vmPIQHOzcdpuVh7+zaEKUemncbOXc5AqefzwPmZdMx5fWn7EUlQlBJ9WnSIVbiWt
mRuFzAYzulPjLn4wNH4QHvECgYBj3qjgboqDpJLa+ar5IW1qkVMe+1PW15SCR0b0
DDaNIPKl67xIto3t65eI4jYltfG0gO9ccJBzJmELp5Ncr6bRNx+77f1PPOH5m5l3
Eht1gSeG9vu86/kyDDNZhVpBs+wqCnBmifyAQ+1cgqz3DGzJRxJ3UK0ZHJ35/9YL
jxluhQKBgQDpMRjF4sMs5QqmJ1+JmhmuzYmwI7nCTDBrOhcX5MxP8J2jCgm9zQsj
ApCA9A01zqpPVo8aSGjxsqeTaaUj5gvYOknPXXekNs3VdPt6kNTUbtxvsUGnDu6W
wzIrxvEwxcTEFkskBehpxU225CbSzC+wFUqk8xO4SMKGdREG+5xo0g==
-----END RSA PRIVATE KEY-----"""

CERT_DIR = os.path.join(tempfile.gettempdir(), "ReLive_Certs")
os.makedirs(CERT_DIR, exist_ok=True)
CERT_FILE = os.path.join(CERT_DIR, "live_revival.crt")
KEY_FILE = os.path.join(CERT_DIR, "live_revival.key")

with open(CERT_FILE, "w", encoding="utf-8") as f:
    f.write(EMBEDDED_CRT.strip() + "\n")
with open(KEY_FILE, "w", encoding="utf-8") as f:
    f.write(EMBEDDED_KEY.strip() + "\n")

gui_logger = None

def log_network_event(entry_text):
    ts = time.strftime('%H:%M:%S')
    formatted = f"[{ts}] {entry_text}"
    try:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass
    try:
        with open(BRIDGE_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass
    if gui_logger:
        gui_logger(entry_text)
    else:
        print(formatted)

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

# -------------------------------------------------------------------
# 1. Reverse Proxy / Bridge for Ports 80 & 443 with Full Diagnostic Logs
# -------------------------------------------------------------------
class ReLiveBridgeHandler(BaseHTTPRequestHandler):
    def do_ANY(self):
        start_time = time.time()
        host = self.headers.get('Host', 'localhost')
        soap_action = self.headers.get('SOAPAction', '')
        user_agent = self.headers.get('User-Agent', '')
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        scheme = "https" if isinstance(self.server.socket, ssl.SSLSocket) or hasattr(self.connection, 'getpeercert') else "http"
        full_req_url = f"{scheme}://{host}{self.path}"

        # 1. Log incoming request
        log_network_event(f"--> [{self.command}] {full_req_url}")
        if soap_action:
            clean_soap = soap_action.replace('"', '').split('/')[-1]
            log_network_event(f"    SOAPAction: {soap_action} (Metodo: {clean_soap})")
        if user_agent and "Windows-Live" in user_agent:
            log_network_event(f"    Client: {user_agent}")

        # 2. Forward upstream to Render cloud
        target_url = f"{REMOTE_SERVER}{self.path}"
        req_headers = {}
        for k, v in self.headers.items():
            if k.lower() not in ('host', 'content-length', 'connection', 'transfer-encoding'):
                req_headers[k] = v
        req_headers['X-Original-Host'] = host
        req_headers['X-Forwarded-Host'] = host

        req = urllib.request.Request(target_url, data=body, headers=req_headers, method=self.command)

        try:
            with urllib.request.urlopen(req, timeout=35) as resp:
                resp_data = resp.read()
                elapsed = int((time.time() - start_time) * 1000)
                self.send_response(resp.status)
                for h_name, h_val in resp.getheaders():
                    if h_name.lower() not in ('transfer-encoding', 'content-encoding', 'connection'):
                        self.send_header(h_name, h_val)
                self.send_header('Content-Length', str(len(resp_data)))
                self.end_headers()
                self.wfile.write(resp_data)
                log_network_event(f"<-- [HTTP {resp.status} OK] {len(resp_data)} bytes in {elapsed}ms -> {self.path}")
        except urllib.error.HTTPError as e:
            elapsed = int((time.time() - start_time) * 1000)
            err_data = e.read()
            self.send_response(e.code)
            for h_name, h_val in e.headers.items():
                if h_name.lower() not in ('transfer-encoding', 'content-encoding', 'connection'):
                    self.send_header(h_name, h_val)
            self.send_header('Content-Length', str(len(err_data)))
            self.end_headers()
            self.wfile.write(err_data)

            preview = ""
            if err_data:
                try:
                    preview = err_data[:120].decode('utf-8', errors='ignore').strip().replace("\n", " ")
                except Exception:
                    pass
            log_network_event(f"<-- [HTTP {e.code}] {self.path} ({elapsed}ms) [ENDPOINT MANCANTE O ERRORE]")
            if preview:
                log_network_event(f"    Risposta: {preview}")
        except Exception as ex:
            elapsed = int((time.time() - start_time) * 1000)
            self.send_response(502)
            msg = b"ReLive Cloud Connection Error"
            self.send_header('Content-Length', str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)
            log_network_event(f"<-- [HTTP 502 Bad Gateway] Errore connessione Cloud ({elapsed}ms): {ex}")

    do_GET = do_ANY
    do_POST = do_ANY
    do_PUT = do_ANY
    do_DELETE = do_ANY
    do_HEAD = do_ANY
    do_OPTIONS = do_ANY

    def log_message(self, format, *args):
        pass

# -------------------------------------------------------------------
# 2. Environment Auto-Repair (Hosts & Cert)
# -------------------------------------------------------------------
ALL_LIVE_DOMAINS = [
    "login.live.com", "nexus.passport.com", "spaces.live.com",
    "spaces-beta.live.com", "photogallery.live.com", "photos.live.com",
    "g.live.com", "g.msn.com", "storage.live.com", "storage.msn.com",
    "tkrdr.storage.msn.com", "byrdr.storage.msn.com", "byrdr.livefilestore.com",
    "contacts.msn.com", "directory.services.live.com", "profile.live.com",
    "people.live.com", "account.live.com", "sync.live.com", "api.live.com",
    "sup.live.com", "soapbox.msn.com", "i64x.users.storage.live.com",
    "cid-d4445d06d15a8466.spaces.live.com", "cid-d4445d06d15a8466.skydrive.live.com",
    "cid-d4445d06d15a8466.users.storage.live.com"
]

def check_and_repair_env():
    # Make sure AutoConfigURL is deleted so no stale proxy interferes
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Internet Settings", 0, winreg.KEY_SET_VALUE)
        try:
            winreg.DeleteValue(key, "AutoConfigURL")
        except Exception:
            pass
        winreg.CloseKey(key)
        ctypes.windll.wininet.InternetSetOptionW(0, 39, 0, 0)
        ctypes.windll.wininet.InternetSetOptionW(0, 37, 0, 0)
    except Exception:
        pass

    # Update hosts file with all domains
    hosts_path = os.path.expandvars(r"%windir%\System32\drivers\etc\hosts")
    try:
        content = ""
        if os.path.exists(hosts_path):
            with open(hosts_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

        missing = [d for d in ALL_LIVE_DOMAINS if d not in content]
        if missing:
            with open(hosts_path, "a", encoding="utf-8") as f:
                f.write("\n# ReLive Windows Live Revival\n")
                for d in missing:
                    f.write(f"127.0.0.1 {d}\n")
            subprocess.run(["ipconfig", "/flushdns"], capture_output=True)
            log_network_event(f"[+] File hosts aggiornato con {len(missing)} domini mancanti.")
        else:
            log_network_event("[+] File hosts verificato: tutti i domini Live sono configurati.")
    except Exception as e:
        log_network_event(f"[!] Errore scrittura file hosts: {e}")

    # Install updated universal SSL certificate into Root store
    try:
        subprocess.run(["certutil.exe", "-addstore", "-f", "Root", CERT_FILE], capture_output=True)
        log_network_event("[+] Certificato SSL Root universale installato e verificato.")
    except Exception:
        pass

# -------------------------------------------------------------------
# 3. ARM64 Watcher
# -------------------------------------------------------------------
def arm64_unlock_watcher():
    user32 = ctypes.windll.user32
    def enum_cb(hwnd, lparam):
        try:
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value.lower()

                class_buff = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, class_buff, 256)
                cls = class_buff.value

                if cls == "#32770" or any(k in title for k in ["accedi", "live", "raccolta", "photo", "corso"]):
                    if title:
                        user32.PostMessageW(hwnd, 0x8521, 0, 0)
        except Exception:
            pass
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    cb_func = WNDENUMPROC(enum_cb)

    while True:
        user32.EnumWindows(cb_func, 0)
        time.sleep(1)

# -------------------------------------------------------------------
# 4. GUI Application
# -------------------------------------------------------------------
class ReLiveApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ReLive — Windows Live Essentials Launcher")
        self.root.geometry("720x620")
        self.root.minsize(650, 530)

        self.style = ttk.Style()
        self.style.theme_use('vista' if 'vista' in self.style.theme_names() else 'clam')

        self._build_ui()
        self._start_services()

    def _build_ui(self):
        header_frame = tk.Frame(self.root, bg="#0d5c96", height=80)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)

        title_lbl = tk.Label(header_frame, text="ReLive Essentials Hub", font=("Segoe UI", 18, "bold"), fg="white", bg="#0d5c96")
        title_lbl.pack(anchor="w", padx=20, pady=(12, 0))

        sub_lbl = tk.Label(header_frame, text="Windows Live Wave 3 Revival Hub & Live Traffic Monitor", font=("Segoe UI", 10), fg="#d0e8fc", bg="#0d5c96")
        sub_lbl.pack(anchor="w", padx=20, pady=(2, 0))

        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        status_group = ttk.LabelFrame(main_frame, text=" Stato Connessione & Servizi ", padding="10")
        status_group.pack(fill=tk.X, pady=(0, 10))

        # Cloud Status
        f_cloud = ttk.Frame(status_group)
        f_cloud.pack(fill=tk.X, pady=2)
        tk.Label(f_cloud, text="●", fg="#107c10", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(f_cloud, text="Server Cloud ReLive:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        ttk.Label(f_cloud, text=" Connesso (Render - relive-ki2f.onrender.com)", font=("Segoe UI", 9)).pack(side=tk.LEFT)

        # Bridge Status
        f_bridge = ttk.Frame(status_group)
        f_bridge.pack(fill=tk.X, pady=2)
        tk.Label(f_bridge, text="●", fg="#107c10", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(f_bridge, text="Bridge Locale:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        ttk.Label(f_bridge, text=" Porte 80 & 443 Attive (Intercettazione e Logging attivi)", font=("Segoe UI", 9)).pack(side=tk.LEFT)

        # ARM64 Status
        arch = platform.machine().lower()
        is_arm = "arm" in arch or "aarch" in arch or os.environ.get("PROCESSOR_ARCHITECTURE", "").lower() == "arm64"
        f_arm = ttk.Frame(status_group)
        f_arm.pack(fill=tk.X, pady=2)
        tk.Label(f_arm, text="●", fg="#107c10" if is_arm else "#888888", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(f_arm, text="Auto-Sblocco ARM64 (0x8521):", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        ttk.Label(f_arm, text=" Attivo in background" if is_arm else " Non necessario (x86/x64 nativo)", font=("Segoe UI", 9)).pack(side=tk.LEFT)

        # Action Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        btn_launch = tk.Button(btn_frame, text="▶  Avvia Raccolta Foto (Photo Gallery)", font=("Segoe UI", 11, "bold"),
                               bg="#0078d4", fg="white", activebackground="#005a9e", activeforeground="white",
                               relief=tk.FLAT, padx=15, pady=8, cursor="hand2", command=self.launch_photo_gallery)
        btn_launch.pack(fill=tk.X, pady=(0, 6))

        sub_btn_frame = ttk.Frame(btn_frame)
        sub_btn_frame.pack(fill=tk.X)

        btn_mail = ttk.Button(sub_btn_frame, text="✉️ Avvia Windows Live Mail", command=self.launch_mail)
        btn_mail.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))

        btn_repair = ttk.Button(sub_btn_frame, text="🛠️ Aggiorna / Ripara Hosts & SSL", command=self.repair_env)
        btn_repair.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2, 4))

        btn_portal = ttk.Button(sub_btn_frame, text="🌐 Portale Web", command=self.open_portal)
        btn_portal.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2, 0))

        # Log Section
        log_group = ttk.LabelFrame(main_frame, text=" Monitor Traffico di Rete in Tempo Reale ", padding="8")
        log_group.pack(fill=tk.BOTH, expand=True)

        log_bar = ttk.Frame(log_group)
        log_bar.pack(fill=tk.X, pady=(0, 4))

        btn_open_log = ttk.Button(log_bar, text="📂 Apri File Log Completo (Desktop)", command=self.open_log_file)
        btn_open_log.pack(side=tk.LEFT, padx=(0, 6))

        btn_clear_log = ttk.Button(log_bar, text="🧹 Pulisci Schermo", command=self.clear_log)
        btn_clear_log.pack(side=tk.LEFT)

        self.log_text = scrolledtext.ScrolledText(log_group, wrap=tk.WORD, font=("Consolas", 9), height=12, bg="#1e1e1e", fg="#d4d4d4", insertbackground="white")
        self.log_text.pack(fill=tk.BOTH, expand=True)

        global gui_logger
        gui_logger = self.log

        self.log("[+] ReLive Hub avviato con successo.")
        self.log(f"[*] Cloud Upstream: {REMOTE_SERVER}")
        self.log(f"[*] File log salvato in tempo reale su: {LOG_FILE_PATH}")
        self.log("[*] In attesa di richieste da Raccolta Foto o Windows Live Mail...")

    def log(self, text):
        def _append():
            ts = time.strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{ts}] {text}\n")
            self.log_text.see(tk.END)
        self.root.after(0, _append)

    def open_log_file(self):
        try:
            if not os.path.exists(LOG_FILE_PATH):
                with open(LOG_FILE_PATH, "w", encoding="utf-8") as f:
                    f.write("# ReLive Network Requests Log\n")
            os.startfile(LOG_FILE_PATH)
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile aprire il file di log: {e}")

    def clear_log(self):
        self.log_text.delete("1.0", tk.END)

    def _start_services(self):
        # 1. Environment check & repair
        threading.Thread(target=check_and_repair_env, daemon=True).start()

        # 2. Start local bridges on 80 & 443
        t80 = threading.Thread(target=self._run_port_80, daemon=True)
        t443 = threading.Thread(target=self._run_port_443, daemon=True)
        t80.start()
        t443.start()

        # 3. ARM64 watcher
        arch = platform.machine().lower()
        is_arm = "arm" in arch or "aarch" in arch or os.environ.get("PROCESSOR_ARCHITECTURE", "").lower() == "arm64"
        if is_arm:
            t_arm = threading.Thread(target=arm64_unlock_watcher, daemon=True)
            t_arm.start()
            self.log("[+] Auto-sblocco ARM64 (0x8521) attivo in background.")

    def _run_port_80(self):
        try:
            httpd = ThreadedHTTPServer(('0.0.0.0', 80), ReLiveBridgeHandler)
            self.log("[+] Porta 80 attiva (HTTP Bridge - intercetta g.live.com e richieste standard).")
            httpd.serve_forever()
        except Exception as e:
            self.log(f"[*] Porta 80 non disponibile: {e}")

    def _run_port_443(self):
        try:
            httpd = ThreadedHTTPServer(('0.0.0.0', 443), ReLiveBridgeHandler)
            ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ctx.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
            httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
            self.log("[+] Porta 443 attiva (HTTPS Bridge SSL - intercetta Spaces, SkyDrive, SchematizedStore).")
            httpd.serve_forever()
        except Exception as e:
            self.log(f"[*] Porta 443 non disponibile: {e}")

    def launch_photo_gallery(self):
        pg_path = r"C:\Program Files (x86)\Windows Live\Photo Gallery\WLXPhotoGallery.exe"
        if os.path.exists(pg_path):
            self.log("[+] Avvio di Windows Live Raccolta Foto...")
            subprocess.Popen([pg_path])
        else:
            messagebox.showwarning("Non trovato", f"Raccolta Foto non trovata in:\n{pg_path}")

    def launch_mail(self):
        mail_path = r"C:\Program Files (x86)\Windows Live\Mail\wlmail.exe"
        if os.path.exists(mail_path):
            self.log("[+] Avvio di Windows Live Mail...")
            subprocess.Popen([mail_path])
        else:
            messagebox.showwarning("Non trovato", f"Windows Live Mail non trovata in:\n{mail_path}")

    def open_portal(self):
        webbrowser.open(REMOTE_SERVER)

    def repair_env(self):
        self.log("[*] Verifica ed eventuale aggiornamento hosts e certificato SSL...")
        check_and_repair_env()
        messagebox.showinfo("ReLive", "File hosts e certificati SSL aggiornati con successo!")

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def main():
    if not is_admin():
        try:
            script = os.path.abspath(sys.argv[0])
            params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
            sys.exit(0)
        except Exception:
            pass

    root = tk.Tk()
    app = ReLiveApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
