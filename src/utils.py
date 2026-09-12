import discord
import logging
import os

logger = logging.getLogger(__name__)
APPROVED_FILE = "./data/approved.txt"
os.makedirs(os.path.dirname(APPROVED_FILE), exist_ok=True)

try:
    with open(APPROVED_FILE, "r") as f:
        approved_users = {line.strip() for line in f if line.strip()}
except FileNotFoundError:
    approved_users = set()


def is_user_approved(user_id: str) -> bool:
    return user_id in approved_users


def whitelist_user(user_id: str) -> bool:
    if is_user_approved(user_id):
        return False

    with open(APPROVED_FILE, "a") as f:
        f.write(f"{user_id}\n")

    approved_users.add(user_id)

    return True


def remove_whitelisted_user(user_id: str) -> bool:
    if not is_user_approved(user_id):
        return False

    approved_users.discard(user_id)

    with open(APPROVED_FILE, "w") as f:
        for user in approved_users:
            f.write(f"{user}\n")

    return True


class LinkUi(discord.ui.View):
    def __init__(self, link: str):
        super().__init__(timeout=None)

        final_link_button = discord.ui.Button(
            label="🔗 Link",
            style=discord.ButtonStyle.link,
            url=link,
        )
        
        self.add_item(final_link_button)


class BaseUi(discord.ui.View):
    def __init__(self, downloads: int = 0):
        super().__init__(timeout=None)

        self.downloads = downloads

        link_button = discord.ui.Button(
            label="📥 Get Link",
            style=discord.ButtonStyle.primary,
            custom_id="download_link",
        )
        link_button.callback = self.send_link
        self.add_item(link_button)

        self.add_item(
            discord.ui.Button(
                label=f"📈 {downloads} Downloads",
                style=discord.ButtonStyle.secondary,
                custom_id="download_count",
                disabled=True,
            )
        )

    async def send_link(self, interaction: discord.Interaction):
        from src import database as db

        # ACK Discord immediately
        await interaction.response.defer(ephemeral=True)

        result = await db.record_download(interaction.message.id)

        if result is None:
            await interaction.followup.send(
                "This link is no longer available.",
                ephemeral=True,
            )
            return

        count, url = result

        await interaction.followup.send(
            ephemeral=True,
            view=LinkUi(url),
            suppress_embeds=True            
        )

        await interaction.message.edit(view=BaseUi(count))
