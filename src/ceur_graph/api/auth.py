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

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
users_db: dict[str, CeurDev] = {}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    access_token: str
    token_type: str


async def login_user(username: str, password: str) -> Token:
    """
    Validate the given user name and password. If they are valid generate an access token and return it.
    After generating the access token, the token and the Wikibase login object are stored in the user db
    :param username: user name
    :param password: password
    :return:
    """
    auth = WikibaseBotAuth(user=username, password=password)
    ceur_dev = CeurDev(auth)
    try:
        ceur_dev.get_wbi_login()
    except LoginError as e:
        raise HTTPException(status_code=400, detail="Incorrect username or password") from e

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": username}, expires_delta=access_token_expires)
    users_db[access_token] = ceur_dev
    return Token(access_token=access_token, token_type="bearer")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> CeurDev:
    """
    Get the wikibase instance of the current user.
    The current user identifies with his token.
    :param token: token of the current user
    :return: CEURDev instance of the current user
    :raises HTTPException: if the token is invalid
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
    """
    Create JWT access token.
    :param data:
    :param expires_delta:
    :return:
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
