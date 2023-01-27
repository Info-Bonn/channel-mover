from typing import Literal, Optional

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks

from ..log_setup import logger
from ..utils import utils as ut


### @package misc
#
# Collection of miscellaneous helpers.
#

class Misc(commands.Cog):
    """
    Various useful Commands for everyone
    """

    def __init__(self, bot):
        self.bot: commands.Bot = bot

    # a chat based command
    @commands.command(name='ping', help="Check if Bot available")
    async def ping(self, ctx):
        """!
        ping to check if the bot is available

        @param ctx Context of the message
        """
        logger.info(f"ping: {round(self.bot.latency * 1000)}")

        await ctx.send(
            embed=ut.make_embed(
                name='Bot is available',
                value=f'`{round(self.bot.latency * 1000)}ms`')
        )

    @app_commands.command(name="ping", description="Ping as a slash command")
    # @app_commands.guild_only
    async def ping_slash(self,
                         interaction: discord.Interaction,
                         mode: Optional[Literal["silent", "loud"]]):
        """
        Ping command implementing the same functionality as "chat"-command
        But with extra option to be silent
        """
        logger.info(f"ping: {round(self.bot.latency * 1000)}")
        # decide whether this message shall be silent
        ephemeral = True if mode and mode == "silent" else False

        await interaction.response.send_message(
            embed=ut.make_embed(
                name='Bot is available',
                value=f'`{round(self.bot.latency * 1000)}ms`'),
            ephemeral=ephemeral
        )

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="cp", description="Copy a category-channel, does not include the channels in it")
    @app_commands.guild_only
    async def copy_category(self,
                            interaction: discord.Interaction,
                            source: discord.CategoryChannel,
                            destination_name: str
                            ):
        await interaction.guild.create_category(destination_name,
                                                overwrites=source.overwrites,
                                                reason="cp command",
                                                position=source.position)

        await interaction.response.send_message("Copied.", ephemeral=True)

    # Example for an event listener
    # This one will be called on each message the bot receives
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        pass

    # Example for a task
    # It can be started using self.my_task.start() e.g. from this cogs __init__
    @tasks.loop(seconds=60)
    async def my_task(self):
        pass

async def setup(bot):
    await bot.add_cog(Misc(bot))
