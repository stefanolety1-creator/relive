import re
import datetime
import hashlib
import base64
from typing import List, Dict, Optional, Tuple

def get_user_cid(email: str) -> str:
    """Generate a consistent 16-character hex CID for the user."""
    h = hashlib.sha256(email.lower().strip().encode('utf-8')).hexdigest()
    return h[:16].upper()

def get_user_puid(email: str) -> str:
    """Generate a consistent 64-bit PUID string."""
    cid = get_user_cid(email)
    return str(int(cid, 16))

def parse_wstrust_request(xml_bytes: bytes) -> Tuple[Optional[str], Optional[str], List[Dict], Optional[str]]:
    """
    Parses a WS-Trust SOAP request XML payload.
    Extracts:
      - username
      - password
      - list of target requests (each with id/context and address)
      - message_id
    """
    text = xml_bytes.decode('utf-8', errors='ignore')
    
    # Extract Username & Password
    user_match = re.search(r'<(?:[a-zA-Z0-9_\-]+:)?Username[^>]*>([^<]+)</(?:[a-zA-Z0-9_\-]+:)?Username>', text)
    pass_match = re.search(r'<(?:[a-zA-Z0-9_\-]+:)?Password[^>]*>([^<]+)</(?:[a-zA-Z0-9_\-]+:)?Password>', text)
    
    username = user_match.group(1).strip() if user_match else None
    password = pass_match.group(1).strip() if pass_match else None

    # Extract MessageID for WS-Addressing RelatesTo header
    msg_m = re.search(r'<(?:[a-zA-Z0-9_\-]+:)?MessageID[^>]*>([^<]+)</(?:[a-zA-Z0-9_\-]+:)?MessageID>', text)
    message_id = msg_m.group(1).strip() if msg_m else None

    # Parse individual RequestSecurityToken blocks if present
    rst_blocks = re.findall(r'<(?:\w+:)?RequestSecurityToken\b([^>]*)>(.*?)</(?:\w+:)?RequestSecurityToken>', text, re.DOTALL)
    
    targets = []
    if rst_blocks:
        for attrs, content in rst_blocks:
            # Extract Id or Context attribute
            id_m = re.search(r'\b(?:Id|Context)=["\']([^"\']+)["\']', attrs)
            token_id = id_m.group(1) if id_m else None
            
            # Extract Address
            addr_m = re.search(r'<(?:[a-zA-Z0-9_\-]+:)?Address[^>]*>([^<]+)</(?:[a-zA-Z0-9_\-]+:)?Address>', content)
            addr = addr_m.group(1).strip() if addr_m else "http://Passport.NET/tb"
            targets.append({"id": token_id, "address": addr})
    else:
        # Fallback to searching all addresses
        addresses = re.findall(r'<(?:[a-zA-Z0-9_\-]+:)?Address[^>]*>([^<]+)</(?:[a-zA-Z0-9_\-]+:)?Address>', text)
        if not addresses:
            addresses = ["http://Passport.NET/tb"]
        for idx, addr in enumerate(addresses):
            targets.append({"id": f"RST{idx}", "address": addr})

    return username, password, targets, message_id

