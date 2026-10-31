import asyncio
import logging
import os
import uvicorn
from app.config import HOST, PORT, BASE_DIR
from app.mail.imap_server import start_imap_server
from app.mail.smtp_server import start_smtp_server
from app.main import app

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("revival")

async def main():
    print("=" * 65)
    print("   WINDOWS LIVE REVIVAL SERVER (Wave 3 / Wave 4)")
    print("   Suite completa: SkyDrive, Raccolta Foto, Mail & Live ID")
    print("=" * 65)
    print(f"[*] SkyDrive & Portale Web:   http://localhost:{PORT}")
    print(f"[*] Windows Live Mail (IMAP): porta 143 (localhost)")
    print(f"[*] Windows Live Mail (SMTP): porta 587 (localhost)")
    print(f"[*] Windows Live ID (HTTP):   porta 80  (localhost)")
    print(f"[*] Windows Live ID (HTTPS):  porta 443 (localhost)")
    print("=" * 65)

    # Start IMAP server for Windows Live Mail
    imap_server = await start_imap_server(host="0.0.0.0", port=143)

    # Start SMTP server for Windows Live Mail
    smtp_server = await start_smtp_server(host="0.0.0.0", port=587)

    # Primary web server (port 8080)
    config_8080 = uvicorn.Config(app=app, host="0.0.0.0", port=PORT, log_level="info")
    server_8080 = uvicorn.Server(config_8080)

    servers = [
        imap_server.serve_forever(),
        smtp_server.serve_forever(),
        server_8080.serve()
    ]

    # HTTP server on standard port 80 (for Nexus discovery & redirects)
    try:
        config_80 = uvicorn.Config(app=app, host="0.0.0.0", port=80, log_level="info")
        server_80 = uvicorn.Server(config_80)
        servers.append(server_80.serve())
        logger.info("Server HTTP Live ID avviato sulla porta 80")
    except Exception as e:
        logger.warning(f"Impossibile avviare la porta 80: {e}")

    # HTTPS server on standard port 443 (for WS-Trust RST.srf Live ID login)
    cert_file = BASE_DIR / "certs" / "leaf_bundle.crt"
    key_file = BASE_DIR / "certs" / "leaf_server.key"
    if not (cert_file.exists() and key_file.exists()):
        cert_file = BASE_DIR / "certs" / "live_revival.crt"
        key_file = BASE_DIR / "certs" / "live_revival.key"
    if cert_file.exists() and key_file.exists():
        try:
            config_443 = uvicorn.Config(
                app=app,
                host="0.0.0.0",
                port=443,
                ssl_keyfile=str(key_file),
                ssl_certfile=str(cert_file),
                log_level="info"
            )
            server_443 = uvicorn.Server(config_443)
            servers.append(server_443.serve())
            logger.info("Server HTTPS Live ID (SSL) avviato sulla porta 443")
        except Exception as e:
            logger.warning(f"Impossibile avviare la porta 443 HTTPS: {e}")
    else:
        logger.warning("Certificati SSL non trovati in certs/, HTTPS disabilitato.")

    # Run all servers concurrently
    await asyncio.gather(*servers)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nArresto del server completato.")
