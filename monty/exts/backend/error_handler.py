import difflib
import logging
import math
import random
from typing import Iterable, Union

from disnake import Embed, Message
from disnake.ext import commands

from monty.bot import Bot
from monty.constants import ERROR_REPLIES, NEGATIVE_REPLIES, Colours, RedirectOutput
from monty.utils.decorators import InChannelCheckFailure, InMonthCheckFailure
from monty.utils.exceptions import APIError


log = logging.getLogger(__name__)


QUESTION_MARK_ICON = "https://cdn.discordapp.com/emojis/512367613339369475.png"


class CommandErrorHandler(commands.Cog):
    """A error handler for the PythonDiscord server."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @staticmethod
    def revert_cooldown_counter(command: commands.Command, message: Message) -> None:
        """Undoes the last cooldown counter for user-error cases."""
        if command._buckets.valid:
            bucket = command._buckets.get_bucket(message)
            bucket._tokens = min(bucket.rate, bucket._tokens + 1)
            logging.debug("Cooldown counter reverted as the command was not used correctly.")

    @staticmethod
    def error_embed(message: str, title: Union[Iterable, str] = ERROR_REPLIES) -> Embed:
        """Build a basic embed with red colour and either a random error title or a title provided."""
        embed = Embed(colour=Colours.soft_red)
        if isinstance(title, str):
            embed.title = title
        else:
            embed.title = random.choice(title)
        embed.description = message
        return embed

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        """Activates when a command raises an error."""
        if getattr(error, "handled", False):
            logging.debug(f"Command {ctx.command} had its error already handled locally; ignoring.")
            return

        parent_command = ""
        if subctx := getattr(ctx, "subcontext", None):
            parent_command = f"{ctx.command} "
            ctx = subctx

        error = getattr(error, "original", error)
        logging.debug(
            f"Error Encountered: {type(error).__name__} - {str(error)}, "
            f"Command: {ctx.command}, "
            f"Author: {ctx.author}, "
            f"Channel: {ctx.channel}"
        )

        if isinstance(error, commands.CommandNotFound):
            await self.send_command_suggestion(ctx, ctx.invoked_with)
            return

        if isinstance(error, (InChannelCheckFailure, InMonthCheckFailure)):
            await ctx.send(embed=self.error_embed(str(error), NEGATIVE_REPLIES), delete_after=7.5)
            return

        if isinstance(error, commands.UserInputError):
            self.revert_cooldown_counter(ctx.command, ctx.message)
            usage = f"```{ctx.prefix}{parent_command}{ctx.command} {ctx.command.signature}```"
            embed = self.error_embed(f"Your input was invalid: {error}\n\nUsage:{usage}")
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.CommandOnCooldown):
            mins, secs = divmod(math.ceil(error.retry_after), 60)
            embed = self.error_embed(
                f"This command is on cooldown:\nPlease retry in {mins} minutes {secs} seconds.",
                NEGATIVE_REPLIES,
            )
            await ctx.send(embed=embed, delete_after=7.5)
            return

        if isinstance(error, commands.DisabledCommand):
            await ctx.send(embed=self.error_embed("This command has been disabled.", NEGATIVE_REPLIES))
            return

        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send(
                embed=self.error_embed(
                    "This command can only be used in a server.",
                    NEGATIVE_REPLIES,
                )
            )
            return

        if isinstance(error, commands.BadArgument):
            self.revert_cooldown_counter(ctx.command, ctx.message)
            embed = self.error_embed(
                "The argument you provided was invalid: "
                f"{error}\n\nUsage:\n```{ctx.prefix}{parent_command}{ctx.command} {ctx.command.signature}```"
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.CheckFailure):
            await ctx.send(embed=self.error_embed("You are not authorized to use this command.", NEGATIVE_REPLIES))
            return

        if isinstance(error, APIError):
            await ctx.send(
                embed=self.error_embed(
                    f"There was an error when communicating with the {error.api}."
                    + (f"\n{error.error_msg}" if error.error_msg is not None else ""),
                    NEGATIVE_REPLIES,
                )
            )
            return

        log.exception(f"Unhandled command error: {str(error)}", exc_info=error)

    async def send_command_suggestion(self, ctx: commands.Context, command_name: str) -> None:
        """Sends user similar commands if any can be found."""
        raw_commands = []
        for cmd in self.bot.walk_commands():
            if not cmd.hidden:
                raw_commands += (cmd.name, *cmd.aliases)
        if similar_command_data := difflib.get_close_matches(command_name, raw_commands, 1):
            similar_command_name = similar_command_data[0]
            similar_command = self.bot.get_command(similar_command_name)

            if not similar_command:
                return

            log_msg = "Cancelling attempt to suggest a command due to failed checks."
            try:
                if not await similar_command.can_run(ctx):
                    log.debug(log_msg)
                    return
            except commands.errors.CommandError as cmd_error:
                log.debug(log_msg)
                await self.on_command_error(ctx, cmd_error)
                return

            misspelled_content = ctx.message.content
            e = Embed()
            e.set_author(name="Did you mean:", icon_url=QUESTION_MARK_ICON)
            e.description = misspelled_content.replace(command_name, similar_command_name, 1)
            await ctx.send(embed=e, delete_after=RedirectOutput.delete_delay)


def setup(bot: Bot) -> None:
    """Load the ErrorHandler cog."""
    bot.add_cog(CommandErrorHandler(bot))
