from dataclasses import dataclass
from dataclasses_json import dataclass_json
import disnake
from disnake.ext import commands
from dotenv import load_dotenv

import os
import json
from itertools import chain

# Load the token from the .env file
load_dotenv()
TOKEN = os.getenv("TEMP_CHANNELS_DISCORD_TOKEN")

TEST_GUILDS = os.getenv("TEST_GUILD")

bot = commands.InteractionBot(test_guilds=TEST_GUILDS)


@dataclass_json
@dataclass
class SpawnerChannel:
    """
    Represents a spawner channel.
    """

    guild_id: int
    category_id: int
    channel_id: int
    spawned_channels: list[int]
    spawned_counter: int = 0


class DataEncoder(json.JSONEncoder):
    """
    A custom JSON encoder for the SpawnerChannel class.
    """

    def default(self, obj):
        if isinstance(obj, SpawnerChannel):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)


DATA_FILE = "temp_vc_data.json"
# channel_id -> SpawnerChannel
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
    temp: dict[str, dict] = {}
    try:
        with open(DATA_FILE, "r") as f:
            temp = json.load(f)
    except OSError:
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)

    for k, v in temp.items():
        data[int(k)] = SpawnerChannel.from_dict(v) # type: ignore


@bot.slash_command(default_member_permissions=disnake.Permissions(administrator=True))
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

    spawner_channel = await category.create_voice_channel("➕ Create a new VC")
    await spawner_channel.edit(
        overwrites={
            inter.guild.default_role: disnake.PermissionOverwrite()
        }
    )

    data[spawner_channel.id] = SpawnerChannel(
        guild_id=inter.guild.id,
        category_id=category.id,
        channel_id=spawner_channel.id,
        spawned_channels=[],
    )

    save_data()

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
    # ignore bots
    if member.bot:
        return

    # if member left a spawned channel
    if before.channel and before.channel.id in list(
        chain.from_iterable([c.spawned_channels for c in data.values()])
    ):
        # if the member was the only one in the channel
        if len(before.channel.members) == 0:
            # delete the channel
            await before.channel.delete()
            # remove the channel from the list of spawned channels
            for c in data.values():
                if before.channel.id in c.spawned_channels:
                    c.spawned_channels.remove(before.channel.id)
                    if len(c.spawned_channels) == 0:
                        c.spawned_counter = 0
                    break

            save_data()

    # if member joined a spawner channel
    if after.channel and after.channel.id in data:
        # create a new channel
        assert after.channel.category
        data[after.channel.id].spawned_counter += 1
        channel = await after.channel.category.create_voice_channel(
            f"{after.channel.category.name} {data[after.channel.id].spawned_counter}",
        )

        # add the channel to the list of spawned channels
        data[after.channel.id].spawned_channels.append(channel.id)

        save_data()

        # move the member to the new channel
        await member.move_to(channel)



@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

    load_data()
    dels = []
    for k, v in data.items():
        if not bot.get_guild(v.guild_id).get_channel(v.channel_id): # type: ignore
            dels.append(k)
    for k in dels:
        del data[k]

    save_data()

bot.run(TOKEN)
