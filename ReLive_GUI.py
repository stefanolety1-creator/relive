import os
import sys
import ssl
import time
import socket
import select
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

EMBEDDED_CRT = """-----BEGIN CERTIFICATE-----
MIIEPjCCAyagAwIBAgIUC0ndG3e/zZUBj4HBVnrf4oAEAlUwDQYJKoZIhvcNAQEL
BQAwRjElMCMGA1UEAwwcV2luZG93cyBMaXZlIFJldml2YWwgUm9vdCBDQTEdMBsG
A1UECgwUV2luZG93cyBMaXZlIFJldml2YWwwHhcNMjYxMDI4MTkxMzIzWhcNMzYx
MDI2MTkxMzIzWjBGMSUwIwYDVQQDDBxXaW5kb3dzIExpdmUgUmV2aXZhbCBSb290
IENBMR0wGwYDVQQKDBRXaW5kb3dzIExpdmUgUmV2aXZhbDCCASIwDQYJKoZIhvcN
AQEBBQADggEPADCCAQoCggEBAIUBCcHRTIecxJI1Uy2XyIV8oywVC21VG4uHli7t
I2vRok/ZJhKJyhwPMHjPKLcoXbKBAM8CAB02T9Ji8RJ/jlMq04wH8g1GU0t46Mpf
sA4SoEEd/jafoIdXJMBdVm1cOCW0oKUpfG5CcJIATITOQrN/pr8h1iuCDwvUT0Ac
PTHjQasTBrvMz32nv91yZGvuWMRvpdObWaSAPUr7/zPzzYQ4JtZM6ZXuOY1d1SkK
WzPbdfnRmeWJ98j2rNf25uYWxzhtxjQvd7/sHdRkIapg75qbozwTIa08SUFYAJwp
Mi9XnwrqPrYFDtAwwsLPlhacmCBKaaSBBW8HPa4j+FOZHJ0CAwEAAaOCASIwggEe
MIIBCQYDVR0RBIIBADCB/YIObG9naW4ubGl2ZS5jb22CFG1zbmlhLmxvZ2luLmxp
dmUuY29tghVsb2dpbm5ldC5wYXNzcG9ydC5jb22CEm5leHVzLnBhc3Nwb3J0LmNv
bYIQY29udGFjdHMubXNuLmNvbYIWb21lZ2EuY29udGFjdHMubXNuLmNvbYIcYnly
ZHIub21lZ2EuY29udGFjdHMubXNuLmNvbYIQc3RvcmFnZS5saXZlLmNvbYIPc3Rv
cmFnZS5tc24uY29tghV0a3Jkci5zdG9yYWdlLm1zbi5jb22CF2NpZC0qLnNreWRy
aXZlLmxpdmUuY29tgglsb2NhbGhvc3SHBH8AAAEwDwYDVR0TAQH/BAUwAwEB/zAN
BgkqhkiG9w0BAQsFAAOCAQEAbViRvckl6RjS2EG8eSoYuwU07Qg1mBq77w66793l
fiKiS1BHmVoz2BG4uS9dIH+G2CLytGLvJ1MO7XXyWeEkZsq+l6krtNJacuvn6gIc
0Kpk39Tod/OGCqNOgSOXdCNFWtZHzAaAaCpLpBEhhFQHQfl+LyAClVyc0534l0GY
BpqcRxqeHdlITVbQ8HQoMk5bkewv5iqFhyCy75r31pGxmiOpytT2wiAdl0x/2zDV
qdXVu0/5HY6DF6bgXTa/R38KhByFVjuiQqrv9+HkgpPs4oJ1PY/VCKRS1UZAPv33
b6S5XpjLfQ9Fcr4gL1whBnArHYr2PJ1MVdltE0CRM0iwYg==
-----END CERTIFICATE-----"""

