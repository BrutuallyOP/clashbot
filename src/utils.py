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


class BaseUi(discord.ui.View):
    def __init__(self, baseurl):
        super().__init__()

        self.add_item(
            discord.ui.Button(
                label="🔗Link", style=discord.ButtonStyle.primary, url=baseurl
            )
        )

        self.add_item(
            discord.ui.Button(
                label="{❓} Downloads",
                style=discord.ButtonStyle.secondary,
                custom_id="count",
                disabled=True,
            )
        )
