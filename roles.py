import disnake
from disnake.ext import commands
from dotenv import load_dotenv

import os
import time

from helpers import error, log

# Load the token from the .env file
load_dotenv()
TOKEN = os.getenv("ROLES_DISCORD_TOKEN")


TEST_GUILDS = os.getenv("TEST_GUILD")

# TODO: make this configurable in the slash command
VOUCH_FOR_ROLE_DEFAULT = 1152024701808418827
VOUCHES_REQUIRED = 3

bot = commands.InteractionBot(test_guilds=TEST_GUILDS)

# dict structure: { user_id: ([user_vouching_id], [user_not_vouching_id]) }
vouch_data: dict[int, tuple[list[int], list[int]]] = {}


def vouches(user_id: int):
    """
    Returns how many vouches the user has.
    """
    return (len(vouch_data[user_id][0])) - (len(vouch_data[user_id][1]))


@bot.slash_command()
async def vouch(
    inter: disnake.ApplicationCommandInteraction,
    user: disnake.Member,
    # role: disnake.Role | None = None,
):
    """
    Vouch for a user to get a role. This is a public message.

    Parameters
    ----------
    user : disnake.Member
        The user to vouch for
    """
    assert inter.guild
    role = inter.guild.get_role(VOUCH_FOR_ROLE_DEFAULT)
    assert role

    if role not in inter.author.roles:  # type: ignore
        await inter.send("You can't vouch for a role you don't have!", ephemeral=True)
        return

    if role in user.roles:
        await inter.send("This user already has this role!", ephemeral=True)
        return

    if vouch_data.get(user.id) is None:
        vouch_data[user.id] = ([], [])

    if inter.author.id in vouch_data[user.id][0]:
        await inter.send("You already vouched for this user!", ephemeral=True)
        return

    if inter.author.id in vouch_data[user.id][1]:
        vouch_data[user.id][1].remove(inter.author.id)

    vouch_data[user.id][0].append(inter.author.id)

    await inter.send(
        f"{inter.author.display_name} vouched for {user.display_name} to get the {role.name} role. {VOUCHES_REQUIRED - vouches(user.id)} more vouches are required."
    )

    if vouches(user.id) >= VOUCHES_REQUIRED:
        # wait for 60 seconds to see if the user gets unvouched
        await inter.send(
            f"Waiting a minute to give {user.display_name} the {role.name} role..."
        )
        time.sleep(60)
        if vouches(user.id) >= VOUCHES_REQUIRED and role not in user.roles:
            await user.add_roles(role)
            await inter.send(f"{user.display_name} got the {role.name} role!")


@bot.slash_command()
async def unvouch(
    inter: disnake.ApplicationCommandInteraction,
    user: disnake.Member,
    # role: disnake.Role | None = None,
):
    """
    Vouch for a user to NOT get a role. This is a public message.

    Parameters
    ----------
    user : disnake.Member
        The user to vouch against
    """
    assert inter.guild
    role = inter.guild.get_role(VOUCH_FOR_ROLE_DEFAULT)
    assert role

    if role not in inter.author.roles:  # type: ignore
        await inter.send("You can't vouch for a role you don't have!", ephemeral=True)
        return

    if role in user.roles:
        await inter.send("This user already has this role!", ephemeral=True)
        return

    if vouch_data.get(user.id) is None:
        vouch_data[user.id] = ([], [])

    if inter.author.id in vouch_data[user.id][1]:
        await inter.send("You already vouched for this user!", ephemeral=True)
        return

    if inter.author.id in vouch_data[user.id][0]:
        vouch_data[user.id][0].remove(inter.author.id)

    vouch_data[user.id][1].append(inter.author.id)

    await inter.send(
        f"{inter.author.display_name} doesn't want {user.display_name} to get the {role.name} role. "
    )


@bot.slash_command(default_member_permissions=disnake.Permissions(administrator=True))
async def addnewrolebutton(
    inter: disnake.ApplicationCommandInteraction,
    in_channel: disnake.TextChannel,
    label: str,
    description: str,
    role: disnake.Role,
    emoji: str | None = None,
):
    """
    Create a new role button.

    Parameters
    ----------
    in_channel : disnake.TextChannel
        The channel to send the button in
    label : str
        The label of the button
    description : str
        The description of the button
    role : disnake.Role
        The role to add/remove when the button is clicked
    emoji : str, optional
        The emoji to use for the button, by default None
    """
    # parse emoji from string, create button
    parsed_emoji = disnake.PartialEmoji.from_str(emoji) if emoji else None

    components = []
    embed = disnake.Embed(
        title=f"{role.name}",
        description=description,
        color=0x00FF00,
    )

    components.append(
        disnake.ui.Button(
            label=label,
            custom_id=f"role_button_{role.id}",
            emoji=parsed_emoji,
        )
    )

    assert inter.guild_id
    chan = bot.get_channel(in_channel.id)
    assert type(chan) is disnake.TextChannel

    await chan.send(
        embed=embed,
        components=components,
    )

    await inter.response.send_message(
        "Button created!",
        ephemeral=True,
        delete_after=5,
    )


@bot.listen()
async def on_button_click(inter: disnake.MessageInteraction):
    if type(inter.author) is not disnake.Member:
        await error(
            inter, message="You must be a member of this server to use this button."
        )
        return

    assert inter.guild_id and inter.guild
    assert inter.component.custom_id
    if inter.component.custom_id.startswith("role_button_"):
        role_id = int(inter.component.custom_id.split("_")[2])
        role = inter.guild.get_role(role_id)
        assert role

        if role in inter.author.roles:
            await inter.author.remove_roles(role)
            await inter.response.send_message(
                f"Removed the {role.name} role from you!",
                ephemeral=True,
                delete_after=5,
            )
        else:
            await inter.author.add_roles(role)
            await inter.response.send_message(
                f"Added the {role.name} role to you!",
                ephemeral=True,
                delete_after=5,
            )


@bot.listen()
async def on_ready():
    log(f"Logged in as {bot.user} ({bot.user.id})")
    log(f"Connected to {len(bot.guilds)} guilds:")
    for guild in bot.guilds:
        log(f" - {guild.name} ({guild.id})")


bot.run(TOKEN)