def build_wstrust_response(user: Dict, targets: List[Dict], message_id: Optional[str] = None) -> str:
    """
    Builds a WS-Trust 1.3 / SOAP 1.2 RequestSecurityTokenResponseCollection
    perfectly matching MSIDCRL 4.0 / 5.0 XPath and WS-Addressing expectations.
    """
    email = user['email']
    display_name = user.get('display_name') or email.split('@')[0]
    cid = get_user_cid(email)
    puid = get_user_puid(email)

    name_parts = display_name.split(None, 1)
    first_name = user.get('first_name') or (name_parts[0] if name_parts else display_name)
    last_name = user.get('last_name') or (name_parts[1] if len(name_parts) > 1 else ("De Luca" if "stefano" in email.lower() else "User"))
    gender = user.get('gender') or "m"
    birth_date = user.get('birth_date') or "1995-01-01"
    country = user.get('country') or "IT"
    
    now = datetime.datetime.now(datetime.timezone.utc)
    expires = now + datetime.timedelta(days=14)
    
    created_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    expires_iso = expires.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    token_responses = []
    
    for i, tgt in enumerate(targets, start=1):
        context_id = tgt.get("id") or f"RST{i-1}"
        addr = tgt.get("address") or "http://Passport.NET/tb"
        
        # Binary secret (session key) in base64
        binary_secret = base64.b64encode(hashlib.sha256(f"{cid}_{i}".encode()).digest()).decode()
        
        # Token and p-token values
        token_val = f"wl_{cid}_{i}_{int(now.timestamp())}"
        p_val = f"wl_p_{cid}_{i}"
        
        compact_ticket = f"t={token_val}&amp;p={p_val}&amp;cid={cid}&amp;da=1&amp;ct={int(now.timestamp())}&amp;bver=5"
        
        resp_xml = f"""
        <wst:RequestSecurityTokenResponse Context="{context_id}">
            <wst:TokenType>urn:passport:compact</wst:TokenType>
            <wsp:AppliesTo xmlns:wsp="http://schemas.xmlsoap.org/ws/2004/09/policy">
                <wsa:EndpointReference xmlns:wsa="http://www.w3.org/2005/08/addressing">
                    <wsa:Address>{addr}</wsa:Address>
                </wsa:EndpointReference>
            </wsp:AppliesTo>
            <wst:Lifetime xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
                <wsu:Created>{created_iso}</wsu:Created>
                <wsu:Expires>{expires_iso}</wsu:Expires>
            </wst:Lifetime>
            <wst:RequestedSecurityToken>
                <wsse:BinarySecurityToken xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd" Id="Compact{i}">
                    {compact_ticket}
                </wsse:BinarySecurityToken>
            </wst:RequestedSecurityToken>
            <wst:RequestedProofToken>
                <wst:BinarySecret>{binary_secret}</wst:BinarySecret>
            </wst:RequestedProofToken>
            <wst:RequestedAttachedReference>
                <wsse:SecurityTokenReference xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
                    <wsse:Reference URI="#Compact{i}"/>
                </wsse:SecurityTokenReference>
            </wst:RequestedAttachedReference>
            <wst:RequestedUnattachedReference>
                <wsse:SecurityTokenReference xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
                    <wsse:Reference URI="#Compact{i}"/>
                </wsse:SecurityTokenReference>
            </wst:RequestedUnattachedReference>
            <psf:pp>
                <psf:authstate>0x48803</psf:authstate>
                <psf:reqstatus>0x0</psf:reqstatus>
                <psf:errorstatus>0x0</psf:errorstatus>
                <psf:authreq>0x0</psf:authreq>
            </psf:pp>
            <ps:pp xmlns:ps="http://schemas.microsoft.com/Passport/SoapServices/PPCRL">
                <ps:serverData>token={token_val}</ps:serverData>
                <ps:responseProperties>
                    <ps:CID>{cid}</ps:CID>
                    <ps:cid>{cid.lower()}</ps:cid>
                    <ps:EmailStatus>1</ps:EmailStatus>
                    <ps:PassportCID>{cid}</ps:PassportCID>
                    <ps:PUID>{puid}</ps:PUID>
                    <ps:MemberName>{email}</ps:MemberName>
                    <ps:AuthMemberName>{email}</ps:AuthMemberName>
                    <ps:DisplayName>{display_name}</ps:DisplayName>
                    <ps:FirstName>{first_name}</ps:FirstName>
                    <ps:LastName>{last_name}</ps:LastName>
                    <ps:NickName>{first_name}</ps:NickName>
                    <ps:Nickname>{first_name}</ps:Nickname>
                    <ps:Gender>{gender}</ps:Gender>
                    <ps:BirthDate>{birth_date}</ps:BirthDate>
                    <ps:Birthdate>{birth_date}</ps:Birthdate>
                    <ps:Country>{country}</ps:Country>
                    <ps:City>Roma</ps:City>
                    <ps:State>RM</ps:State>
                    <ps:PostalCode>00100</ps:PostalCode>
                    <ps:Phone>+393331234567</ps:Phone>
                    <ps:PhoneNumber>+393331234567</ps:PhoneNumber>
                    <ps:MobilePhone>+393331234567</ps:MobilePhone>
                    <ps:TimeZone>1</ps:TimeZone>
                    <ps:Timezone>1</ps:Timezone>
                    <ps:AgeStatus>1</ps:AgeStatus>
                    <ps:HasParent>0</ps:HasParent>
                    <ps:Consent>1</ps:Consent>
                    <ps:LangPreference>1040</ps:LangPreference>
                    <ps:Flags>40100643</ps:Flags>
                    <ps:FlagsV2>00000000</ps:FlagsV2>
                    <ps:ChildFlags>00000001</ps:ChildFlags>
                    <ps:MainBrandID>MSFT</ps:MainBrandID>
                    <ps:IsWinLiveUser>true</ps:IsWinLiveUser>
                    <ps:AssociatedForStrongAuth>0</ps:AssociatedForStrongAuth>
                    <ps:FederationBrandName>Windows Live</ps:FederationBrandName>
                </ps:responseProperties>
            </ps:pp>
        </wst:RequestSecurityTokenResponse>
        """
        token_responses.append(resp_xml)
        
    all_responses = "\n".join(token_responses)
    
    relates_to = f"<wsa:RelatesTo>{message_id}</wsa:RelatesTo>" if message_id else ""
    header_block = f"""
    <S:Header>
        <wsa:Action S:mustUnderstand="1">http://schemas.xmlsoap.org/ws/2005/02/trust/RSTR/Issue</wsa:Action>
        {relates_to}
        <wsse:Security>
            <wsu:Timestamp Id="Timestamp">
                <wsu:Created>{created_iso}</wsu:Created>
                <wsu:Expires>{expires_iso}</wsu:Expires>
            </wsu:Timestamp>
        </wsse:Security>
        <psf:pp>
            <psf:serverVersion>1</psf:serverVersion>
            <psf:uiVersion>1</psf:uiVersion>
            <psf:configVersion>1</psf:configVersion>
            <psf:authstate>0x48803</psf:authstate>
            <psf:reqstatus>0x0</psf:reqstatus>
            <psf:errorstatus>0x0</psf:errorstatus>
            <psf:authreq>0x0</psf:authreq>
            <psf:serverInfo ServerTime="{created_iso}"/>
            <psf:PUID>{puid}</psf:PUID>
            <psf:credProperties>
                <psf:credProperty Name="EmailStatus">1</psf:credProperty>
                <psf:credProperty Name="PassportCID">{cid}</psf:credProperty>
                <psf:credProperty Name="CID">{cid.lower()}</psf:credProperty>
                <psf:credProperty Name="MemberName">{email}</psf:credProperty>
                <psf:credProperty Name="AuthMemberName">{email}</psf:credProperty>
                <psf:credProperty Name="DisplayName">{display_name}</psf:credProperty>
                <psf:credProperty Name="FirstName">{first_name}</psf:credProperty>
                <psf:credProperty Name="LastName">{last_name}</psf:credProperty>
                <psf:credProperty Name="NickName">{first_name}</psf:credProperty>
                <psf:credProperty Name="Nickname">{first_name}</psf:credProperty>
                <psf:credProperty Name="Gender">m</psf:credProperty>
                <psf:credProperty Name="BirthDate">1995-01-01</psf:credProperty>
                <psf:credProperty Name="Birthdate">1995-01-01</psf:credProperty>
                <psf:credProperty Name="Country">IT</psf:credProperty>
                <psf:credProperty Name="City">Roma</psf:credProperty>
                <psf:credProperty Name="State">RM</psf:credProperty>
                <psf:credProperty Name="PostalCode">00100</psf:credProperty>
                <psf:credProperty Name="Phone">+393331234567</psf:credProperty>
                <psf:credProperty Name="PhoneNumber">+393331234567</psf:credProperty>
                <psf:credProperty Name="MobilePhone">+393331234567</psf:credProperty>
                <psf:credProperty Name="TimeZone">1</psf:credProperty>
                <psf:credProperty Name="Timezone">1</psf:credProperty>
                <psf:credProperty Name="AgeStatus">1</psf:credProperty>
                <psf:credProperty Name="HasParent">0</psf:credProperty>
                <psf:credProperty Name="Consent">1</psf:credProperty>
                <psf:credProperty Name="LangPreference">1040</psf:credProperty>
                <psf:credProperty Name="Flags">40100643</psf:credProperty>
                <psf:credProperty Name="FlagsV2">00000000</psf:credProperty>
                <psf:credProperty Name="ChildFlags">00000001</psf:credProperty>
                <psf:credProperty Name="MainBrandID">MSFT</psf:credProperty>
                <psf:credProperty Name="IsWinLiveUser">true</psf:credProperty>
                <psf:credProperty Name="AssociatedForStrongAuth">0</psf:credProperty>
                <psf:credProperty Name="FederationBrandName">Windows Live</psf:credProperty>
            </psf:credProperties>
        </psf:pp>
    </S:Header>"""
    
    soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<S:Envelope xmlns:S="http://www.w3.org/2003/05/soap-envelope"
            xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
            xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd"
            xmlns:wsp="http://schemas.xmlsoap.org/ws/2004/09/policy"
            xmlns:wsa="http://www.w3.org/2005/08/addressing"
            xmlns:wst="http://schemas.xmlsoap.org/ws/2005/02/trust"
            xmlns:ps="http://schemas.microsoft.com/Passport/SoapServices/PPCRL"
            xmlns:psf="http://schemas.microsoft.com/Passport/SoapServices/SOAPFault">{header_block}
    <S:Body>
        <wst:RequestSecurityTokenResponseCollection>
            {all_responses}
        </wst:RequestSecurityTokenResponseCollection>
    </S:Body>
</S:Envelope>"""
    return soap_envelope.strip()

def build_wstrust_fault(fault_code="psf:AuthenticationFailed", message="Credenziali non valide.") -> str:
    """Builds a WS-Trust SOAP 1.2 Fault response."""
    return f"""<?xml version="1.0" encoding="utf-8"?>
<S:Envelope xmlns:S="http://www.w3.org/2003/05/soap-envelope"
            xmlns:psf="http://schemas.microsoft.com/Passport/SoapServices/SOAPFault">
    <S:Body>
        <S:Fault>
            <S:Code>
                <S:Value>S:Sender</S:Value>
                <S:Subcode>
                    <S:Value>{fault_code}</S:Value>
                </S:Subcode>
            </S:Code>
            <S:Reason>
                <S:Text xml:lang="it-IT">{message}</S:Text>
            </S:Reason>
            <S:Detail>
                <psf:error>
                    <psf:value>0x80048821</psf:value>
                    <psf:internalerror>
                        <psf:code>0x80048821</psf:code>
                        <psf:text>{message}</psf:text>
                    </psf:internalerror>
                </psf:error>
            </S:Detail>
        </S:Fault>
    </S:Body>
</S:Envelope>""".strip()