EMBEDDED_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAhQEJwdFMh5zEkjVTLZfIhXyjLBULbVUbi4eWLu0ja9GiT9km
EonKHA8weM8otyhdsoEAzwIAHTZP0mLxEn+OUyrTjAfyDUZTS3joyl+wDhKgQR3+
Np+gh1ckwF1WbVw4JbSgpSl8bkJwkgBMhM5Cs3+mvyHWK4IPC9RPQBw9MeNBqxMG
u8zPfae/3XJka+5YxG+l05tZpIA9Svv/M/PNhDgm1kzple45jV3VKQpbM9t1+dGZ
5Yn3yPas1/bm5hbHOG3GNC93v+wd1GQhqmDvmpujPBMhrTxJQVgAnCkyL1efCuo+
tgUO0DDCws+WFpyYIEpppIEFbwc9riP4U5kcnQIDAQABAoIBAAo8S7duN4ECOAB2
eRm7ohNfxaDpV7FIyO9idlTTLBQqlF6nu+3WS8cABj9t1djOkvNfSSQlJ8QXv2nV
8m51gYr180TGAcMyw8s9mVClr4NNvKZ2O++RNkXkF3B0XmfZHnsMXQaI3EoR897Q
hhL8Wpa8vqTb4kMD5cuHwbeR1MXHdooEN3wt+xGKpy9n2nyCjNmeRnK4596jOwwK
KuMaYE7lPSG7OwjfG2tToM3SVYRLzhqWpM/AWvefDToMYrCxjKqezEC1nt4X9DNZ
6rhy+PX1XVACiinrFjLLEyYVMYFhWR2mv0etsKp6mjc8wRIaEIyIxaw6MVidkGKK
HxbQnvECgYEAuXOE8hRRxkCNZTiE0+INfgkNHi+mpH1Dbc9ZvMRlaV4/9L5bFF0E
QpFBeQ4Kcyb/pGtoTwX3qOs+6baD6AUzZVa1Q+L5YMGG5unw+jbP5rEy8Ub5G4RR
HS5c4uDgbLwd2RYvczTVARJ8A+sgOFfazLZCbTbno6KKfEDjoQ82j9UCgYEAt5nc
bRsipzKcLrw5YLSqctIrRqT6fUqcbhBYVWfaWwx8hX245NNJ1ShepMTHjCVB0pos
t6dmHJ3P4VOrP8thPrKRZ/km4j6woGbTy2HrDzWUsF1q7JRph38Bnbx8L2EPxVjO
ix8Sv6QCN+JSB/8CoXuTyiBnBqV76wSc0PAxBakCgYEAr3lB0zkswxTzdVJMRJxB
Pf9cfTKDUGMCOVYYSAfhGRlIFNFFJvh4fnAo7l09wAWnoLDMqvEvjJLDHatIFnNN
VVb8/vY2FronZjj3fhn9EACc/jW0obfKdH0ZAMfdMqWw7GcUkMLtxSzzUVXaT9W5
Pzg5lFN+TJQQy08u04esjd0CgYBXMj6KnsmNaK7eT0xczlDpKUGeUnoYiRfT+fVJ
0oHUnhCBgZ0PJ/23u21/iWlP+N3S/J/iNSF808JHvGnnaVrs4PfHzn+WEbnm5A8Q
V5fAaG0Oeb9vTmj0DfChjkPYaJuJ2Ux2rDJGS8k160mUPJtuP/eHlm33rR42FsG3
RWuyyQKBgQCz4mfrgRSAWG0fOGov8WwmVxqiMF9zXyp4kAI6GHtU3I00i/gUIjw9
UpSwIU7yEObsn9OrrZ1oYiLo3KlkMs30grWL/E3dvE6/Zhfni42kGerKUoU6kGLo
MjWg/Q9nkxSCQPxX/RiJsY7wXwPdsN2oeQaT6xPiN7mBxkI+fPD+lQ==
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

