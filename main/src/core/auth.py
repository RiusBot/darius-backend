import os
import json
import secrets
import requests
import logging
import functools
from firebase_admin import auth, firestore
from jose import JWTError
from werkzeug.exceptions import Unauthorized
from google.cloud import secretmanager


usingProjectId = os.getenv('project_id', 'local')
logger = logging.getLogger(__name__)
db = firestore.Client()


async def openapi_auth(bearer_token: str, request):
    if request._method == "GET":
        json_payload = dict(request.rel_url.query)
    else:
        json_payload = await request.text()
        json_payload = json.loads(json_payload) if json_payload else {}

    json_payload['idToken'] = bearer_token
    json_payload['token'] = bearer_token
    if usingProjectId != "local":
        if check_client_access(json_payload) is False:
            if check_server_access(json_payload) is False:
                raise Unauthorized from JWTError
    return {'sub': ''}


async def openapi_auth_backend_only(bearer_token: str, request):
    if request._method == "GET":
        json_payload = dict(request.rel_url.query)
    else:
        json_payload = await request.text()
        json_payload = json.loads(json_payload) if json_payload else {}

    json_payload['idToken'] = bearer_token
    json_payload['token'] = bearer_token
    if usingProjectId != "local":
        if check_server_access(json_payload) is False:
            raise Unauthorized from JWTError
    return {'sub': ''}


def authenticate(json_payload):
    if usingProjectId != "local":
        if check_client_access(json_payload) is False:
            if check_server_access(json_payload) is False:
                return False
    return True


def check_server_access(json_payload):
    try:
        Token = fetch_secret_token_firestore()
        requestToken = json_payload.get('token')
        if not Token or not requestToken:
            return False
        return secrets.compare_digest(Token, requestToken)
    except Exception:
        logger.error("exception when dealing with check_server_access token")
        return False


@functools.lru_cache(maxsize=None)
def fetch_secret_token_manager():
    secretsManagerClient = secretmanager.SecretManagerServiceClient()
    name = secretsManagerClient.secret_version_path(usingProjectId, "backend", "latest")
    response = secretsManagerClient.access_secret_version(request={"name": name})
    payload = response.payload.data.decode("UTF-8")
    try:
        Secret = json.loads(payload)
        Token = Secret['token']
    except json.decoder.JSONDecodeError:
        Token = payload
    return Token


@functools.lru_cache(maxsize=None)
def fetch_secret_token_firestore():
    Secret = db.collection("config").document("backend").get().to_dict()
    Token = Secret['auth_token']
    return Token


@functools.lru_cache(maxsize=64)
def verify_firestore_uid_exists(uid: str):
    user = db.collection("users").document(uid).get().to_dict()
    return (user is not None)


def check_client_access(json_payload: dict):
    # TODO HERE
    try:
        # https://firebase.google.com/docs/auth/admin/verify-id-tokens#web
        clientUserIdToken = json_payload.get('idToken')
        if clientUserIdToken is None or clientUserIdToken == '':
            return False
        decoded_token = auth.verify_id_token(clientUserIdToken, check_revoked=True)
        if decoded_token.get('uid') is None or json_payload.get('uid') is None:
            return False
        return secrets.compare_digest(json_payload["uid"], decoded_token["uid"])
    except Exception:
        logger.error("exception when dealing with check_client_access token")
        return False


def fetch_access_token(audience_url: str):
    # set up metadata server request
    metadata_server_token_url = "http://metadata/computeMetadata/v1/instance/service-accounts/default/identity?audience="

    token_request_url = metadata_server_token_url + audience_url
    token_request_headers = {"Metadata-Flavor": "Google"}

    # fetch the token
    token_response = requests.get(token_request_url, headers=token_request_headers)
    jwt = token_response.content.decode("utf-8")

    return jwt
