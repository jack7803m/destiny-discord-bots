from dataclasses import dataclass
import disnake
from disnake.ext import commands
from dotenv import load_dotenv

import os
import sys
import threading
import json

from helpers import error, generate_embed_and_components, ButtonData

# Load the token from the .env file
load_dotenv()
TOKEN = os.getenv("TEMP_VC_DISCORD_TOKEN")

TEST_GUILDS = None
TEST_GUILDS = [846119474025594900]

bot = commands.InteractionBot(test_guilds=TEST_GUILDS)

@dataclass
class SpawnerChannel:
    """
    Represents a spawner channel.
    """
    guild_id: int
    category_id: int
    channel_id: int
    spawned_channels: list[int]

class DataEncoder(json.JSONEncoder):
    """
    A custom JSON encoder for the SpawnerChannel class.
    """
    def default(self, obj):
        if isinstance(obj, SpawnerChannel):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)

DATA_FILE = "temp_vc_data.json"
data: dict[int, SpawnerChannel] = {}

def save_data() -> None:
    """
    Serializes and saves the data to disk.
    """
    global data
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, cls=DataEncoder)


def load_data() -> None:
    """
    Deserializes and loads saved data from disk.
    """
    global data
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    

# data[846119474025594900] = SpawnerChannel(
#     guild_id=846119474025594900,
#     category_id=846119474025594900,
#     channel_id=846119474025594900,
#     spawned_channels=[2938293482934, 2938293482934, 2938293482934],
# )

# data[9283429348] = SpawnerChannel(
#     guild_id=9283429348,
#     category_id=9283429348,
#     channel_id=9283429348,
#     spawned_channels=[2938293482934, 2938293482934, 2938293482934],
# )

# save_data()
# load_data()

# import pprint
# pprint.pprint(data)

# exit()


@bot.slash_command()
async def createtempcategory(
    inter: disnake.ApplicationCommandInteraction,
    name: str,
):
    """
    Creates a category for temporary VCs and adds the ability to create them.

    Parameters
    ----------
    name : str
        The name of the category to create
    """

    # create new category
    assert inter.guild
    category = await inter.guild.create_category(name=name)

    spawner_channel = await category.create_voice_channel("➕ Create a new temporary VC")
    await spawner_channel.edit(
        overwrites={
            inter.guild.default_role: disnake.PermissionOverwrite(connect=False)
        }
    )

    await inter.response.send_message(
        f"Created category {category.mention} with spawner channel {spawner_channel.mention}.",
        ephemeral=True,
    )

@bot.event
async def on_voice_state_update(
    member: disnake.Member,
    before: disnake.VoiceState,
    after: disnake.VoiceState,
):
    """
    Handles the creation and deletion of temporary VCs.
    """
    

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

    await load_data()


bot.run(TOKEN)