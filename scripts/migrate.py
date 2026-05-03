"""Pre-deploy migration script for Render.

Runs the idempotent DDL against the DATABASE_URL before the app starts.
Safe to re-run on every deploy — all statements use CREATE TABLE IF NOT EXISTS.
"""

from __future__ import annotations

import asyncio
import os

import asyncpg

from kinetic.db.postgres_client import _DDL  # type: ignore[import-untyped]


async def main() -> None:
    url = os.environ["DATABASE_URL"]
    conn: asyncpg.Connection = await asyncpg.connect(url)
    try:
        await conn.execute(_DDL)
        print("Migration complete.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
