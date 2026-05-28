import secrets
import time
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from starlette import status
from wikibaseintegrator.wbi_login import LoginError

from ceur_graph.ceur_dev import CeurDev
from ceur_graph.datamodel.auth import WikibaseBotAuth
from ceur_graph.settings import get_settings

SECRET_KEY = secrets.token_hex(20)
ALGORITHM = "HS256"
_OAUTH_STATE_TTL_SECONDS = 600

users_db: dict[str, CeurDev] = {}
oauth_states: dict[str, float] = {}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=True)


class Token(BaseModel):
    access_token: str
    token_type: str


def _access_token_expires() -> timedelta:
    return timedelta(minutes=get_settings().session_ttl_minutes)


def register_session(ceur_dev: CeurDev, subject: str) -> str:
    """Issue a session token for the given CeurDev instance and store it."""
    access_token = create_access_token(data={"sub": subject}, expires_delta=_access_token_expires())
    users_db[access_token] = ceur_dev
    return access_token


async def login_user(username: str, password: str) -> Token:
    """
    Validate the given user name and password. If they are valid generate an access token and return it.
    After generating the access token, the token and the Wikibase login object are stored in the user db
    """
    auth = WikibaseBotAuth(user=username, password=password)
    ceur_dev = CeurDev(auth)
    try:
        ceur_dev.get_wbi_login()
    except LoginError as e:
        raise HTTPException(status_code=400, detail="Incorrect username or password") from e

    access_token = register_session(ceur_dev, subject=username)
    return Token(access_token=access_token, token_type="bearer")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> CeurDev:
    """
    Get the wikibase instance of the current user.
    The current user identifies with his token.
    """
    user = users_db.get(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def issue_oauth_state() -> str:
    """Generate a fresh OAuth ``state`` value and remember it for later validation."""
    _gc_oauth_states()
    state = secrets.token_urlsafe(24)
    oauth_states[state] = time.time() + _OAUTH_STATE_TTL_SECONDS
    return state


def consume_oauth_state(state: str) -> bool:
    """Pop and validate an OAuth ``state`` value. Returns True if it was valid."""
    _gc_oauth_states()
    expiry = oauth_states.pop(state, None)
    return expiry is not None and expiry >= time.time()


def _gc_oauth_states() -> None:
    now = time.time()
    expired = [s for s, exp in oauth_states.items() if exp < now]
    for s in expired:
        oauth_states.pop(s, None)
