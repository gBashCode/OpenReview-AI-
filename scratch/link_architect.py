import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import uuid

db_url = 'postgresql+asyncpg://neondb_owner:npg_zAn51ZsorgDR@ep-aged-bird-beixkhpi.c-9.us-east-2.aws.neon.tech/neondb?ssl=require'

async def link_architect():
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        # Add architect user to 221069d6-37fb-421f-8d2a-4b22eef2cf6d
        await conn.execute(text("""
            INSERT INTO organization_members (id, organization_id, user_id, role, created_at, updated_at)
            VALUES (:id, '221069d6-37fb-421f-8d2a-4b22eef2cf6d', '3fdafef2-b469-4099-8506-73853860b4dc', 'admin', NOW(), NOW())
            ON CONFLICT DO NOTHING;
        """), {"id": str(uuid.uuid4())})
        print('Linked architect user to organization 221069d6-37fb-421f-8d2a-4b22eef2cf6d')

if __name__ == '__main__':
    asyncio.run(link_architect())
