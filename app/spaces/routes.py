import logging
from fastapi import APIRouter, Request, Response
from fastapi.responses import Response
from app.database import get_user_by_email, get_db

logger = logging.getLogger("spaces")
router = APIRouter(tags=["Windows Live Spaces & Storage"])

WLPG_XML = """<?xml version="1.0" encoding="utf-8"?>
<wlx:Clients xmlns:wlx="http://schemas.microsoft.com/wlx" xmlns="http://schemas.microsoft.com/wlx">
    <wlx:Client id="WLPG">
        <MinimumVersion>1.0.0.0</MinimumVersion>
        <PersonalPublishVerification>true</PersonalPublishVerification>
        <GroupPublishVerification>true</GroupPublishVerification>
        <EventPublishVerification>true</EventPublishVerification>
        <SoapboxPublishVerification>true</SoapboxPublishVerification>
        <FlickrPublishVerification>true</FlickrPublishVerification>
    </wlx:Client>
    <Client id="WLPG">
        <MinimumVersion>1.0.0.0</MinimumVersion>
        <PersonalPublishVerification>true</PersonalPublishVerification>
        <GroupPublishVerification>true</GroupPublishVerification>
        <EventPublishVerification>true</EventPublishVerification>
        <SoapboxPublishVerification>true</SoapboxPublishVerification>
        <FlickrPublishVerification>true</FlickrPublishVerification>
    </Client>
</wlx:Clients>
""".strip()

def build_profile_xml(user: dict = None) -> str:
    if not user:
        first = "Stefano"
        last = "De Luca"
        display = "Stefano De Luca"
        email = "stefano@live.it"
        gender = "Male"
        birth = "1995-01-01T00:00:00Z"
        country = "IT"
    else:
        first = user.get("first_name") or user.get("display_name", "User").split()[0]
        last = user.get("last_name") or "User"
        display = user.get("display_name", f"{first} {last}")
        email = user.get("email", "user@live.it")
        gender = "Male" if user.get("gender") == "m" else "Female" if user.get("gender") == "f" else "Unspecified"
        birth = f"{user.get('birth_date', '1995-01-01')}T00:00:00Z"
        country = user.get("country", "IT")

    return f"""<?xml version="1.0" encoding="utf-8"?>
<PersonalContactProfile xmlns="http://schemas.microsoft.com/LiveSearch/2008/03/PersonalContactProfile" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <FirstName>{first}</FirstName>
    <LastName>{last}</LastName>
    <DisplayName>{display}</DisplayName>
    <NickName>{first}</NickName>
    <Gender>{gender}</Gender>
    <BirthDate>{birth}</BirthDate>
    <PrimaryEmail>{email}</PrimaryEmail>
    <PersonalEmail>{email}</PersonalEmail>
    <MobilePhone>+393331234567</MobilePhone>
    <PrimaryPhone>+393331234567</PrimaryPhone>
    <Country>{country}</Country>
    <City>Roma</City>
    <State>RM</State>
    <PostalCode>00100</PostalCode>
    <TimeZone>+01:00</TimeZone>
    <UserTileURL>/static/img/avatar.png</UserTileURL>
    <TileURL>/static/img/avatar.png</TileURL>
    <PhotoURL>/static/img/avatar.png</PhotoURL>
    <FirstNameLastModified>2026-10-29T20:00:00Z</FirstNameLastModified>
    <LastNameLastModified>2026-10-29T20:00:00Z</LastNameLastModified>
</PersonalContactProfile>""".strip()

@router.get("/wlpg.aspx")
@router.post("/wlpg.aspx")
async def spaces_wlpg_config(request: Request):
    logger.info(f"WLPG client config requested from {request.client.host if request.client else 'local'}")
    return Response(content=WLPG_XML, media_type="text/xml; charset=utf-8")

@router.get("/users/{user_id}/myprofile/personalcontactprofile")
async def user_personal_contact_profile(user_id: str, request: Request):
    logger.info(f"Personal contact profile requested for user {user_id}")
    return Response(content=build_profile_xml(), media_type="application/web3s+xml; charset=utf-8")

@router.get("/users/{user_id}/myprofile/{rest_of_path:path}")
async def user_profile_catchall(user_id: str, rest_of_path: str, request: Request):
    logger.info(f"Profile sub-path requested: {rest_of_path} for user {user_id}")
    return Response(content=build_profile_xml(), media_type="application/web3s+xml; charset=utf-8")

# -------------------------------------------------------------------
# SOAP SchematizedStore Responses
# -------------------------------------------------------------------

RESPONSE_GET_PROFILE = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <soap:Body>
        <GetProfileResponse xmlns="http://www.msn.com/webservices/storage/w10">
            <GetProfileResult>
                <ResourceID>00000000-0000-0000-0000-000000000001</ResourceID>
                <DateModified>2026-10-31T17:00:00Z</DateModified>
                <ExpressionProfile>
                    <ResourceID>00000000-0000-0000-0000-000000000002</ResourceID>
                    <DateModified>2026-10-31T17:00:00Z</DateModified>
                    <DisplayName>Stefano De Luca</DisplayName>
                    <DisplayNameLastModified>2026-10-31T17:00:00Z</DisplayNameLastModified>
                    <PersonalStatus>Online con Windows Live</PersonalStatus>
                    <PersonalStatusLastModified>2026-10-31T17:00:00Z</PersonalStatusLastModified>
                    <StaticUserTilePublicURL>https://login.live.com/static/img/avatar.png</StaticUserTilePublicURL>
                    <Photo>https://login.live.com/static/img/avatar.png</Photo>
                    <Flags>0</Flags>
                </ExpressionProfile>
            </GetProfileResult>
        </GetProfileResponse>
    </soap:Body>
