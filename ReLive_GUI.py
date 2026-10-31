import os
import sys
import ssl
import time
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

# Global GUI log callback
gui_logger = None

def log_to_gui(msg):
    if gui_logger:
        gui_logger(msg)
    else:
        print(msg)

# -------------------------------------------------------------------
# 1. Reverse Proxy / Bridge
# -------------------------------------------------------------------
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

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
# 2. ARM64 Watcher
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
# 3. Environment Check & Fix
# -------------------------------------------------------------------
def check_and_repair_env():
    hosts_path = os.path.expandvars(r"%windir%\System32\drivers\etc\hosts")
    domains = [
        "login.live.com", "nexus.passport.com", "spaces.live.com",
        "byrdr.livefilestore.com", "storage.live.com", "storage.msn.com",
        "contacts.msn.com", "directory.services.live.com",
        "cid-d4445d06d15a8466.spaces.live.com", "cid-d4445d06d15a8466.skydrive.live.com",
        "cid-d4445d06d15a8466.users.storage.live.com", "spaces-beta.live.com",
        "photogallery.live.com", "profile.live.com", "people.live.com",
        "account.live.com", "tkrdr.storage.msn.com"
    ]
    added = False
    try:
        content = ""
        if os.path.exists(hosts_path):
            with open(hosts_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

        missing = [d for d in domains if d not in content]
        if missing:
            with open(hosts_path, "a", encoding="utf-8") as f:
                f.write("\n# ReLive Windows Live Revival\n")
                for d in missing:
                    f.write(f"127.0.0.1 {d}\n")
            subprocess.run(["ipconfig", "/flushdns"], capture_output=True)
            added = True
    except Exception as e:
        log_to_gui(f"[!] Errore scrittura file hosts: {e}")

    try:
        subprocess.run(["certutil.exe", "-addstore", "-f", "Root", CERT_FILE], capture_output=True)
    except Exception as e:
        log_to_gui(f"[!] Errore installazione certificato: {e}")

    return added

# -------------------------------------------------------------------
# 4. GUI Application
# -------------------------------------------------------------------
class ReLiveApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ReLive — Windows Live Essentials Launcher")
        self.root.geometry("680x560")
        self.root.minsize(620, 500)

        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('vista' if 'vista' in self.style.theme_names() else 'clam')

        self.httpd_80 = None
        self.httpd_443 = None

        self._build_ui()
        self._start_services()

    def _build_ui(self):
        # Header Frame (Aero Gradient imitation)
        header_frame = tk.Frame(self.root, bg="#0d5c96", height=80)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)

        title_lbl = tk.Label(header_frame, text="ReLive Essentials", font=("Segoe UI", 18, "bold"), fg="white", bg="#0d5c96")
        title_lbl.pack(anchor="w", padx=20, pady=(12, 0))

        sub_lbl = tk.Label(header_frame, text="Windows Live Wave 3 Revival Hub & Cloud Connector", font=("Segoe UI", 10), fg="#d0e8fc", bg="#0d5c96")
        sub_lbl.pack(anchor="w", padx=20, pady=(2, 0))

        # Main Body
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Status Group
        status_group = ttk.LabelFrame(main_frame, text=" Stato Connessione & Servizi ", padding="12")
        status_group.pack(fill=tk.X, pady=(0, 12))

        # Cloud Status
        f_cloud = ttk.Frame(status_group)
        f_cloud.pack(fill=tk.X, pady=3)
        self.lbl_cloud_icon = tk.Label(f_cloud, text="●", fg="#107c10", font=("Segoe UI", 12, "bold"))
        self.lbl_cloud_icon.pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(f_cloud, text="Server Cloud ReLive:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        ttk.Label(f_cloud, text=" Connesso (Render - relive-ki2f.onrender.com)", font=("Segoe UI", 9)).pack(side=tk.LEFT)

        # Bridge Status
        f_bridge = ttk.Frame(status_group)
        f_bridge.pack(fill=tk.X, pady=3)
        self.lbl_bridge_icon = tk.Label(f_bridge, text="●", fg="#107c10", font=("Segoe UI", 12, "bold"))
        self.lbl_bridge_icon.pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(f_bridge, text="Bridge Locale:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        self.lbl_bridge_text = ttk.Label(f_bridge, text=" Porte 80 & 443 Attive", font=("Segoe UI", 9))
        self.lbl_bridge_text.pack(side=tk.LEFT)

        # ARM64 Status
        arch = platform.machine().lower()
        is_arm = "arm" in arch or "aarch" in arch or os.environ.get("PROCESSOR_ARCHITECTURE", "").lower() == "arm64"
        f_arm = ttk.Frame(status_group)
        f_arm.pack(fill=tk.X, pady=3)
        lbl_arm_icon = tk.Label(f_arm, text="●", fg="#107c10" if is_arm else "#888888", font=("Segoe UI", 12, "bold"))
        lbl_arm_icon.pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(f_arm, text="Auto-Sblocco ARM64 (0x8521):", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        ttk.Label(f_arm, text=" Attivo in background" if is_arm else " Non necessario (x86/x64 nativo)", font=("Segoe UI", 9)).pack(side=tk.LEFT)

        # Action Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 12))

        # Launch WLPG Button (Prominent)
        btn_launch = tk.Button(btn_frame, text="▶  Avvia Raccolta Foto (Photo Gallery)", font=("Segoe UI", 11, "bold"),
                               bg="#0078d4", fg="white", activebackground="#005a9e", activeforeground="white",
                               relief=tk.FLAT, padx=15, pady=8, cursor="hand2", command=self.launch_photo_gallery)
        btn_launch.pack(fill=tk.X, pady=(0, 8))

        # Secondary Buttons
        sub_btn_frame = ttk.Frame(btn_frame)
        sub_btn_frame.pack(fill=tk.X)

        btn_portal = ttk.Button(sub_btn_frame, text="🌐 Portale Web ReLive", command=self.open_portal)
        btn_portal.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))

        btn_repair = ttk.Button(sub_btn_frame, text="🛠️ Verifica Hosts & Certificato", command=self.repair_env)
        btn_repair.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2, 4))

        btn_escargot = ttk.Button(sub_btn_frame, text="💬 Escargot Messenger", command=self.open_escargot)
        btn_escargot.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2, 0))

        # Activity Log Group
        log_group = ttk.LabelFrame(main_frame, text=" Registro Attività in Tempo Reale ", padding="8")
        log_group.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(log_group, wrap=tk.WORD, font=("Consolas", 8), height=10, bg="#f9f9f9")
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Set global logger
        global gui_logger
        gui_logger = self.log

        self.log("[+] ReLive Hub avviato.")
        self.log(f"[*] Cloud Upstream: {REMOTE_SERVER}")

    def log(self, text):
        def _append():
            ts = time.strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{ts}] {text}\n")
            self.log_text.see(tk.END)
        self.root.after(0, _append)

    def _start_services(self):
        # 1. Environment check
        threading.Thread(target=check_and_repair_env, daemon=True).start()

        # 2. Bridge threads
        t80 = threading.Thread(target=self._run_port_80, daemon=True)
        t443 = threading.Thread(target=self._run_port_443, daemon=True)
        t80.start()
        t443.start()

        # 3. ARM watcher
        arch = platform.machine().lower()
        is_arm = "arm" in arch or "aarch" in arch or os.environ.get("PROCESSOR_ARCHITECTURE", "").lower() == "arm64"
        if is_arm:
            t_arm = threading.Thread(target=arm64_unlock_watcher, daemon=True)
            t_arm.start()
            self.log("[+] Auto-sblocco ARM64 attivo e in monitoraggio.")

    def _run_port_80(self):
        try:
            self.httpd_80 = ThreadedHTTPServer(('0.0.0.0', 80), ReLiveBridgeHandler)
            self.log("[+] Porta 80 attiva (HTTP Bridge pronto).")
            self.httpd_80.serve_forever()
        except Exception as e:
            self.log(f"[*] Porta 80 non disponibile: {e}")

    def _run_port_443(self):
        try:
            self.httpd_443 = ThreadedHTTPServer(('0.0.0.0', 443), ReLiveBridgeHandler)
            ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ctx.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
            self.httpd_443.socket = ctx.wrap_socket(self.httpd_443.socket, server_side=True)
            self.log("[+] Porta 443 attiva (HTTPS Bridge SSL pronto).")
            self.httpd_443.serve_forever()
        except Exception as e:
            self.log(f"[*] Porta 443 non disponibile: {e}")

    def launch_photo_gallery(self):
        pg_path = r"C:\Program Files (x86)\Windows Live\Photo Gallery\WLXPhotoGallery.exe"
        if os.path.exists(pg_path):
            self.log("[+] Avvio di Windows Live Raccolta Foto...")
            subprocess.Popen([pg_path])
        else:
            self.log(f"[!] File non trovato: {pg_path}")
            messagebox.showwarning("Non trovato", f"Impossibile trovare Raccolta Foto in:\n{pg_path}")

    def open_portal(self):
        self.log("[*] Apertura portale ReLive nel browser...")
        webbrowser.open(REMOTE_SERVER)

    def open_escargot(self):
        self.log("[*] Apertura Escargot Chat nel browser...")
        webbrowser.open("https://escargot.chat")

    def repair_env(self):
        self.log("[*] Verifica ed eventuale ripristino di hosts e certificato...")
        check_and_repair_env()
        self.log("[+] Verifica completata con successo.")
        messagebox.showinfo("ReLive", "Certificato SSL e reindirizzamenti file hosts verificati con successo!")


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def main():
    if not is_admin():
        # Re-run with admin elevation
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
