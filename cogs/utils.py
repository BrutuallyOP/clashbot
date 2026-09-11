from __future__ import annotations
from src.__version__ import *
import discord
from discord import app_commands
from discord.ext import commands
import logging
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from main import CustomBot


class Utility(commands.Cog):
    def __init__(self, bot: CustomBot):
        self.bot = bot

    @app_commands.command(name="ping", description="Returns the bot's gateway latency")
    async def ping(self, interaction: discord.Interaction):
        latency_ms = round(self.bot.latency * 1000, 2)
        await interaction.response.send_message(f"pong! ({latency_ms} ms)")

    @app_commands.command(
        name="version", description="Bot's version and What's New? info"
    )
    async def version(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"This instance of bot is running `v{VERSION_INFO}` !\n"
        )


async def setup(bot: CustomBot):
    await bot.add_cog(Utility(bot))