def log_to_gui(msg):
    try:
        with open(r"C:\Users\stefanodeluca\bridge_activity.log", "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    except Exception:
        pass
    if gui_logger:
        gui_logger(msg)
    else:
        print(msg)

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

# -------------------------------------------------------------------
# 1. Reverse Proxy / Bridge for Ports 80 & 443
# -------------------------------------------------------------------
class ReLiveBridgeHandler(BaseHTTPRequestHandler):
    def do_ANY(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None
        target_url = f"{REMOTE_SERVER}{self.path}"

        req_headers = {}
        for k, v in self.headers.items():
            if k.lower() not in ('host', 'content-length', 'connection', 'transfer-encoding'):
                req_headers[k] = v

        req = urllib.request.Request(target_url, data=body, headers=req_headers, method=self.command)
        short_path = self.path[:40] + ("..." if len(self.path) > 40 else "")
        try:
            with urllib.request.urlopen(req, timeout=35) as resp:
                resp_data = resp.read()
                self.send_response(resp.status)
                for h_name, h_val in resp.getheaders():
                    if h_name.lower() not in ('transfer-encoding', 'content-encoding', 'connection'):
                        self.send_header(h_name, h_val)
                self.send_header('Content-Length', str(len(resp_data)))
                self.end_headers()
                self.wfile.write(resp_data)
                log_to_gui(f"[{resp.status}] {self.command} {short_path}")
        except urllib.error.HTTPError as e:
            err_data = e.read()
            self.send_response(e.code)
            for h_name, h_val in e.headers.items():
                if h_name.lower() not in ('transfer-encoding', 'content-encoding', 'connection'):
                    self.send_header(h_name, h_val)
            self.send_header('Content-Length', str(len(err_data)))
            self.end_headers()
            self.wfile.write(err_data)
            log_to_gui(f"[{e.code}] {self.command} {short_path}")
        except Exception as ex:
            self.send_response(502)
            msg = b"ReLive Cloud Connection Error"
            self.send_header('Content-Length', str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)
            log_to_gui(f"[502] Errore connessione Cloud: {ex}")

    do_GET = do_ANY
    do_POST = do_ANY
    do_PUT = do_ANY
    do_DELETE = do_ANY
    do_HEAD = do_ANY
    do_OPTIONS = do_ANY

    def log_message(self, format, *args):
        pass

# -------------------------------------------------------------------
# 2. Universal PAC Smart Proxy (Catches 100% of *.live.com / *.msn.com)
# -------------------------------------------------------------------
PAC_SCRIPT = """function FindProxyForURL(url, host) {
    if (dnsDomainIs(host, ".live.com") || host === "live.com" ||
        dnsDomainIs(host, ".msn.com") || host === "msn.com" ||
        dnsDomainIs(host, ".passport.com") || host === "passport.com" ||
        dnsDomainIs(host, ".livefilestore.com") || host === "livefilestore.com") {
        return "PROXY 127.0.0.1:8888";
    }
    return "DIRECT";
}"""

class SmartProxyHandler(BaseHTTPRequestHandler):
    def do_CONNECT(self):
        parts = self.path.split(":")
        host = parts[0]
        port = int(parts[1]) if len(parts) > 1 else 443

        is_live = any(host.endswith(d) or host == d.lstrip(".") for d in [
            ".live.com", ".msn.com", ".passport.com", ".livefilestore.com",
            "live.com", "msn.com", "passport.com"
        ])

        dest_host = "127.0.0.1" if is_live else host
        dest_port = 443 if is_live else port

        try:
            upstream = socket.create_connection((dest_host, dest_port), timeout=10)
            self.send_response(200, "Connection Established")
            self.end_headers()
        except Exception as e:
            self.send_error(502, f"Tunnel Error: {e}")
            return

        conns = [self.connection, upstream]
        try:
            while True:
                r, _, x = select.select(conns, [], conns, 30)
                if x or not r:
                    break
                closed = False
                for s in r:
                    other = upstream if s is self.connection else self.connection
                    data = s.recv(8192)
                    if not data:
                        closed = True
                        break
                    other.sendall(data)
                if closed:
                    break
        except Exception:
            pass
        finally:
            upstream.close()

    def do_GET(self):
        if self.path == "/proxy.pac":
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ns-proxy-autoconfig")
            self.send_header("Content-Length", str(len(PAC_SCRIPT)))
            self.end_headers()
            self.wfile.write(PAC_SCRIPT.encode("utf-8"))
            return
        self.forward_http()

    def do_POST(self):
        self.forward_http()

    def forward_http(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None
        
        path = self.path
        if "://" in path:
            path = path.split("://", 1)[1]
            if "/" in path:
                path = "/" + path.split("/", 1)[1]
            else:
                path = "/"

        target_url = f"{REMOTE_SERVER}{path}"
        req_headers = {k: v for k, v in self.headers.items() if k.lower() not in ('host', 'content-length', 'connection')}
        req = urllib.request.Request(target_url, data=body, headers=req_headers, method=self.command)
        try:
            with urllib.request.urlopen(req, timeout=35) as resp:
                resp_data = resp.read()
                self.send_response(resp.status)
                for h, val in resp.getheaders():
                    if h.lower() not in ('transfer-encoding', 'content-encoding', 'connection'):
                        self.send_header(h, val)
                self.send_header('Content-Length', str(len(resp_data)))
                self.end_headers()
                self.wfile.write(resp_data)
        except Exception as e:
            self.send_response(502)
            msg = b"Proxy Forward Error"
            self.send_header('Content-Length', str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)

    def log_message(self, *args):
        pass

def enable_pac_proxy():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Internet Settings", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "AutoConfigURL", 0, winreg.REG_SZ, "http://127.0.0.1:8888/proxy.pac")
        winreg.CloseKey(key)
        ctypes.windll.wininet.InternetSetOptionW(0, 39, 0, 0) # SETTINGS_CHANGED
        ctypes.windll.wininet.InternetSetOptionW(0, 37, 0, 0) # REFRESH
        log_to_gui("[+] Intercettatore *.live.com attivato con successo (PAC Proxy).")
    except Exception as e:
        log_to_gui(f"[!] Errore attivazione PAC proxy: {e}")

def disable_pac_proxy():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Internet Settings", 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, "AutoConfigURL")
        winreg.CloseKey(key)
        ctypes.windll.wininet.InternetSetOptionW(0, 39, 0, 0)
        ctypes.windll.wininet.InternetSetOptionW(0, 37, 0, 0)
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
        self.root.geometry("680x570")
        self.root.minsize(620, 510)

        self.style = ttk.Style()
        self.style.theme_use('vista' if 'vista' in self.style.theme_names() else 'clam')

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self._build_ui()
        self._start_services()

    def _build_ui(self):
        header_frame = tk.Frame(self.root, bg="#0d5c96", height=80)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)

        title_lbl = tk.Label(header_frame, text="ReLive Essentials Hub", font=("Segoe UI", 18, "bold"), fg="white", bg="#0d5c96")
        title_lbl.pack(anchor="w", padx=20, pady=(12, 0))

        sub_lbl = tk.Label(header_frame, text="Smart Redirection System: tutto il traffico Live è collegato automaticamente", font=("Segoe UI", 10), fg="#d0e8fc", bg="#0d5c96")
        sub_lbl.pack(anchor="w", padx=20, pady=(2, 0))

        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        status_group = ttk.LabelFrame(main_frame, text=" Stato Connessione Universale ", padding="12")
        status_group.pack(fill=tk.X, pady=(0, 12))

        # Cloud Status
        f_cloud = ttk.Frame(status_group)
        f_cloud.pack(fill=tk.X, pady=3)
        tk.Label(f_cloud, text="●", fg="#107c10", font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(f_cloud, text="Server Cloud ReLive:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        ttk.Label(f_cloud, text=" Connesso (Render - relive-ki2f.onrender.com)", font=("Segoe UI", 9)).pack(side=tk.LEFT)

        # Smart Proxy Status
        f_proxy = ttk.Frame(status_group)
        f_proxy.pack(fill=tk.X, pady=3)
        tk.Label(f_proxy, text="●", fg="#107c10", font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(f_proxy, text="Regola Universale Live:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        ttk.Label(f_proxy, text=" Attiva (100% di *.live.com, *.msn.com e CID reindirizzati)", font=("Segoe UI", 9)).pack(side=tk.LEFT)

        # ARM64 Status
        arch = platform.machine().lower()
        is_arm = "arm" in arch or "aarch" in arch or os.environ.get("PROCESSOR_ARCHITECTURE", "").lower() == "arm64"
        f_arm = ttk.Frame(status_group)
        f_arm.pack(fill=tk.X, pady=3)
        tk.Label(f_arm, text="●", fg="#107c10" if is_arm else "#888888", font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(f_arm, text="Auto-Sblocco ARM64 (0x8521):", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        ttk.Label(f_arm, text=" Attivo in background" if is_arm else " Non necessario (x86/x64 nativo)", font=("Segoe UI", 9)).pack(side=tk.LEFT)

        # Action Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 12))

        btn_launch = tk.Button(btn_frame, text="▶  Avvia Raccolta Foto (Photo Gallery)", font=("Segoe UI", 11, "bold"),
                               bg="#0078d4", fg="white", activebackground="#005a9e", activeforeground="white",
                               relief=tk.FLAT, padx=15, pady=8, cursor="hand2", command=self.launch_photo_gallery)
        btn_launch.pack(fill=tk.X, pady=(0, 8))

        sub_btn_frame = ttk.Frame(btn_frame)
        sub_btn_frame.pack(fill=tk.X)

        btn_mail = ttk.Button(sub_btn_frame, text="✉️ Avvia Windows Live Mail", command=self.launch_mail)
        btn_mail.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))

        btn_portal = ttk.Button(sub_btn_frame, text="🌐 Portale Web", command=self.open_portal)
        btn_portal.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2, 4))

        btn_escargot = ttk.Button(sub_btn_frame, text="💬 Escargot Chat", command=self.open_escargot)
        btn_escargot.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2, 0))

        log_group = ttk.LabelFrame(main_frame, text=" Registro Attività in Tempo Reale ", padding="8")
        log_group.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(log_group, wrap=tk.WORD, font=("Consolas", 8), height=10, bg="#f9f9f9")
        self.log_text.pack(fill=tk.BOTH, expand=True)

        global gui_logger
        gui_logger = self.log

        self.log("[+] ReLive Hub avviato con Smart Redirection.")
        self.log(f"[*] Cloud Upstream: {REMOTE_SERVER}")

    def log(self, text):
        def _append():
            ts = time.strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{ts}] {text}\n")
            self.log_text.see(tk.END)
        self.root.after(0, _append)

    def _start_services(self):
        # 1. Install root cert
        try:
            subprocess.run(["certutil.exe", "-addstore", "-f", "Root", CERT_FILE], capture_output=True)
        except Exception:
            pass

        # 2. Start Smart Proxy on port 8888
        t_proxy = threading.Thread(target=self._run_smart_proxy, daemon=True)
        t_proxy.start()

        # 3. Start local bridges on 80 & 443
        t80 = threading.Thread(target=self._run_port_80, daemon=True)
        t443 = threading.Thread(target=self._run_port_443, daemon=True)
        t80.start()
        t443.start()

        # 4. Activate Windows PAC
        time.sleep(0.3)
        enable_pac_proxy()

        # 5. ARM64 watcher
        arch = platform.machine().lower()
        is_arm = "arm" in arch or "aarch" in arch or os.environ.get("PROCESSOR_ARCHITECTURE", "").lower() == "arm64"
        if is_arm:
            t_arm = threading.Thread(target=arm64_unlock_watcher, daemon=True)
            t_arm.start()
            self.log("[+] Auto-sblocco ARM64 attivo e in monitoraggio.")

    def _run_smart_proxy(self):
        try:
            httpd = ThreadedHTTPServer(('127.0.0.1', 8888), SmartProxyHandler)
            self.log("[+] Smart Proxy attivo su 127.0.0.1:8888 (intercetta tutti i CID e domini *.live.com).")
            httpd.serve_forever()
        except Exception as e:
            self.log(f"[*] Smart Proxy errore: {e}")

    def _run_port_80(self):
        try:
            httpd = ThreadedHTTPServer(('0.0.0.0', 80), ReLiveBridgeHandler)
            self.log("[+] Porta 80 attiva (HTTP Bridge).")
            httpd.serve_forever()
        except Exception as e:
            self.log(f"[*] Porta 80 non disponibile: {e}")

    def _run_port_443(self):
        try:
            httpd = ThreadedHTTPServer(('0.0.0.0', 443), ReLiveBridgeHandler)
            ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ctx.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
            httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
            self.log("[+] Porta 443 attiva (HTTPS Bridge SSL).")
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

    def open_escargot(self):
        webbrowser.open("https://escargot.chat")

    def on_close(self):
        disable_pac_proxy()
        self.root.destroy()

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
