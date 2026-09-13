import aiosqlite
from contextlib import asynccontextmanager
import discord
from pathlib import Path

DATABASE_PATH = Path("./data/links.db")


@asynccontextmanager
async def connect():
    async with aiosqlite.connect(DATABASE_PATH) as connection:
        await connection.execute("PRAGMA busy_timeout=5000")
        yield connection


async def initialize_database():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    async with connect() as connection:
        await connection.execute("PRAGMA journal_mode=WAL")
        await connection.execute("PRAGMA foreign_keys=ON")
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS links (
                message_id INTEGER PRIMARY KEY,
                channel_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                count INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """)
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS tracker (
                tracker_id INTEGER PRIMARY KEY,
                message_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                UNIQUE (message_id, user_id)
                FOREIGN KEY (message_id) REFERENCES links(message_id)
            )
            """)

        await connection.commit()


async def create_link(message_id: int, channel_id: int, url: str) -> None:
    async with connect() as connection:
        await connection.execute(
            """
            INSERT INTO links (message_id, channel_id, url)
            VALUES (?, ?, ?)
            """,
            (message_id, channel_id, url),
        )
        await connection.commit()


async def record_download(interaction: discord.Interaction) -> tuple[int, str] | None:
    async with connect() as connection:
        count = await connection.execute(
            """
            INSERT OR IGNORE INTO tracker (message_id, user_id)
            VALUES (?, ?)
            """,
            (interaction.message.id, interaction.user.id),
        )

        if count.rowcount == 1:  # user added to table tracker
            async with connection.execute(
                """
                UPDATE links
                SET count = count + 1
                WHERE message_id = ?
                RETURNING count, url
                """,
                (interaction.message.id,),
            ) as cursor:
                row = await cursor.fetchone()

            if row is None:
                return None

            await connection.commit()

        else:  # user already present in table tracker
            async with connection.execute(
                """
                SELECT count, url FROM links
                WHERE message_id = ?
                """,
                (interaction.message.id,),
            ) as cursor:
                row = await cursor.fetchone()

            if row is None:
                return None

            await connection.commit()

    return row[0], row[1]


async def send_downloads(interaction: discord.Interaction):
    download_list = []
    async with connect() as connection:
        async with connection.execute(
            """
            SELECT user_id FROM tracker
            WHERE message_id = ?
            """,
            (interaction.message.id,),
        ) as cursor:
            async for row in cursor:
                download_list.append(str(row[0]))

    return download_list
