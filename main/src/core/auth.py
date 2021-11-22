import os
import requests
import logging
import functools
from firebase_admin import auth, initialize_app


initialize_app()
usingProjectId = os.getenv('project_id', 'darius')


def authenticate(json_payload):
    if usingProjectId != "darius":
        if check_client_access(json_payload) is False:
            if check_server_access(json_payload) is False:
                return False
    return True


def check_server_access(json_payload):
    try:
        Token = fetch_secret_token()
        requestToken = json_payload.get('token')
        if not Token or not requestToken:
            return False
        return Token == requestToken
    except Exception:
        logging.error("exception when dealing with check_server_access token")
        return False


@functools.lru_cache(maxsize=None)
def fetch_secret_token():
    token = fetch_token()
    return token


def check_client_access(json_payload):
    # TODO HERE
    try:
        # https://firebase.google.com/docs/auth/admin/verify-id-tokens#web
        clientUserIdToken = json_payload.get('idToken')
        if clientUserIdToken is None or clientUserIdToken == '':
            return False
        decoded_token = auth.verify_id_token(clientUserIdToken)
        if json_payload.get('uid') != decoded_token.get('uid'):
            return False
        uid = decoded_token.get('uid')
        return (uid is not None)
    except Exception:
        logging.error("exception when dealing with check_client_access token")
        return False


def fetch_access_token(audience_url):
    # set up metadata server request
    metadata_server_token_url = "http://metadata/computeMetadata/v1/instance/service-accounts/default/identity?audience="

    token_request_url = metadata_server_token_url + audience_url
    token_request_headers = {"Metadata-Flavor": "Google"}

    # fetch the token
    token_response = requests.get(token_request_url, headers=token_request_headers)
    jwt = token_response.content.decode("utf-8")

    return jwt
