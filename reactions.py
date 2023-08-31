import disnake
from disnake.ext import commands
from dotenv import load_dotenv

import os
import sys
import threading

from helpers import error, generate_embed_and_components, ButtonData

# Load the token from the .env file
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# The test guild ID (only for development)
TEST_GUILDS = None
TEST_GUILDS = [846119474025594900]

bot = commands.InteractionBot(test_guilds=TEST_GUILDS)
channel_and_message_lock = threading.Lock()
message_buttons_lock = threading.Lock()
button_data_lock = threading.Lock()

# dict structure: { guild_id: { channel_id: message_id } }
# keeps track of the message ID for each channel, persists across bot restarts
channel_and_message: dict[int, dict[int, int]] = {}

# dict structure: { message_id: [button_id] }
# used to keep track of which buttons are on which message
message_buttons: dict[int, list[str]] = {}

# dict structure: { button_id: buttonData }
# used to keep track of each button's data
button_data: dict[str, ButtonData] = {}


# TODO: ensure no duplicate labels
@bot.slash_command()
async def addnewrolebutton(
    inter: disnake.ApplicationCommandInteraction,
    in_channel: disnake.TextChannel,
    label: str,
    role: disnake.Role,
    emoji: str | None = None,
    description: str | None = None,
):
    """
    Create a new role button.
    """
    # parse emoji from string, create button
    parsed_emoji = disnake.PartialEmoji.from_str(emoji) if emoji else None
    button = disnake.ui.Button(label=label, emoji=parsed_emoji)

    # lock button data dict, add button data
    assert inter.guild_id
    assert button.custom_id
    with button_data_lock:
        if button_data.get(button.custom_id) is None:
            button_data[button.custom_id] = ButtonData(
                label=label,
                roles=[role],
                custom_id=button.custom_id,
                emoji=parsed_emoji,
                description=description,
            )

    # lock message buttons dict, add button to message or create new message
    assert inter.guild
    chan = inter.guild.get_channel(in_channel.id)
    assert type(chan) is disnake.TextChannel

    message_id = None
    with channel_and_message_lock:
        if channel_and_message.get(inter.guild_id) is None:
            channel_and_message[inter.guild_id] = {}

        if channel_and_message[inter.guild_id].get(chan.id) is not None:
            message_id = channel_and_message[inter.guild_id][chan.id]

    with message_buttons_lock:
        # if we already sent a message in this channel, edit it
        if message_id is not None and message_buttons.get(message_id):
            message_buttons[message_id].append(button.custom_id)

            buts = [button_data[but] for but in message_buttons[message_id]]
            embed, components = generate_embed_and_components(buts)

            await (await chan.fetch_message(message_id)).edit(
                embed=embed, components=components
            )

        # otherwise, send a new message
        else:
            embed, components = generate_embed_and_components(
                [button_data[button.custom_id]]
            )
            message = await chan.send(
                embed=embed,
                components=components,
            )

            # lock channel and message dict, add message ID
            with channel_and_message_lock:
                channel_and_message[inter.guild_id][chan.id] = message.id

            message_buttons[message.id] = [button.custom_id]

    await inter.response.send_message(
        "Button created!",
        ephemeral=True,
    )


@bot.slash_command()
async def deleterolebutton(
    inter: disnake.ApplicationCommandInteraction,
    in_channel: disnake.TextChannel,
):
    """
    Sends a selection menu to delete a role button.
    """
    assert inter.guild_id
    assert inter.guild

    # lock channel and message dict, get message ID
    chan = inter.guild.get_channel(in_channel.id)
    assert type(chan) is disnake.TextChannel

    message_id = None
    with channel_and_message_lock:
        if channel_and_message.get(inter.guild_id) is None:
            channel_and_message[inter.guild_id] = {}

        if channel_and_message[inter.guild_id].get(chan.id) is not None:
            message_id = channel_and_message[inter.guild_id][chan.id]

    # if we have a message ID, send a selection menu
    if message_id is not None:
        buttons = [
            disnake.SelectOption(
                label=f"{button_data[button_id].label} - @{inter.guild.get_role(button_data[button_id].roles[0].id).name}",  # type: ignore
                value=button_id,
                description=button_data[button_id].description,
                emoji=button_data[button_id].emoji,
            )
            for button_id in message_buttons[message_id]
        ]

        select = disnake.ui.Select(
            placeholder="Select a button to delete",
            options=buttons,
            custom_id="delete_role_button",
        )

        await inter.response.send_message(
            "Select a button to delete",
            components=[select],
            ephemeral=True,
        )

    # otherwise, send an error
    else:
        await inter.send(
            "There are no buttons defined in this channel!", ephemeral=True
        )


@bot.listen()
async def on_button_click(inter: disnake.MessageInteraction):
    if type(inter.author) is not disnake.Member:
        await error(
            inter, message="You must be a member of this server to use this button."
        ) 
        return

    assert inter.guild_id
    if inter.component.custom_id in button_data:
        for role in button_data[inter.component.custom_id].roles:
            if role in inter.author.roles:
                print(f"Removed role {role.name} from {inter.author.name}")
                await inter.author.remove_roles(role)
            else:
                print(f"Added role {role.name} to {inter.author.name}")
                await inter.author.add_roles(role)
        await inter.response.defer()
    else:
        await error(inter, message="This button is not registered.")


@bot.listen()
async def on_dropdown(inter: disnake.MessageInteraction):
    if type(inter.author) is not disnake.Member:
        await error(
            inter, message="You must be a member of this server to use this button."
        )
        return

    # TODO: extract func recompute button message
    # TODO: enforce persistency via file
    if inter.component.custom_id == "delete_role_button":
        assert inter.values
        button_to_delete = inter.values[0]

        # lock button data dict, remove button data
        with button_data_lock:
            if button_data.get(button_to_delete) is not None:
                del button_data[button_to_delete]

        # lock message buttons dict, remove button from message
        assert inter.guild_id
        assert inter.guild
        chan = inter.guild.get_channel(inter.channel.id)
        assert type(chan) is disnake.TextChannel

        message_id = None
        with channel_and_message_lock:
            if channel_and_message.get(inter.guild_id) is not None:
                if channel_and_message[inter.guild_id].get(chan.id) is not None:
                    message_id = channel_and_message[inter.guild_id][chan.id]

        with message_buttons_lock:
            if message_id is not None and message_buttons.get(message_id):
                message_buttons[message_id].remove(button_to_delete)

                buts = [button_data[but] for but in message_buttons[message_id]]
                embed, components = generate_embed_and_components(buts)

                await (await chan.fetch_message(message_id)).edit(
                    embed=embed, components=components
                )

        await inter.response.send_message(
            "Button deleted!",
            ephemeral=True,
        )


bot.run(TOKEN)
