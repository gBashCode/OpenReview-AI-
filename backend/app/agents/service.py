"""AI Agent and Discussion Service."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.models import AgentDiscussion, ReviewAgent
from app.agents.schemas import AgentDiscussionCreate, ReviewAgentCreate
from app.core.exceptions import NotFoundError
from app.reviews.models import Review


class AgentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_agents(self, review_id: str) -> List[ReviewAgent]:
        """Lists all agents assigned to a review."""
        stmt = select(ReviewAgent).where(ReviewAgent.review_id == review_id).order_by(ReviewAgent.agent_name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_discussions(
        self,
        review_id: str,
        finding_id: Optional[str] = None,
    ) -> List[AgentDiscussion]:
        """Lists inter-agent debates and consensus messages for a review."""
        stmt = select(AgentDiscussion).where(AgentDiscussion.review_id == review_id)
        if finding_id:
            stmt = stmt.where(AgentDiscussion.finding_id == finding_id)
        stmt = stmt.order_by(AgentDiscussion.created_at)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add_discussion_message(self, data: AgentDiscussionCreate) -> AgentDiscussion:
        """Adds a message/critique/verification to the agent conference."""
        stmt_rev = select(Review).where(Review.id == data.review_id)
        review = (await self.session.execute(stmt_rev)).scalar_one_or_none()
        if not review:
            raise NotFoundError("Review", data.review_id)

        msg = AgentDiscussion(
            review_id=data.review_id,
            finding_id=data.finding_id,
            agent_name=data.agent_name,
            message_type=data.message_type,
            content=data.content,
            file_context=data.file_context,
            is_verified=data.is_verified,
        )
        self.session.add(msg)
        await self.session.commit()
        await self.session.refresh(msg)
        return msg
