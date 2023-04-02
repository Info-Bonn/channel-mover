import time
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

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="mv", description="Move all channels from one category to an other")
    @app_commands.guild_only
    async def move_channels(self,
                            interaction: discord.Interaction,
                            category_to_move_from: discord.CategoryChannel,
                            destination: discord.CategoryChannel,
                            sync_perms: bool = True
                            ):

        resp: discord.InteractionResponse = interaction.response
        await resp.defer(ephemeral=True, thinking=True)

        for channel in category_to_move_from.channels:
            await channel.move(category=destination, sync_permissions=sync_perms,
                               reason=f"Interaction with {interaction.user.mention} issued that", end=True)
            time.sleep(1)  # please the goods of rate-limit

        followup: discord.Webhook = interaction.followup
        await followup.send("Done :)", ephemeral=True)

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

    # not used atm
    def get_channel_role(self, old_channel: discord.TextChannel,
                         target_category: discord.CategoryChannel) -> Optional[discord.Role]:
        """
        Assuming that the role in question is the only role in that channel that has permissions
        beside the roles that are in the category defined
        :returns: Role if it can be clearly determined
        """
        base_overwrites_set = set(target_category.overwrites.keys())
        overwritten_roles_set = set(old_channel.overwrites.keys())

        only_in_this_channel: set[discord.Role] = overwritten_roles_set.difference(base_overwrites_set)
        if len(only_in_this_channel) != 1:
            return None

        channel_role = only_in_this_channel.pop()
        return channel_role

    async def clone_role(self, role: discord.Role, position_in_hierarchy, name="") -> discord.Role:
        """ Create an exact copy of a role positioned at a specific position in hierarchy (optional with other name) """
        role = await role.guild.create_role(
            name=name or role.name,
            permissions=role.permissions,
            colour=role.colour,
            hoist=role.hoist,
            display_icon=role.display_icon,
            mentionable=role.mentionable,
            reason="Clone command",
        )
        await role.edit(position=position_in_hierarchy)

        return role

    @app_commands.checks.has_permissions(administrator=True)
    async def clone_category_with_new_roles(self,
                            interaction: discord.Interaction,
                            source_category: discord.CategoryChannel,
                            destination: discord.CategoryChannel,
                            new_roles_below: discord.Role,
                            rename_scheme_old_roles: str = "{name} (ws22/23)",
                            ):

        guild = interaction.guild

        role_position_below = new_roles_below.position
        old_channels: list[discord.TextChannel] = source_category.channels
        for i, old_channel in enumerate(source_category.channels):
            new_role = guild.create_role(name=)
            new_channel = guild.create_text_channel(old_channel.name,
                                                    reason="Clone command",
                                                    overwrites=old_channel.,
                                                    category=destination,
                                                    )

async def setup(bot):
    await bot.add_cog(Misc(bot))
