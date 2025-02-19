from __future__ import annotations

import logging
import re
import unicodedata
from typing import Tuple

import disnake
from disnake import Colour, Embed, Object, utils
from disnake.ext import commands
from disnake.ext.commands import BadArgument, Cog, Context
from disnake.utils import DISCORD_EPOCH

from monty.bot import Bot
from monty.utils.delete import get_view
from monty.utils.pagination import LinePaginator


log = logging.getLogger(__name__)


class CharInfo(Cog):
    """A selection of utilities which don't have a clear category."""

    def __init__(self, bot: Bot) -> CharInfo:
        self.bot = bot

    @commands.slash_command(name="char-info")
    async def charinfo(self, ctx: disnake.ApplicationCommandInteraction, characters: str) -> None:
        """Shows you information on up to 50 unicode characters."""
        match = re.match(r"<(a?):(\w+):(\d+)>", characters)
        if match:
            await ctx.send(
                "**Non-Character Detected**\n"
                "Only unicode characters can be processed, but a custom Discord emoji "
                "was found. Please remove it and try again."
            )
            return

        if len(characters) > 50:
            await ctx.send("Too many characters ({len(characters)}/50)")

        def get_info(char: str) -> Tuple[str, str]:
            digit = f"{ord(char):x}"
            if len(digit) <= 4:
                u_code = f"\\u{digit:>04}"
            else:
                u_code = f"\\U{digit:>08}"
            url = f"https://www.compart.com/en/unicode/U+{digit:>04}"
            name = f"[{unicodedata.name(char, '')}]({url})"
            info = f"`{u_code.ljust(10)}`: {name} - {utils.escape_markdown(char)}"
            return (info, u_code)

        (char_list, raw_list) = zip(*(get_info(c) for c in characters))
        embed = Embed().set_author(name="Character Info")

        if len(characters) > 1:
            # Maximum length possible is 502 out of 1024, so there's no need to truncate.
            embed.add_field(name="Full Raw Text", value=f"`{''.join(raw_list)}`", inline=False)
        embed.description = "\n".join(char_list)
        await ctx.send(embed=embed)

    @commands.command(aliases=("snf", "snfl", "sf"))
    async def snowflake(self, ctx: Context, *snowflakes: Object) -> None:
        """Get Discord snowflake creation time."""
        if not snowflakes:
            raise BadArgument("At least one snowflake must be provided.")

        # clear any dup keys
        snowflakes = list(set(snowflakes))

        embed = Embed(colour=Colour.blue())
        embed.set_author(
            name=f"Snowflake{'s'[:len(snowflakes)^1]}",  # Deals with pluralisation
            icon_url="https://github.com/twitter/twemoji/blob/master/assets/72x72/2744.png?raw=true",
        )

        lines = []
        for snowflake in snowflakes:
            created_at = int(((snowflake.id >> 22) + DISCORD_EPOCH) / 1000)
            lines.append(f"**{snowflake.id}** ({created_at})\nCreated at <t:{created_at}:f> (<t:{created_at}:R>).")

        await LinePaginator.paginate(lines, ctx=ctx, embed=embed, max_lines=5, max_size=1000)

    @commands.slash_command(name="snowflake")
    async def slash_snowflake(
        self,
        inter: disnake.AppCommandInteraction,
        snowflake: str,
    ) -> None:
        """
        [BETA] Get creation date of a snowflake.

        Parameters
        ----------
        snowflake: The snowflake.
        """
        try:
            snowflake = int(snowflake)
        except ValueError:
            await inter.send("`snowflake` must be an integer!", ephemeral=True)
            return
        embed = Embed(colour=Colour.blue())
        embed.set_author(
            name="Snowflake",
            icon_url="https://github.com/twitter/twemoji/blob/master/assets/72x72/2744.png?raw=true",
        )
        created_at = int(((snowflake >> 22) + DISCORD_EPOCH) / 1000)
        embed.description = f"**{snowflake}** ({created_at})\nCreated at <t:{created_at}:f> (<t:{created_at}:R>)."
        await inter.send(embed=embed, view=get_view(inter))

    # @command(aliases=("poll",))
    # async def vote(
    #     self, ctx: Context, title: clean_content(fix_channel_mentions=True), *options: str
    # ) -> None:
    #     """
    #     Build a quick voting poll with matching reactions with the provided options.

    #     A maximum of 20 options can be provided, as Discord supports a max of 20
    #     reactions on a single message.
    #     """
    #     if len(title) > 256:
    #         raise BadArgument("The title cannot be longer than 256 characters.")
    #     if len(options) < 2:
    #         raise BadArgument("Please provide at least 2 options.")
    #     if len(options) > 20:
    #         raise BadArgument("I can only handle 20 options!")

    #     codepoint_start = 127462  # represents "regional_indicator_a" unicode value
    #     options = {chr(i): f"{chr(i)} - {v}" for i, v in enumerate(options, start=codepoint_start)}
    #     embed = Embed(title=title, description="\n".join(options.values()))
    #     message = await ctx.send(embed=embed)
    #     for reaction in options:
    #         await message.add_reaction(reaction)


def setup(bot: Bot) -> None:
    """Load the Utils cog."""
    bot.add_cog(CharInfo(bot))
