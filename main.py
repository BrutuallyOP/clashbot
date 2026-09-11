from aiohttp import ClientConnectorError
from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.ext import commands
from src.utils import BaseUi
import logging
from logging.handlers import RotatingFileHandler
import os

load_dotenv("./actual.env")

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s : %(message)s")
file_handler = RotatingFileHandler(
    filename="bot.log", maxBytes=8 * 1024 * 1024, backupCount=3, encoding="utf-8"
)
file_handler.setFormatter(formatter)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("werkzeug").setLevel(logging.WARNING)
logging.getLogger("discord.client").setLevel(logging.WARNING)


class DiscordConnectionTracebackFilter(logging.Filter):
    def filter(self, record):
        if record.name != "discord.client":
            return True

        if not record.exc_info:
            return True

        exc = record.exc_info[1]
        if isinstance(exc, ClientConnectorError):
            record.exc_info = None
            record.exc_text = None

        return True


for handler in logger.handlers:
    handler.addFilter(DiscordConnectionTracebackFilter())


logger.info("Startin up...")


class CustomBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.messages = True
        game_activity = discord.Game(name="Clashing with queen...😏")

        super().__init__(
            command_prefix="!",
            case_insensitive=True,
            intents=intents,
            activity=game_activity,
            status=discord.Status.online,
        )
        self.tree.error(self.on_app_command_error)

    async def on_ready(self):
        logger.info(f"Logged in successfully as {self.user} (ID: {self.user.id})")

    # async def setup_hook(self):
    #     for filename in os.listdir("./cogs"):
    #         if filename.endswith(".py") and not filename.startswith("__"):
    #             await self.load_extension(f"cogs.{filename[:-3]}")
    #     logger.info("Syncing slash commands...")
    #     synced = await self.tree.sync()
    #     logger.info(f"Synced {len(synced)} command(s).")

    async def on_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        """ "Base error handler"""
        original_err = getattr(error, "original", error)
        command_name = (
            f"/{interaction.command.name}" if interaction.command else "Unknown Command"
        )
        if isinstance(error, app_commands.MissingPermissions):
            msg = ":x: You do not have permission to use this command."
            logger.warning(
                f"User {interaction.user} missing permissions for {command_name}: {error.missing_permissions}"
            )

        elif isinstance(error, app_commands.NoPrivateMessage):
            msg = ":x: This command can only be used within a server."
            logger.warning(
                f"User {interaction.user} attempted server-only command {command_name} in DMs"
            )

        elif isinstance(error, app_commands.BotMissingPermissions):
            msg = f":x: I am missing permissions to run this command: `{', '.join(error.missing_permissions)}`"
            logger.warning(
                f"Bot missing permissions for {command_name} in channel #{interaction.channel}: {error.missing_permissions}"
            )

        else:
            msg = f"Oops! An unexpected error occurred: {original_err}"
            logger.error(
                f"Unhandled error in {command_name}: {original_err}",
                exc_info=original_err,
            )

        try:
            if interaction.response.is_done():
                await interaction.edit_original_response(content=msg)
            else:
                await interaction.response.send_message(content=msg, ephemeral=True)
        except discord.HTTPException as e:
            logger.warning(
                f"Could not send error response to user for {command_name}: {e}"
            )


bot = CustomBot()


@bot.event
async def on_message(message: discord.Message):
    if message.guild and not message.author.bot and message.content:
        content = message.content.strip()
        link = None
        subcontent = content.split()
        for part in subcontent:
            if part.startswith(
                (
                    "https://link.clashofclans.com/en?action=OpenLayout",
                    "https://link.clashofclans.com/en/?action=OpenLayout",
                )
            ):
                link = subcontent.pop(subcontent.index(part))
                break

        if not link:
            return

        media = message.attachments
        files = []
        for attachment in media:
            file = await attachment.to_file()
            files.append(file)

        content = " ".join(subcontent)
        try:
            await message.channel.send(content=content, files=files, view=BaseUi(link))
        except Exception as e:
            logger.warning("Excepting in sending message", exc_info=e)
            return

        try:
            await message.delete()
        except discord.NotFound:
            logger.warning("Message already deleted")
        except discord.Forbidden:
            logger.warning(f"No permission to delete message {message.id}")
        except discord.HTTPException as e:
            logger.warning(f"Failed to delete message {message.id}{e}")

bot.run((os.getenv("DISCORD_SECRET")))