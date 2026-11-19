"""GitHub Webhook Signature Verification, Deduplication, and Event Routing Service."""

import hashlib
import hmac
import json
import time
from typing import Any, Dict, Optional, Set, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.core.exceptions import AuthenticationError
from app.core.logging import get_logger
from app.github.models import GitHubInstallation
from app.organizations.models import Organization
from app.repositories.models import Repository

logger = get_logger("openreview.github.webhook")
settings = get_settings()


class GitHubWebhookService:
    """Validates GitHub webhook signatures and idempotently routes incoming events."""

    # LRU/TTL cache of processed delivery IDs: delivery_id -> timestamp
    _processed_deliveries: Dict[str, float] = {}

    def __init__(self, session: AsyncSession):
        self.session = session

    @classmethod
    def verify_signature(cls, payload_body: bytes, signature_header: Optional[str]) -> bool:
        """Verifies HMAC-SHA256 signature using timing-safe comparison."""
        webhook_secret = settings.GITHUB_WEBHOOK_SECRET
        if not webhook_secret:
            logger.warning("GITHUB_WEBHOOK_SECRET is not configured; skipping signature verification.")
            return True

        if not signature_header or not signature_header.startswith("sha256="):
            return False

        expected_sig = "sha256=" + hmac.new(
            webhook_secret.encode("utf-8"),
            payload_body,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected_sig, signature_header)

    @classmethod
    def is_duplicate(cls, delivery_id: Optional[str]) -> bool:
        """Checks if this delivery has already been processed within the last 24 hours."""
        if not delivery_id:
            return False

        now = time.time()
        # Clean entries older than 24h
        cls._processed_deliveries = {
            d_id: ts for d_id, ts in cls._processed_deliveries.items()
            if now - ts < 86400
        }

        if delivery_id in cls._processed_deliveries:
            return True

        cls._processed_deliveries[delivery_id] = now
        return False

    async def handle_installation_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handles GitHub App installation creation or deletion events."""
        action = payload.get("action")
        installation_data = payload.get("installation", {})
        installation_id = installation_data.get("id")
        account = installation_data.get("account", {})
        account_login = account.get("login", "unknown")
        account_type = account.get("type", "Organization")

        if not installation_id:
            return {"status": "ignored", "reason": "Missing installation_id"}

        if action == "created":
            # Link to default organization or find by slug
            stmt_org = select(Organization).order_by(Organization.created_at)
            org = (await self.session.execute(stmt_org)).scalars().first()
            if not org:
                org = Organization(
                    name=account_login,
                    slug=account_login.lower(),
                    plan="team",
                )
                self.session.add(org)
                await self.session.flush()

            stmt_inst = select(GitHubInstallation).where(GitHubInstallation.installation_id == installation_id)
            inst = (await self.session.execute(stmt_inst)).scalar_one_or_none()
            if not inst:
                inst = GitHubInstallation(
                    organization_id=org.id,
                    installation_id=installation_id,
                    account_login=account_login,
                    account_type=account_type,
                    permissions_json=json.dumps(installation_data.get("permissions", {})),
                )
                self.session.add(inst)
            else:
                inst.account_login = account_login
                inst.permissions_json = json.dumps(installation_data.get("permissions", {}))

            await self.session.commit()
            return {"status": "created", "installation_id": installation_id}

        elif action == "deleted":
            stmt_inst = select(GitHubInstallation).where(GitHubInstallation.installation_id == installation_id)
            inst = (await self.session.execute(stmt_inst)).scalar_one_or_none()
            if inst:
                await self.session.delete(inst)
                await self.session.commit()
            return {"status": "deleted", "installation_id": installation_id}

        return {"status": "acknowledged", "action": action}

    async def handle_installation_repositories_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handles repositories added or removed from an installation."""
        action = payload.get("action")
        installation_data = payload.get("installation", {})
        installation_id = installation_data.get("id")

        if not installation_id:
            return {"status": "ignored", "reason": "Missing installation_id"}

        stmt_inst = select(GitHubInstallation).where(GitHubInstallation.installation_id == installation_id)
        inst = (await self.session.execute(stmt_inst)).scalar_one_or_none()
        if not inst:
            return {"status": "ignored", "reason": f"Installation {installation_id} not registered"}

        if action == "added":
            added_repos = payload.get("repositories_added", [])
            for r in added_repos:
                stmt_r = select(Repository).where(Repository.github_repo_id == r["id"])
                existing = (await self.session.execute(stmt_r)).scalar_one_or_none()
                owner, name = r["full_name"].split("/", 1)
                if existing:
                    existing.installation_id = inst.id
                    existing.is_active = True
                else:
                    new_repo = Repository(
                        organization_id=inst.organization_id,
                        installation_id=inst.id,
                        github_repo_id=r["id"],
                        owner=owner,
                        name=name,
                        full_name=r["full_name"],
                        default_branch="main",
                        is_active=True,
                    )
                    self.session.add(new_repo)

            await self.session.commit()
            return {"status": "repositories_added", "count": len(added_repos)}

        elif action == "removed":
            removed_repos = payload.get("repositories_removed", [])
            for r in removed_repos:
                stmt_r = select(Repository).where(Repository.github_repo_id == r["id"])
                existing = (await self.session.execute(stmt_r)).scalar_one_or_none()
                if existing:
                    existing.is_active = False

            await self.session.commit()
            return {"status": "repositories_removed", "count": len(removed_repos)}

        return {"status": "acknowledged", "action": action}
