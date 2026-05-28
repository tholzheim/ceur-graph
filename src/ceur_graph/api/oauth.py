"""OAuth 2.0 authorization-code login flow against a Wikibase instance.

Exposes two endpoints:

* ``GET /oauth/login`` — redirects the browser to the Wikibase
  ``/oauth2/authorize`` endpoint.
* ``GET /oauth/callback`` — exchanges the authorization code for an access
  token, builds a user-bound :class:`CeurDev`, stores it in the session
  store, and redirects the SPA with the session token in the URL fragment.
"""

from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from ceur_graph.api.auth import consume_oauth_state, issue_oauth_state, register_session
from ceur_graph.ceur_dev import CeurDev
from ceur_graph.datamodel.auth import WikibaseUserOAuth2
from ceur_graph.settings import get_settings

router = APIRouter(prefix="/oauth", tags=["Authentication"])


def _rest_base() -> str:
    return get_settings().wikibase_mediawiki_rest_url.unicode_string().rstrip("/")


def _require_oauth_config() -> tuple[str, str, str]:
    settings = get_settings()
    if not settings.oauth_client_id or not settings.oauth_client_secret or not settings.oauth_redirect_uri:
        raise HTTPException(
            status_code=503,
            detail=(
                "OAuth is not configured. Set CEUR_GRAPH_OAUTH_CLIENT_ID, "
                "CEUR_GRAPH_OAUTH_CLIENT_SECRET, and CEUR_GRAPH_OAUTH_REDIRECT_URI."
            ),
        )
    return (
        settings.oauth_client_id,
        settings.oauth_client_secret.get_secret_value(),
        settings.oauth_redirect_uri.unicode_string(),
    )


@router.get("/login")
async def oauth_login() -> RedirectResponse:
    """Start the OAuth 2.0 authorization-code flow."""
    client_id, _client_secret, redirect_uri = _require_oauth_config()
    state = issue_oauth_state()
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
    }
    return RedirectResponse(url=f"{_rest_base()}/oauth2/authorize?{urlencode(params)}", status_code=302)


@router.get("/callback")
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
) -> RedirectResponse:
    """Exchange the authorization code for an access token and create a session."""
    client_id, client_secret, redirect_uri = _require_oauth_config()
    if not consume_oauth_state(state):
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    token_url = f"{_rest_base()}/oauth2/access_token"
    profile_url = f"{_rest_base()}/oauth2/resource/profile"
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"OAuth token exchange failed: {resp.text}")
        payload = resp.json()
        access_token = payload.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="OAuth token exchange returned no access_token")

        username = "oauth2-user"
        try:
            profile_resp = await client.get(profile_url, headers={"Authorization": f"Bearer {access_token}"})
            if profile_resp.status_code == 200:
                username = profile_resp.json().get("username") or username
        except httpx.HTTPError:
            pass

    auth = WikibaseUserOAuth2(
        access_token=access_token,
        refresh_token=payload.get("refresh_token"),
        client_id=client_id,
        client_secret=client_secret,
    )
    ceur_dev = CeurDev(auth)
    # Eagerly resolve the wbi login so we fail loudly here if the token is bad,
    # rather than on the user's first edit.
    ceur_dev.get_wbi_login()
    session_token = register_session(ceur_dev, subject=username)

    app_base = get_settings().app_base_url.unicode_string().rstrip("/")
    return RedirectResponse(url=f"{app_base}/#token={session_token}", status_code=302)
