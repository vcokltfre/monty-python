from pathlib import Path

import yaml
from disnake import Color, Embed
from disnake.ext import commands

from monty.bot import Bot
from monty.utils.randomization import RandomCycle


SUGGESTION_FORM = ""

with Path("monty/resources/evergreen/starter.yaml").open("r", encoding="utf8") as f:
    STARTERS = yaml.load(f, Loader=yaml.FullLoader)

with Path("monty/resources/evergreen/py_topics.yaml").open("r", encoding="utf8") as f:
    # First ID is #python-general and the rest are top to bottom categories of Topical Chat/Help.
    PY_TOPICS = yaml.load(f, Loader=yaml.FullLoader)

    # Removing `None` from lists of topics, if not a list, it is changed to an empty one.
    PY_TOPICS = {k: [i for i in v if i] if isinstance(v, list) else [] for k, v in PY_TOPICS.items()}

    # All the allowed channels that the ".topic" command is allowed to be executed in.

# Putting all topics into one dictionary and shuffling lists to reduce same-topic repetitions.
ALL_TOPICS = {"default": STARTERS, **PY_TOPICS}
TOPICS = {
    channel: RandomCycle(topics or ["No topics found for this channel."]) for channel, topics in ALL_TOPICS.items()
}


class ConvoStarters(commands.Cog):
    """Evergreen conversation topics."""

    @commands.command()
    async def topic(self, ctx: commands.Context) -> None:
        """
        Responds with a random topic to start a conversation.

        If in a Python channel, a python-related topic will be given.

        Otherwise, a random conversation topic will be received by the user.
        """
        # No matter what, the form will be shown.
        embed = Embed(
            description=f"Suggest more topics [here]({SUGGESTION_FORM})!",
            color=Color.blurple(),
        )

        try:
            # Fetching topics.
            channel_topics = TOPICS[ctx.channel.id]

        # If the channel isn't Python-related.
        except KeyError:
            embed.title = f"**{next(TOPICS['default'])}**"

        # If the channel ID doesn't have any topics.
        else:
            embed.title = f"**{next(channel_topics)}**"

        finally:
            await ctx.send(embed=embed)


def setup(bot: Bot) -> None:
    """Load the ConvoStarters cog."""
    bot.add_cog(ConvoStarters())
