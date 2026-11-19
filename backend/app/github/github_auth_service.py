"""GitHub App Authentication Service.

Handles RS256 App JWT minting, short-lived installation access token exchange,
caching with TTL expiration, and rate-limit aware HTTP client provisioning.
"""

from datetime import datetime, timezone
import time
from typing import Dict, Optional, Tuple
import httpx
import jwt
from app.core.config import get_settings
from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from app.core.logging import get_logger

logger = get_logger("openreview.github.auth")
settings = get_settings()

GITHUB_API_BASE = "https://api.github.com"
GITHUB_API_VERSION = "2022-11-28"


class GitHubAuthService:
    """Manages GitHub App authentication and installation tokens."""

    # In-memory token cache: installation_id -> (token_str, expire_timestamp_epoch)
    _token_cache: Dict[int, Tuple[str, float]] = {}

    def __init__(self, http_client: Optional[httpx.AsyncClient] = None):
        self._client = http_client

    def generate_app_jwt(self) -> str:
        """Generates a signed RS256 JWT representing the GitHub App itself.
        
        Valid for maximum 10 minutes as enforced by GitHub.
        """
        app_id = settings.GITHUB_APP_ID
        private_key = settings.get_github_private_key()

        if not app_id:
            raise AuthenticationError("GITHUB_APP_ID is not configured in application settings.")
        if not private_key:
            raise AuthenticationError("GitHub App private key (GITHUB_APP_PRIVATE_KEY or path) is not configured.")

        now = int(time.time())
        payload = {
            "iat": now - 60,  # 60s in the past to allow for clock drift
            "exp": now + (10 * 60),  # 10 minutes expiration
            "iss": str(app_id),
        }

        try:
            token = jwt.encode(payload, private_key, algorithm="RS256")
            return token
        except Exception as exc:
            logger.error(f"Failed to generate GitHub App RS256 JWT: {exc}")
            raise AuthenticationError(f"GitHub App cryptographic signing failed: {str(exc)}")

    async def get_installation_access_token(self, installation_id: int) -> str:
        """Exchanges App JWT for a short-lived repository installation access token.
        
        Reuses cached tokens if more than 3 minutes of validity remain.
        """
        now = time.time()
        cached = self._token_cache.get(installation_id)
        if cached:
            token_str, expire_ts = cached
            if expire_ts > now + 180:  # 3-minute safety buffer
                return token_str

        app_jwt = self.generate_app_jwt()
        url = f"{GITHUB_API_BASE}/app/installations/{installation_id}/access_tokens"
        headers = {
            "Authorization": f"Bearer {app_jwt}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "User-Agent": "OpenReviewAI-App/1.0",
        }

        client = self._client or httpx.AsyncClient(timeout=15.0)
        close_client = self._client is None

        try:
            response = await client.post(url, headers=headers)
            if response.status_code == 404:
                raise NotFoundError("GitHubInstallation", installation_id)
            if response.status_code == 403 or response.status_code == 429:
                reset_time = response.headers.get("X-RateLimit-Reset", "unknown")
                raise ConflictError(f"GitHub API rate limit exceeded. Reset at {reset_time}.")
            if response.status_code not in (200, 201):
                logger.error(f"GitHub token exchange failed [{response.status_code}]: {response.text}")
                raise AuthenticationError(f"Failed to obtain installation access token from GitHub: {response.text}")

            data = response.json()
            token_str = data["token"]
            expires_at_str = data.get("expires_at")
            if expires_at_str:
                expire_dt = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
                expire_ts = expire_dt.timestamp()
            else:
                expire_ts = now + 3600

            self._token_cache[installation_id] = (token_str, expire_ts)
            return token_str
        finally:
            if close_client:
                await client.aclose()

    async def get_authenticated_client(
        self,
        installation_id: Optional[int] = None,
        token: Optional[str] = None,
    ) -> httpx.AsyncClient:
        """Returns an AsyncClient pre-configured with installation or direct bearer token headers."""
        resolved_token = token or settings.GITHUB_TOKEN
        if not resolved_token and installation_id is not None:
            resolved_token = await self.get_installation_access_token(installation_id)

        if not resolved_token:
            raise AuthenticationError(
                "Neither a valid GitHub installation_id nor direct token/GITHUB_TOKEN was provided."
            )

        headers = {
            "Authorization": f"Bearer {resolved_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "User-Agent": "OpenReviewAI-App/1.0",
        }
        transport = getattr(self._client, "_transport", None) if self._client else None
        return httpx.AsyncClient(base_url=GITHUB_API_BASE, headers=headers, transport=transport, timeout=20.0)

    @classmethod
    def get_installation_url(cls, state: Optional[str] = None) -> str:
        """Generates the GitHub App installation URL for onboarding repositories."""
        slug = settings.GITHUB_APP_SLUG or "openreview-ai"
        url = f"https://github.com/apps/{slug}/installations/new"
        if state:
            url = f"{url}?state={state}"
        return url

    @classmethod
    def clear_cache(cls):
        """Clears cached installation tokens (useful for testing)."""
        cls._token_cache.clear()