</soap:Envelope>""".strip()

RESPONSE_GET_SPACE = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <soap:Body>
        <GetSpaceResponse xmlns="http://www.msn.com/webservices/storage/w10">
            <GetSpaceResult>
                <ResourceID>00000000-0000-0000-0000-000000000003</ResourceID>
                <Name>Album e Foto Personali</Name>
                <Tagline>Il mio spazio su Windows Live Spaces</Tagline>
                <DateCreated>2026-10-31T17:00:00Z</DateCreated>
                <DateModified>2026-10-31T17:00:00Z</DateModified>
            </GetSpaceResult>
        </GetSpaceResponse>
    </soap:Body>
</soap:Envelope>""".strip()

RESPONSE_GET_FOLDERS = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <soap:Body>
        <GetFoldersResponse xmlns="http://www.msn.com/webservices/storage/w10">
            <GetFoldersResult>
                <Folder>
                    <ResourceID>00000000-0000-0000-0000-000000000010</ResourceID>
                    <FolderResourceID>00000000-0000-0000-0000-000000000010</FolderResourceID>
                    <Name>Raccolta Foto Principale</Name>
                    <DocumentCount>0</DocumentCount>
                    <DateCreated>2026-10-31T17:00:00Z</DateCreated>
                    <DateModified>2026-10-31T17:00:00Z</DateModified>
                </Folder>
            </GetFoldersResult>
        </GetFoldersResponse>
    </soap:Body>
</soap:Envelope>""".strip()

RESPONSE_GET_PHOTOS = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <soap:Body>
        <GetPhotosResponse xmlns="http://www.msn.com/webservices/storage/w10">
            <GetPhotosResult>
            </GetPhotosResult>
        </GetPhotosResponse>
    </soap:Body>
</soap:Envelope>""".strip()

RESPONSE_FIND_PHOTOS = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <soap:Body>
        <FindPhotosResponse xmlns="http://www.msn.com/webservices/storage/w10">
            <FindPhotosResult>
            </FindPhotosResult>
        </FindPhotosResponse>
    </soap:Body>
</soap:Envelope>""".strip()

RESPONSE_CREATE_FOLDER = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <soap:Body>
        <CreateFolderResponse xmlns="http://www.msn.com/webservices/storage/w10">
            <CreateFolderResult>
                <ResourceID>00000000-0000-0000-0000-000000000020</ResourceID>
                <FolderResourceID>00000000-0000-0000-0000-000000000020</FolderResourceID>
            </CreateFolderResult>
        </CreateFolderResponse>
    </soap:Body>
</soap:Envelope>""".strip()

RESPONSE_CREATE_DOCUMENT = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <soap:Body>
        <CreateDocumentResponse xmlns="http://www.msn.com/webservices/storage/w10">
            <CreateDocumentResult>
                <ResourceID>00000000-0000-0000-0000-000000000030</ResourceID>
                <DocumentResourceID>00000000-0000-0000-0000-000000000030</DocumentResourceID>
            </CreateDocumentResult>
        </CreateDocumentResponse>
    </soap:Body>
</soap:Envelope>""".strip()

@router.post("/storageservice/SchematizedStore.asmx")
@router.get("/storageservice/SchematizedStore.asmx")
@router.post("/storageservice/schematizedstore.asmx")
@router.get("/storageservice/schematizedstore.asmx")
@router.post("/StorageService/SchematizedStore.asmx")
@router.get("/StorageService/SchematizedStore.asmx")
@router.post("/SchematizedStore.asmx")
@router.get("/SchematizedStore.asmx")
@router.post("/schematizedstore.asmx")
@router.get("/schematizedstore.asmx")
async def schematized_store_service(request: Request):
    """
    Handles SOAP calls from Windows Live Photo Gallery for Windows Live Spaces & Storage.
    Supports GetProfile, GetSpace, GetFolders, GetPhotos, FindPhotos, CreateFolder, CreateDocument.
    """
    body_bytes = await request.body()
    body_text = body_bytes.decode("utf-8", errors="ignore")
    soap_action = request.headers.get("soapaction", "")

    logger.info(f"SchematizedStore request: action='{soap_action}' (body len: {len(body_bytes)})")

    req_lower = (soap_action + " " + body_text).lower()

    if "getfolders" in req_lower:
        logger.info("Serving GetFoldersResponse")
        return Response(content=RESPONSE_GET_FOLDERS, media_type="text/xml; charset=utf-8")
    elif "getspace" in req_lower:
        logger.info("Serving GetSpaceResponse")
        return Response(content=RESPONSE_GET_SPACE, media_type="text/xml; charset=utf-8")
    elif "findphotos" in req_lower:
        logger.info("Serving FindPhotosResponse")
        return Response(content=RESPONSE_FIND_PHOTOS, media_type="text/xml; charset=utf-8")
    elif "getphotos" in req_lower:
        logger.info("Serving GetPhotosResponse")
        return Response(content=RESPONSE_GET_PHOTOS, media_type="text/xml; charset=utf-8")
    elif "createfolder" in req_lower:
        logger.info("Serving CreateFolderResponse")
        return Response(content=RESPONSE_CREATE_FOLDER, media_type="text/xml; charset=utf-8")
    elif "createdocument" in req_lower:
        logger.info("Serving CreateDocumentResponse")
        return Response(content=RESPONSE_CREATE_DOCUMENT, media_type="text/xml; charset=utf-8")
    else:
        logger.info("Serving GetProfileResponse (default)")
        return Response(content=RESPONSE_GET_PROFILE, media_type="text/xml; charset=utf-8")
