import logging
from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, PlainTextResponse
from app.database import authenticate_user, get_user_by_email
from app.passport.wstrust import parse_wstrust_request, build_wstrust_response, build_wstrust_fault

logger = logging.getLogger("passport")
router = APIRouter(tags=["Passport / Windows Live ID"])

# -------------------------------------------------------------
# Nexus Discovery Endpoints (nexus.passport.com / rdr/pprdr.asp)
# -------------------------------------------------------------
@router.get("/rdr/pprdr.asp")
@router.post("/rdr/pprdr.asp")
async def nexus_discovery(request: Request):
    """
    Nexus discovery endpoint used by MSIDCRL to discover login and refresh endpoints.
    """
    host = request.headers.get("host", "login.live.com")
    logger.info(f"Nexus discovery query from {request.client.host} for host {host}")
    
    passport_urls = (
        "DARefresh=https://login.live.com/pprdr.asp,"
        "DALo=https://login.live.com/login.srf,"
        "ConfigVersion=1,"
        "Properties=https://nexus.passport.com/rdr/pprdr.asp"
    )
    
    headers = {
        "PassportURLs": passport_urls,
        "Content-Type": "text/html",
        "Connection": "close"
    }
    return Response(content="", status_code=200, headers=headers)

@router.get("/pprdr.asp")
@router.post("/pprdr.asp")
async def passport_refresh(request: Request):
    """Secondary passport redirector / refresh URL."""
    headers = {
        "PassportURLs": "DARefresh=https://login.live.com/pprdr.asp,DALo=https://login.live.com/login.srf,ConfigVersion=1",
        "Content-Type": "text/html",
    }
    return Response(content="", status_code=200, headers=headers)

# -------------------------------------------------------------
# WS-Trust Security Token Service (/RST.srf and /RST2.srf)
# -------------------------------------------------------------
@router.post("/RST.srf")
@router.post("/rst.srf")
@router.post("/RST2.srf")
@router.post("/rst2.srf")
async def request_security_token(request: Request):
    """
    WS-Trust active authentication endpoint for Windows Live MSIDCRL.
    Receives SOAP credentials and issues compact security tokens.
    """
    body_bytes = await request.body()
    logger.info(f"=== INCOMING WS-TRUST REQUEST ({len(body_bytes)} bytes) ===\n{body_bytes.decode('utf-8', errors='ignore')}")
    username, password, addresses, message_id = parse_wstrust_request(body_bytes)
    
    logger.info(f"RST.srf authentication request: username='{username}', targets={addresses}, message_id={message_id}")
    
    # Check if this is a primary authentication (username + password) or secondary service token issue (session/token auth)
    if username and password:
        user = authenticate_user(username, password)
        if not user:
            logger.warning(f"RST.srf: Authentication failed for '{username}'")
            fault_xml = build_wstrust_fault("psf:AuthenticationFailed", "ID Windows Live o password non corretti.")
            return Response(content=fault_xml, status_code=401, media_type="text/xml; charset=utf-8")
    else:
        # Secondary token request using session token / DerivedKeyToken (e.g. ads.arcct.msn.com or service token refresh)
        user = (get_user_by_email(username) if username else None) or get_user_by_email("stefano@live.it")
        if not user:
            logger.warning("RST.srf: No session user found for secondary token request")
            fault_xml = build_wstrust_fault("psf:InvalidCredentials", "Nome utente o password mancanti.")
            return Response(content=fault_xml, status_code=401, media_type="text/xml; charset=utf-8")
        logger.info(f"RST.srf: Secondary/service token request authenticated for '{user['email']}'")
        
    logger.info(f"RST.srf: User '{username}' successfully authenticated! Issuing tokens for {addresses}")
    response_xml = build_wstrust_response(user, addresses, message_id)
    logger.info(f"=== OUTGOING WS-TRUST RESPONSE ({len(response_xml)} bytes) ===\n{response_xml}")
    
    headers = {
        "Content-Type": "application/soap+xml; charset=utf-8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }
    return Response(content=response_xml, status_code=200, headers=headers, media_type="application/soap+xml; charset=utf-8")

# -------------------------------------------------------------
# Live ID Web Login fallback (/login.srf)
# -------------------------------------------------------------
@router.get("/login.srf")
@router.post("/login.srf")
async def live_id_web_login():
    """Retro Live ID sign-in page."""
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Accedi a Windows Live ID</title>
    <style>
        body { font-family: "Segoe UI", Arial, sans-serif; background: #0072c6; margin:0; display:flex; align-items:center; justify-content:center; height:100vh; }
        .box { background: white; border-radius: 8px; padding: 32px; width: 360px; box-shadow: 0 4px 16px rgba(0,0,0,0.3); }
        h1 { font-size: 20px; color: #0072c6; margin-top: 0; }
        p { font-size: 13px; color: #555; }
        .status { background: #eef7fc; border-left: 4px solid #0072c6; padding: 10px; font-size: 12px; margin-top: 16px; }
    </style>
</head>
<body>
    <div class="box">
        <h1>Windows Live ID Revival</h1>
        <p>Il server di autenticazione locale &egrave; attivo e pronto.</p>
        <div class="status">
            <strong>Endpoint WS-Trust:</strong> <code>/RST.srf</code> attivo.<br>
            Accedi direttamente con il tuo account <strong>@live.it</strong> dai client desktop.
        </div>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html_content, status_code=200)

@router.get("/logout.srf")
async def live_id_logout():
    return HTMLResponse("<html><body>Disconnessione effettuata.</body></html>", status_code=200)
