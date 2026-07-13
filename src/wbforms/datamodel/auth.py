from enum import Enum

from pydantic import BaseModel


class WikibaseLoginTypes(Enum):
    """
    Wikibase login types supported by wikibaseintegrator
    """

    BOT = "bot"
    USER = "user"
    OAUTH1 = "oauth1"
    OAUTH2 = "oauth2"
    USER_OAUTH2 = "user_oauth2"
    NONE = "none"


class WikibaseAuthorizationConfig(BaseModel):
    """
    Wikibase Oauth Owner-only consumer
    https://www.mediawiki.org/wiki/OAuth/Owner-only_consumers
    """

    auth_type: WikibaseLoginTypes = WikibaseLoginTypes.NONE


class WikibaseOauth1(WikibaseAuthorizationConfig):
    """
    Wikibase Oauth1
    """

    auth_type: WikibaseLoginTypes = WikibaseLoginTypes.OAUTH1
    consumer_token: str
    consumer_secret: str
    access_token: str
    access_secret: str


class WikibaseOauth2(WikibaseAuthorizationConfig):
    """
    Wikibase Oauth2
    """

    auth_type: WikibaseLoginTypes = WikibaseLoginTypes.OAUTH2
    consumer_token: str
    consumer_secret: str


class WikibaseBotAuth(WikibaseAuthorizationConfig):
    """
    Wikibase Bot
    """

    auth_type: WikibaseLoginTypes = WikibaseLoginTypes.BOT
    user: str
    password: str


class WikibaseUserAuth(WikibaseAuthorizationConfig):
    """
    Wikibase User
    """

    auth_type: WikibaseLoginTypes = WikibaseLoginTypes.USER
    user: str
    password: str


class WikibaseUserOAuth2(WikibaseAuthorizationConfig):
    """
    Wikibase OAuth 2.0 user-delegated access (authorization code grant).
    The access token is obtained on behalf of a logged-in user — edits made
    with it are attributed to that user.
    """

    auth_type: WikibaseLoginTypes = WikibaseLoginTypes.USER_OAUTH2
    access_token: str
    refresh_token: str | None = None
    client_id: str | None = None
    client_secret: str | None = None


class Authorization(BaseModel):
    """
    Wikibase Oauth Owner-only consumer
    https://www.mediawiki.org/wiki/OAuth/Owner-only_consumers
    """

    factgrid: WikibaseOauth1 | WikibaseOauth2 | WikibaseBotAuth | WikibaseUserAuth | WikibaseAuthorizationConfig = (
        WikibaseAuthorizationConfig()
    )
    wikidata: WikibaseOauth1 | WikibaseOauth2 | WikibaseBotAuth | WikibaseUserAuth | WikibaseAuthorizationConfig = (
        WikibaseAuthorizationConfig()
    )
