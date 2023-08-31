import disnake
import sys
import traceback


# used to keep track of which role is assigned to which button
class ButtonData:
    def __init__(
        self,
        label: str,
        roles: list[disnake.Role],
        custom_id: str,
        emoji: disnake.PartialEmoji | None,
        description: str | None,
    ):
        self.label = label
        self.roles = roles
        self.custom_id = custom_id
        self.emoji = emoji
        self.description = description

    def __str__(self):
        return f"ButtonData(label={self.label}, roles={self.roles}, custom_id={self.custom_id}, emoji={self.emoji}, description={self.description})"

    def __repr__(self):
        return self.__str__()


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


def generate_embed_and_components(button_data: list[ButtonData]):
    components = []
    embed = disnake.Embed(
        title="Role Buttons",
        description="Click a button to get a role!",
        color=0x00FF00,
    )

    for button in button_data:
        components.append(
            disnake.ui.Button(
                label=button.label,
                custom_id=button.custom_id,
                emoji=button.emoji,
            )
        )

        if button.description:
            embed.add_field(name=button.label, value=button.description, inline=False)

    return (embed, components)
