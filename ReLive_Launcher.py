import os
import sys
import ssl
import time
import ctypes
import platform
import subprocess
import threading
import tempfile
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

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

# Ensure cert files exist
CERT_DIR = os.path.join(tempfile.gettempdir(), "ReLive_Certs")
os.makedirs(CERT_DIR, exist_ok=True)
CERT_FILE = os.path.join(CERT_DIR, "live_revival.crt")
KEY_FILE = os.path.join(CERT_DIR, "live_revival.key")

with open(CERT_FILE, "w", encoding="utf-8") as f:
    f.write(EMBEDDED_CRT.strip() + "\n")

with open(KEY_FILE, "w", encoding="utf-8") as f:
    f.write(EMBEDDED_KEY.strip() + "\n")

# -------------------------------------------------------------------
# 1. Reverse Proxy / Bridge to Render Cloud
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
        except urllib.error.HTTPError as e:
            err_data = e.read()
            self.send_response(e.code)
            for h_name, h_val in e.headers.items():
                if h_name.lower() not in ('transfer-encoding', 'content-encoding', 'connection'):
                    self.send_header(h_name, h_val)
            self.send_header('Content-Length', str(len(err_data)))
            self.end_headers()
            self.wfile.write(err_data)
        except Exception:
            self.send_response(502)
            msg = b"ReLive Cloud Connection Error"
            self.send_header('Content-Length', str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)

    do_GET = do_ANY
    do_POST = do_ANY
    do_PUT = do_ANY
    do_DELETE = do_ANY
    do_HEAD = do_ANY
    do_OPTIONS = do_ANY

    def log_message(self, format, *args):
        pass

def run_http_server():
    try:
        httpd = ThreadedHTTPServer(('0.0.0.0', 80), ReLiveBridgeHandler)
        httpd.serve_forever()
    except Exception as e:
        print(f"[*] Porta 80 non disponibile o gia' in ascolto: {e}")

def run_https_server():
    try:
        httpd = ThreadedHTTPServer(('0.0.0.0', 443), ReLiveBridgeHandler)
        ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ctx.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
        httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
        httpd.serve_forever()
    except Exception as e:
        print(f"[*] Porta 443 non disponibile o gia' in ascolto: {e}")

# -------------------------------------------------------------------
# 2. ARM64 Auto-Unlocker Thread (Signal 0x8521)
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
    
    start_time = time.time()
    while time.time() - start_time < 300:
        user32.EnumWindows(cb_func, 0)
        time.sleep(1)

# -------------------------------------------------------------------
# 3. Environment Self-Check (Hosts & SSL Certificate)
# -------------------------------------------------------------------
def configure_environment():
    hosts_path = os.path.expandvars(r"%windir%\System32\drivers\etc\hosts")
    domains = [
        "login.live.com", "nexus.passport.com", "spaces.live.com",
        "byrdr.livefilestore.com", "storage.live.com", "storage.msn.com",
        "contacts.msn.com", "directory.services.live.com"
    ]
    try:
        with open(hosts_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        
        missing = [d for d in domains if d not in content]
        if missing:
            with open(hosts_path, "a", encoding="utf-8") as f:
                f.write("\n# ReLive Windows Live Revival\n")
                for d in missing:
                    f.write(f"127.0.0.1 {d}\n")
            subprocess.run(["ipconfig", "/flushdns"], capture_output=True)
    except Exception:
        pass

    try:
        subprocess.run(["certutil.exe", "-addstore", "-f", "Root", CERT_FILE], capture_output=True)
    except Exception:
        pass

# -------------------------------------------------------------------
# 4. Main Entrypoint
# -------------------------------------------------------------------
def main():
    print("=================================================================")
    print("           RELIVE LAUNCHER — WINDOWS LIVE ESSENTIALS             ")
    print("=================================================================")
    print(f"[*] Cloud Revival Server: {REMOTE_SERVER}")
    print("[*] Inizializzazione connettore di sicurezza...")

    configure_environment()

    # Start bridges
    t80 = threading.Thread(target=run_http_server, daemon=True)
    t443 = threading.Thread(target=run_https_server, daemon=True)
    t80.start()
    t443.start()

    time.sleep(0.5)
    print("[+] Connettore Cloud attivo su porte 80 e 443!")

    # Start ARM64 watcher
    arch = platform.machine().lower()
    is_arm = "arm" in arch or "aarch" in arch or os.environ.get("PROCESSOR_ARCHITECTURE", "").lower() == "arm64"
    if is_arm:
        print("[*] Architettura ARM64 rilevata: modulo auto-sblocco 0x8521 attivato!")
        t_arm = threading.Thread(target=arm64_unlock_watcher, daemon=True)
        t_arm.start()

    # Launch WLXPhotoGallery if installed
    pg_path = r"C:\Program Files (x86)\Windows Live\Photo Gallery\WLXPhotoGallery.exe"
    if os.path.exists(pg_path):
        print("[+] Avvio di Windows Live Raccolta Foto...")
        subprocess.Popen([pg_path])
    else:
        print(f"[*] Raccolta Foto non rilevata nel percorso standard: {pg_path}")

    print("\n[+] ReLive e' pronto e attivo. Goditi Windows Live Essentials!")
    print("[*] Tieni questa finestra aperta durante l'utilizzo.")
    print("    (Premi Ctrl+C per uscire al termine della sessione)\n")

    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("Chiusura ReLive Launcher.")

if __name__ == "__main__":
    main()
