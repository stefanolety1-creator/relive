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
    """
    Windows Live Photo Gallery client verification and capabilities endpoint.
    """
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

SCHEMATIZED_STORE_RESPONSE = """<?xml version="1.0" encoding="utf-8"?>
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

@router.post("/storageservice/SchematizedStore.asmx")
@router.get("/storageservice/SchematizedStore.asmx")
@router.post("/SchematizedStore.asmx")
@router.get("/SchematizedStore.asmx")
async def schematized_store_service(request: Request):
    logger.info(f"SchematizedStore SOAP request from {request.client.host if request.client else 'local'}")
    return Response(content=SCHEMATIZED_STORE_RESPONSE, media_type="text/xml; charset=utf-8")
