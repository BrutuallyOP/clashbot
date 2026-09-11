import aiosqlite
from pathlib import Path

DATABASE_PATH = Path("./data/links.db")


async def connect() -> aiosqlite.Connection:
    connection = await aiosqlite.connect(DATABASE_PATH)
    await connection.execute("PRAGMA journal_mode=WAL")
    await connection.execute("PRAGMA busy_timeout=5000")
    return connection


async def initialize_database():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    async with await connect() as connection:
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS links (
                message_id INTEGER PRIMARY KEY,
                channel_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                count INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """)

        await connection.commit()


async def create_link(message_id: int, channel_id: int, url: str) -> None:
    async with await connect() as connection:
        await connection.execute(
            """
            INSERT INTO links (message_id, channel_id, url)
            VALUES (?, ?, ?)
            """,
            (message_id, channel_id, url),
        )
        await connection.commit()


async def record_download(message_id: int) -> tuple[int, str] | None:
    async with await connect() as connection:
        async with connection.execute(
            """
            UPDATE links
            SET count = count + 1
            WHERE message_id = ?
            RETURNING count, url
            """,
            (message_id,),
        ) as cursor:
            row = await cursor.fetchone()

        if row is None:
            return None

        await connection.commit()

    return row[0], row[1]
