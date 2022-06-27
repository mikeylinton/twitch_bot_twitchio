import os
from urllib.parse import quote_plus
import requests
from dotenv import load_dotenv
import webbrowser
import datetime
import random
import string

TWITCH_CLIENT_ID = "TWITCH_CLIENT_ID"
TWITCH_CLIENT_SECRET = "TWITCH_CLIENT_SECRET"
TWITCH_REDIRECT_URI = "TWITCH_REDIRECT_URI"
TWITCH_OAUTH_ACCESS_TOKEN = "TWITCH_OAUTH_ACCESS_TOKEN"
TWITCH_OAUTH_REFRESH_TOKEN = "TWITCH_OAUTH_REFRESH_TOKEN"
TWITCH_OAUTH_TOKEN_EXPIRES_ON = "TWITCH_OAUTH_TOKEN_EXPIRES_ON"

DOTENV_FPATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
OAUTH_TOKEN_FPATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env.oauth")
TWITCH_API_STATE = "".join(random.sample(string.ascii_letters + string.digits, 32))
TWITCH_API_SCOPE = "TWITCH_API_SCOPE"
TWITCH_OAUTH_URI = "https://id.twitch.tv/oauth2"


def setup_new_profile():
    webbrowser.open_new_tab("https://dev.twitch.tv/console/apps")
    client_id = input("Enter the Client ID: ")
    client_secret = input("Enter the Client Secret: ")
    channel_list = input("Enter your twitch channel: ")
    to_write = [
        f'TWITCH_CLIENT_ID="{client_id}"',
        f'TWITCH_CLIENT_SECRET="{client_secret}"',
        'TWITCH_REDIRECT_URI="http://localhost"',
        f'TWITCH_CHANNEL_LIST="{channel_list}"',
    ]
    with open(DOTENV_FPATH, "w") as f:
        for line in to_write:
            f.write(f"{line}\n")


def save_token(access_token: str, expires_on: str, refresh_token: str):
    to_write = [
        f'{TWITCH_OAUTH_ACCESS_TOKEN}="{access_token}"',
        f'{TWITCH_OAUTH_TOKEN_EXPIRES_ON}="{expires_on}"',
        f'{TWITCH_OAUTH_REFRESH_TOKEN}="{refresh_token}"',
    ]
    with open(OAUTH_TOKEN_FPATH, "w") as f:
        for line in to_write:
            f.write(f"{line}\n")


def get_auth_uri(client_id, redirect_uri, api_scope, api_state):
    # https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/#authorization-code-grant-flow
    auth_uri = f"\
    {TWITCH_OAUTH_URI}/authorize\
    ?response_type=code\
    &client_id={client_id}\
    &redirect_uri={redirect_uri}\
    &scope={api_scope}\
    &state={api_state}\
    ".replace(
        " ", ""
    )
    return auth_uri


def get_auth_code() -> str:
    auth_uri = get_auth_uri(
        os.environ[TWITCH_CLIENT_ID],
        os.environ[TWITCH_REDIRECT_URI],
        quote_plus(os.environ[TWITCH_API_SCOPE]),
        TWITCH_API_STATE,
    )

    webbrowser.open_new_tab(auth_uri)
    redirect_uri = input("Enter the redirect URL: ")
    return parse_auth_uri(redirect_uri)


def parse_auth_uri(uri: str) -> str:
    try:
        redirect_uri, redirect_vars = uri.split("?")
        ret_auth_vars = redirect_vars.split("&")
        auth = {}
        for ret_auth_var in ret_auth_vars:
            k, v = ret_auth_var.split("=")
            auth[k] = v
        valid_response = True
        if redirect_uri.strip("/") != os.environ[TWITCH_REDIRECT_URI].strip("/"):
            print("[ERROR] Redirect URL was altered")
            valid_response = False
        if auth["scope"] != quote_plus(os.environ[TWITCH_API_SCOPE]):
            print("[ERROR] Scope was altered")
            valid_response = False
        if auth["state"] != TWITCH_API_STATE:
            print("[ERROR] State was altered")
            valid_response = False
        twitch_auth_code = auth["code"]
    except Exception:
        valid_response = False
        print("[ERROR] Unexpected response:", auth, uri)
    if not valid_response:
        exit(1)
    return twitch_auth_code


def request_new_token(client_id: str, client_secret: str, redirect_uri: str, refresh_token: str = None) -> str:
    load_dotenv()
    body = {
        "client_id": client_id,
        "client_secret": client_secret,
    }

    if refresh_token:
        grant_type = "refresh_token"
        auth_type = "refresh_token"
        auth_value = refresh_token
    else:
        grant_type = "authorization_code"
        auth_type = "code"
        auth_value = get_auth_code()
        body["redirect_uri"] = redirect_uri
    body["grant_type"] = grant_type
    body[auth_type] = auth_value

    _time = datetime.datetime.now()
    _response = requests.post("https://id.twitch.tv/oauth2/token", body)
    data = _response.json()
    try:
        if data.get("error"):
            print("[ERROR]", data["error"], data["message"])
            return None
        expires_on = _time + datetime.timedelta(0, data["expires_in"])
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
    except KeyError:
        print("[ERROR] Unexpected response:", data)
        exit(1)
    save_token(access_token, expires_on, refresh_token)
    return access_token


def is_expired(_datetime: str) -> bool:
    try:
        expires_on = datetime.datetime.strptime(_datetime, "%Y-%m-%d %H:%M:%S.%f")
        expired = datetime.datetime.now() > expires_on
    except ValueError:
        return True
    return expired


def get_token() -> str:
    if not os.path.isfile(DOTENV_FPATH):
        setup_new_profile()
    load_dotenv()

    client_id = os.environ[TWITCH_CLIENT_ID]
    client_secret = os.environ[TWITCH_CLIENT_SECRET]
    redirect_uri = os.environ[TWITCH_REDIRECT_URI]

    if not os.path.isfile(OAUTH_TOKEN_FPATH):
        access_token = request_new_token(client_id, client_secret, redirect_uri)
    else:
        load_dotenv(OAUTH_TOKEN_FPATH)
        try:
            access_token = os.environ[TWITCH_OAUTH_ACCESS_TOKEN]
            refresh_token = os.environ[TWITCH_OAUTH_REFRESH_TOKEN]
            if is_expired(os.environ[TWITCH_OAUTH_TOKEN_EXPIRES_ON]):
                access_token = request_new_token(client_id, client_secret, redirect_uri, refresh_token)
                if not access_token:
                    access_token = request_new_token(client_id, client_secret, redirect_uri)
        except KeyError:
            access_token = request_new_token(client_id, client_secret, redirect_uri)
    if not access_token:
        print("Something went wrong while requesting access token")
        exit(1)
    return access_token
