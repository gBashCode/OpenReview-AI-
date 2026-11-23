import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

db_url = 'postgresql+asyncpg://neondb_owner:npg_zAn51ZsorgDR@ep-aged-bird-beixkhpi.c-9.us-east-2.aws.neon.tech/neondb?ssl=require'

async def clean():
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        await conn.execute(text("""
            UPDATE patches 
            SET status = 'applied', 
                branch_name = 'autofix/patch-559ad12b', 
                rejection_reason = NULL, 
                pr_url = 'https://github.com/gBashCode/OpenReview-AI-/pull/7' 
            WHERE id = '559ad12b-e5e2-4b2f-948e-bd040f10c843';
        """))
        print('Cleaned patch 559ad12b!')

if __name__ == '__main__':
    asyncio.run(clean())
