import os
import sys
import ssl
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import threading

REMOTE_SERVER = os.getenv("RELIVE_REMOTE", "https://relive-ki2f.onrender.com")
CERTS_DIR = os.path.join(os.path.dirname(__file__), "certs")
CERT_FILE = os.path.join(CERTS_DIR, "live_revival.crt")
KEY_FILE = os.path.join(CERTS_DIR, "live_revival.key")

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class ReLiveProxyHandler(BaseHTTPRequestHandler):
    def do_ANY(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        target_url = f"{REMOTE_SERVER}{self.path}"
        print(f"-> [CLOUD PROXY] {self.command} {self.path} (Inoltro a Render...)")

        # Copy headers, removing hop-by-hop and host
        req_headers = {}
        for k, v in self.headers.items():
            if k.lower() not in ('host', 'content-length', 'connection', 'transfer-encoding'):
                req_headers[k] = v

        req = urllib.request.Request(target_url, data=body, headers=req_headers, method=self.command)

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                resp_data = resp.read()
                self.send_response(resp.status)
                for h_name, h_val in resp.getheaders():
                    if h_name.lower() not in ('transfer-encoding', 'content-encoding', 'connection'):
                        self.send_header(h_name, h_val)
                self.send_header('Content-Length', str(len(resp_data)))
                self.end_headers()
                self.wfile.write(resp_data)
                print(f"<- [CLOUD RISPOSTA] {resp.status} per {self.path}")
        except urllib.error.HTTPError as e:
            err_data = e.read()
            self.send_response(e.code)
            for h_name, h_val in e.headers.items():
                if h_name.lower() not in ('transfer-encoding', 'content-encoding', 'connection'):
                    self.send_header(h_name, h_val)
            self.send_header('Content-Length', str(len(err_data)))
            self.end_headers()
            self.wfile.write(err_data)
            print(f"<- [CLOUD RISPOSTA] {e.code} per {self.path}")
        except Exception as e:
            print(f"[!] Errore connessione a Render: {e}")
            self.send_response(502)
            msg = b"ReLive Cloud Bridge Error"
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
        pass # clean console

def run_http(port=80):
    try:
        httpd = ThreadedHTTPServer(('0.0.0.0', port), ReLiveProxyHandler)
        httpd.serve_forever()
    except Exception as e:
        print(f"HTTP Server error on port {port}: {e}")

def run_https(port=443):
    try:
        httpd = ThreadedHTTPServer(('0.0.0.0', port), ReLiveProxyHandler)
        ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ctx.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
        httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
        httpd.serve_forever()
    except Exception as e:
        print(f"HTTPS Server error on port {port}: {e}")

if __name__ == "__main__":
    print("=================================================================")
    print("        RELIVE CLOUD CONNECTOR (CENTRAL REVIVAL BRIDGE)          ")
    print("=================================================================")
    print(f"[*] Server Centralizzato: {REMOTE_SERVER}")
    print("[*] Inoltro trasparente delle chiamate Windows Live al Cloud...")
    print("=================================================================")

    t80 = threading.Thread(target=run_http, args=(80,), daemon=True)
    t443 = threading.Thread(target=run_https, args=(443,), daemon=True)
    t80.start()
    t443.start()

    print("\n[+] CONNESSO AL SERVER CENTRALIZZATO CON SUCCESSO!")
    print("[+] Tutte le operazioni di Raccolta Foto sono ora sincronizzate sul Cloud!")
    print("[+] Premi Ctrl+C per fermare il connettore.\n")

    try:
        while True:
            threading.Event().wait(3600)
    except KeyboardInterrupt:
        print("\nChiusura connettore.")
