import disnake
import sys
import traceback
import time

# log message with formatted timestamp
def log(message: str):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}] {message}")

async def error(
    inter: disnake.MessageInteraction | disnake.ApplicationCommandInteraction,
    message: str = "It seems I've encountered an error. Please try again later.",
    ephemeral: bool = True,
):
    print('Encountered an error: ')
    traceback.print_stack(file=sys.stdout)
    await inter.send(
        message,
        ephemeral=ephemeral,
    )
