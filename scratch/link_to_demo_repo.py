import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def link_to_demo_repo():
    db_url = 'postgresql+asyncpg://neondb_owner:npg_zAn51ZsorgDR@ep-aged-bird-beixkhpi.c-9.us-east-2.aws.neon.tech/neondb?ssl=require'
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        await conn.execute(text("UPDATE pull_requests SET repository_id = '35ac2f9e-d37f-42fa-9f80-b68694da68c9' WHERE id = '481c299c-b48a-4d10-b10a-26ef18a72b34';"))
        await conn.execute(text("UPDATE patches SET status = 'pending', branch_name = NULL, pr_url = NULL WHERE id = '559ad12b-e5e2-4b2f-948e-bd040f10c843';"))
        print('PR linked to gBashCode/demo and patch reset to pending!')

if __name__ == '__main__':
    asyncio.run(link_to_demo_repo())
