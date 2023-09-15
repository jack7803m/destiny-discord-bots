import disnake
from disnake.ext import commands
from dotenv import load_dotenv

import random
import time
import os
from helpers import log

# Load the token from the .env file
load_dotenv()
TOKEN = os.getenv("ROLES_DISCORD_TOKEN")

# The test guild ID (only for development)
TEST_GUILDS = None
TEST_GUILDS = [1146525933965160479]

TARGET_MEMBER = 358609857646952448

intents = disnake.Intents.default()
intents.members = True
intents.presences = True
intents.message_content = True

bot = commands.InteractionBot(test_guilds=TEST_GUILDS, intents=intents)

def create_embed() -> disnake.Embed:
    embed = disnake.Embed(title="Vex Incursion Incoming!",
                      colour=0xb6dd62)

    embed.add_field(name="Incursion starts in",
                    value=f"<t:{int(time.time()) + 285}:R>",
                    inline=False)
    embed.add_field(name="Location",
                    value="Zephyr Concourse",
                    inline=False)
    embed.add_field(name="Support me and help me keep the bot running!",
                    value="https://ko-fi.com/buuz135",
                    inline=False)

    embed.set_thumbnail(url="https://media.discordapp.net/attachments/1100800542978097253/1104429284430450758/02E4-01FA.png")

    embed.set_footer(text="Vex Network",
                    icon_url="https://media.discordapp.net/attachments/1100800542978097253/1104424186895671387/0332-07FE.png")

    return embed

@bot.event
async def on_presence_update(before: disnake.Member, after: disnake.Member):
    if after.id == TARGET_MEMBER and before.guild.id == TEST_GUILDS[0] and after.guild.id == TEST_GUILDS[0]:
        log(f"{after.display_name} is now {after.status} from {before.status} with {before._client_status}.")

        if not after.status == disnake.Status.offline:
            return
        
        if not before.desktop_status == disnake.Status.online:
            return

        # 1/15 chance of happening
        r = random.randint(1, 15)
        if r != 1:
            log(f'\tFailed roll {r=}.')
            return
        
        log('\tSucceeded roll!')

        # wait some time between 20 seconds and 2 minutes
        t = random.randint(20, 120)
        log(f'\tWaiting {t} seconds to start...')
        time.sleep(t)

        # check if the target is still offline
        if not (await after.guild.fetch_member(after.id)).status == disnake.Status.offline:
            return

        bot_original_nickname = bot.user.display_name

        # create the role
        role = await after.guild.create_role(name="Harpy")
        # add the target to the role
        await after.add_roles(role)

        # create a channel only visible to bot and the target
        channel = await after.guild.create_text_channel(
            name="vex-incursion", overwrites={after.guild.default_role: disnake.PermissionOverwrite(read_messages=False),
                                      role: disnake.PermissionOverwrite(read_messages=True)})
        
        # change bot's nickname to a temporary one
        bot_member = after.guild.get_member(bot.user.id);
        assert bot_member
        await bot_member.edit(nick="Asher Mir")

        # send a message to the channel, pinging the role
        await channel.send(f"{role.mention}", embed=create_embed())
        time.sleep(3)

        # delete the channel
        try:
            await channel.delete()
            log('\tCleaned up channel.')
        except:
            log('\tFailed to clean up channel.')
            log('\tRetrying...')
            time.sleep(2)
            try:
                await channel.delete()
                log('\tCleaned up channel.')
            except:
                log('\tFailed to clean up channel.')


        # delete the role
        try:
            await role.delete()
            log('\tCleaned up role.')
        except:
            log('\tFailed to clean up role.')
            log('\tRetrying...')
            time.sleep(2)
            try:
                await role.delete()
                log('\tCleaned up role.')
            except:
                log('\tFailed to clean up role.')

        # change bot's nickname back to normal
        try:
            await bot_member.edit(nick=bot_original_nickname)
            log('\tChanged bot\'s nickname back to normal.')
        except:
            log('\tFailed to change bot\'s nickname back to normal.')
            log('\tRetrying...')
            time.sleep(2)
            try:
                await bot_member.edit(nick=bot_original_nickname)
                log('\tChanged bot\'s nickname back to normal.')
            except:
                log('\tFailed to change bot\'s nickname back to normal.')
                

        log('\tDone!')



bot.run(TOKEN)
