import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

db_url = 'postgresql+asyncpg://neondb_owner:npg_zAn51ZsorgDR@ep-aged-bird-beixkhpi.c-9.us-east-2.aws.neon.tech/neondb?ssl=require'

async def check():
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        u = (await conn.execute(text("SELECT id, email FROM users WHERE email = 'architect@openreview.ai';"))).fetchone()
        print('User:', u)
        if u:
            m = (await conn.execute(text(f"SELECT organization_id, role FROM organization_members WHERE user_id = '{u[0]}';"))).fetchall()
            print('Memberships:', m)
            
            repo = (await conn.execute(text("SELECT id, organization_id, name, owner FROM repositories WHERE name = 'OpenReview-AI-';"))).fetchall()
            print('Repo OpenReview-AI-:', repo)

if __name__ == '__main__':
    asyncio.run(check())
