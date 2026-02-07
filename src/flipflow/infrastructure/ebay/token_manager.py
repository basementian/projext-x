"""OAuth 2.0 token manager for eBay REST APIs."""

import time
from dataclasses import dataclass

import httpx

from flipflow.core.exceptions import EbayAuthError


SELLER_SCOPES = (
    "https://api.ebay.com/oauth/api_scope/sell.inventory "
    "https://api.ebay.com/oauth/api_scope/sell.marketing "
    "https://api.ebay.com/oauth/api_scope/sell.analytics.readonly "
    "https://api.ebay.com/oauth/api_scope/sell.account "
    "https://api.ebay.com/oauth/api_scope/sell.fulfillment"
)

APP_SCOPE = "https://api.ebay.com/oauth/api_scope"


@dataclass
class TokenData:
    """Cached token with expiry tracking."""

    access_token: str
    token_type: str
    expires_at: float  # time.monotonic() value
    scope: str = ""

    @property
    def is_expired(self) -> bool:
        """True if token is expired or within 5-minute safety buffer."""
        return time.monotonic() >= (self.expires_at - 300)


class EbayTokenManager:
    """Manages eBay OAuth 2.0 tokens with automatic refresh.

    Two flows:
    1. User token (via refresh_token grant) — for seller APIs
    2. Application token (via client_credentials grant) — for Browse API
    """

    TOKEN_PATH = "/identity/v1/oauth2/token"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        base_url: str,
    ):
        self._client_id = client_id
        self._client_secret = client_secret
        self._refresh_token = refresh_token
        self._base_url = base_url
        self._user_token: TokenData | None = None
        self._app_token: TokenData | None = None
        self._http: httpx.AsyncClient | None = None

    async def _get_http(self) -> httpx.AsyncClient:
        """Lazy-init a dedicated httpx client for token requests."""
        if self._http is None:
            self._http = httpx.AsyncClient(
                base_url=self._base_url,
                auth=(self._client_id, self._client_secret),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=httpx.Timeout(30.0),
            )
        return self._http

    async def get_user_token(self) -> str:
        """Get a valid user access token, refreshing if needed."""
        if self._user_token is None or self._user_token.is_expired:
            await self._refresh_user_token()
        return self._user_token.access_token

    async def get_app_token(self) -> str:
        """Get a valid application token, refreshing if needed."""
        if self._app_token is None or self._app_token.is_expired:
            await self._fetch_app_token()
        return self._app_token.access_token

    async def _refresh_user_token(self) -> None:
        """Exchange refresh_token for a new access_token."""
        http = await self._get_http()
        response = await http.post(
            self.TOKEN_PATH,
            data={
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token,
                "scope": SELLER_SCOPES,
            },
        )
        self._handle_token_response(response, is_user=True)

    async def _fetch_app_token(self) -> None:
        """Get an application token via client credentials."""
        http = await self._get_http()
        response = await http.post(
            self.TOKEN_PATH,
            data={
                "grant_type": "client_credentials",
                "scope": APP_SCOPE,
            },
        )
        self._handle_token_response(response, is_user=False)

    def _handle_token_response(
        self, response: httpx.Response, *, is_user: bool,
    ) -> None:
        """Parse token response or raise EbayAuthError."""
        if response.status_code != 200:
            raise EbayAuthError(
                f"Token request failed: {response.status_code} {response.text}"
            )

        data = response.json()
        token = TokenData(
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            expires_at=time.monotonic() + data.get("expires_in", 7200),
            scope=data.get("scope", ""),
        )
        if is_user:
            self._user_token = token
        else:
            self._app_token = token

    async def close(self) -> None:
        """Close the internal HTTP client."""
        if self._http is not None:
            await self._http.aclose()
            self._http = None
