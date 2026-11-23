import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def get_gbash_repos():
    db_url = 'postgresql+asyncpg://neondb_owner:npg_zAn51ZsorgDR@ep-aged-bird-beixkhpi.c-9.us-east-2.aws.neon.tech/neondb?ssl=require'
    engine = create_async_engine(db_url)
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT id, full_name, organization_id FROM repositories WHERE owner = 'gBashCode';"))
        for row in res.fetchall():
            print(row[0], row[1], row[2])

if __name__ == '__main__':
    asyncio.run(get_gbash_repos())
