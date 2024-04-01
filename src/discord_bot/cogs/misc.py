import glob
import os
import re
import time
from typing import Literal, Optional

import discord
import discord.errors as d_errs
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks

from ..lib.OEE__c_NV_RT_RS import EAEEAE__r_PL_C_M_NTc_S_
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

        self.ctx_tutor_message = app_commands.ContextMenu(
            name='add_tutor_annotations',
            callback=self.add_tutor_annotations,
        )

        self.ctx_revert_channels = app_commands.ContextMenu(
            name='revert_channel_creation',
            callback=self.ctx_revert_channel_creation,
        )
        self.bot.tree.add_command(self.ctx_tutor_message)
        self.bot.tree.add_command(self.ctx_revert_channels)

        self.repl_state = {}

    @staticmethod
    def find_latest_backup_file(guild: discord.Guild, dir_path="data/"):
        list_of_files = glob.glob(f"{dir_path}NAME_BACKUP_{guild.id}_*.csv")  # get list of all csv files
        if not list_of_files:  # if list is empty, return None
            return None
        latest_file = max(list_of_files, key=os.path.getmtime)  # find latest (most recent) file
        return latest_file

    @staticmethod
    def make_name_backup(guild: discord.Guild) -> str:
        backup_file = f"data/NAME_BACKUP_{guild.id}_{time.time()}.csv"
        backup_str = "member_id\,member_display_name\,member_name\n"
        backup_str += "\n".join(f"{m.id}\,{m.display_name}\,{m.name}" for m in guild.members)

        with open(backup_file, "w") as f:
            f.write(backup_str)

        logger.info(f"Written backup to: '{backup_file}'")
        return backup_file

    def get_member_backup(self, guild: discord.Guild) -> list[tuple[discord.Member, str]]:
        file = self.find_latest_backup_file(guild)
        logger.info(f"Reading file '{file}'")
        with open(file, "r") as f:
            lines = f.readlines()[1:]

        members = []
        errs = 0
        for line in lines:
            m_id, disp_name, m_name = line.split("\,")
            m_id = int(m_id)
            member = guild.get_member(m_id)
            if member is None:
                logger.warning(f"CANT RESOLVE id={m_id}, disp_name={disp_name}, member_name={m_name}")
                errs += 1
                continue
            members.append((member, disp_name))

        logger.info(f"Finished loading members with {errs} errors")

        return members

    def replacement_case_max_len(self, name: str, max_len=32):
        res = EAEEAE__r_PL_C_M_NTc_S_(name)
        if len(res) <= max_len:
            return res
        return self.replacement_case_max_len(name[:-1], max_len=max_len)

    def acquire_replacement_case_for_guild(self, guild: discord.Guild):
        state = self.repl_state.get(guild.id)
        if state is None or state is False:
            logger.info(f"acquired {guild.name=} {guild.id=}")
            self.repl_state[guild.id] = True
            return True

        logger.warning(f"Tried to lock for guild {guild.id} but it's locked")
        return False

    def free_replacement_case_for_guild(self, guild: discord.Guild):
        state = self.repl_state.get(guild.id)
        if state is True:
            self.repl_state[guild.id] = False
            logger.info(f"freed {guild.name=} {guild.id=}")
        else:
            logger.warning(f"Tried to free lock for {guild.id} but it wasn't locked")


    @commands.has_permissions(administrator=True)
    @commands.command("backup")
    async def backup(self, ctx: commands.Context):
        members = ctx.guild.members
        file = self.make_name_backup(ctx.guild)
        await ctx.send(f"Done: '{file}")

    @commands.has_permissions(administrator=True)
    @commands.command("replace_all", aliases=['EAEA__r_PL_C__LL'])
    async def replacement_case_all(self, ctx: commands.Context):

        lock_success = self.acquire_replacement_case_for_guild(ctx.guild)
        if not lock_success:
            await ctx.send(f"some process in progress, can't do that now")
            return

        await ctx.send(content=f"Your choice - there is no going back :)")
        members = ctx.guild.members
        self.make_name_backup(ctx.guild)

        cnt = 0
        errs = 0
        for member in members:
            disp_in_replacement_case = self.replacement_case_max_len(member.display_name)

            # logger.info(f"{member}")
            try:
                # TODO: maybe save persitents who was already changed?
                #  so if we interrupt we can skip these people and don't 'screw' their name up xd
                await member.edit(nick=disp_in_replacement_case)
            except d_errs.Forbidden:
                logger.warning(f"can't edit {member.display_name}, {member.id}")
                errs += 1
            cnt += 1
            if cnt % 20 == 0:
                logger.info(f"Status: {cnt} / {ctx.guild.member_count}")

            if cnt % 100 == 0:
                await ctx.send(content=f"AU__sT_T_S: {cnt} / {ctx.guild.member_count}")

        logger.info(f"Done for guild: {ctx.guild}, {errs=}")
        await ctx.send(embed=ut.make_embed(title=self.replacement_case_max_len('Done'), value=f"{EAEEAE__r_PL_C_M_NTc_S_('Have a nice day', eAE___SC_P_=True)} :)"))
        await ctx.send(content=f"with {errs=}")

        self.free_replacement_case_for_guild(ctx.guild)


    @commands.has_permissions(administrator=True)
    @commands.command("rollback")
    async def roll_back_replacement_case(self, ctx: commands.Context):
        lock_success = self.acquire_replacement_case_for_guild(ctx.guild)
        if not lock_success:
            await ctx.send(f"some process in progress, can't do that now")
            return

        await ctx.send(content=f"Starting rollback")
        logger.info(f"Rolling back for guild: {ctx.guild.name}")
        to_roll_back = self.get_member_backup(ctx.guild)

        cnt = 0
        errs = 0
        for m, nick in to_roll_back:
            try:
                await m.edit(nick=nick)
            except d_errs.Forbidden:
                logger.warning(f"can't edit {m.display_name}, {m.id}")
                errs += 1

            cnt += 1
            if cnt % 20 == 0:
                logger.info(f"Status: {cnt} / {ctx.guild.member_count}")

            if cnt % 100 == 0:
                await ctx.send(content=f"Status: {cnt} / {ctx.guild.member_count}")

        logger.info(f"Done for guild: {ctx.guild}, {errs=}")
        await ctx.send(content=f"Done :), {errs=}")

        self.free_replacement_case_for_guild(ctx.guild)


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
                            destination_name: str,
                            position: Literal["top", "bottom", "below_source"] = "top"
                            ):

        pos_dict = {
            "top": 0,  # TODO: why is 0 only second highest but -1 doesn't work? :shrug:
            "bottom": len(interaction.guild.channels),
            "below_source": source.position
        }
        await interaction.guild.create_category(destination_name,
                                                overwrites=source.overwrites,
                                                reason="cp command",
                                                position=pos_dict[position])

        await interaction.response.send_message("Copied.", ephemeral=True)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="mv", description="Move all channels from one category to an other")
    @app_commands.guild_only
    async def move_channels(self,
                            interaction: discord.Interaction,
                            category_to_move_from: discord.CategoryChannel,
                            destination: discord.CategoryChannel,
                            module_selection_channel: discord.TextChannel = None,
                            sync_perms_to_new_category: bool = True,
                            preserve_disable_channel_role: bool = True,
                            ):

        if module_selection_channel is not None:
            logger.warning(f"No module selection channel was given. continuing...")

        resp: discord.InteractionResponse = interaction.response
        await resp.defer(ephemeral=True, thinking=True)

        for channel in category_to_move_from.channels:

            logger.info(f"Editing channel {channel.name}...")

            # get base perms
            if sync_perms_to_new_category:
                new_perms = destination.overwrites
            else:
                new_perms = channel.overwrites

            # re-add module channel role if wanted, but with no perms
            # this is helpful to create a new set of channels for the next semester with the same role names
            # also exclude the channel where modules are chosen, this one has no channel role
            if preserve_disable_channel_role and channel != module_selection_channel:
                channel_role = self.get_channel_role(channel, category_to_move_from)
                # setup new overwrite that disallows everything
                channel_perms = discord.PermissionOverwrite.from_pair(discord.Permissions(), discord.Permissions.none())
                # add to global overwrite
                new_perms[channel_role] = channel_perms

            await channel.edit(category=destination, overwrites=new_perms,
                               reason=f"Interaction with {interaction.user.mention} issued that",)

            logger.info(f"Done editing {channel.name}")
            time.sleep(1)  # please the goods of rate-limit

        followup: discord.Webhook = interaction.followup
        logger.info(f"Done with the whole move process")
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
        # do comprehension to filter only for role-overwrites
        base_overwrites_set = set(ov for ov in target_category.overwrites.keys() if type(ov) == discord.Role)
        overwritten_roles_set = set(ov for ov in old_channel.overwrites.keys() if type(ov) == discord.Role)

        only_in_this_channel: set[discord.Role] = overwritten_roles_set.difference(base_overwrites_set)
        if len(only_in_this_channel) != 1:
            logger.warning(f"Can't determine channel role, more than one candidate: {only_in_this_channel=}")
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
    @app_commands.command(name="rename_roles",
                          description="Rename roles with scheme ({name} and {to_add}), "
                                      "roles containing scheme and limits are not edited.")
    @app_commands.guild_only
    async def rename_roles_bulk(self,
                                interaction: discord.Interaction,
                                lower_role: discord.Role,
                                upper_role: discord.Role,
                                to_add: str,
                                rename_scheme: str = "{name} {to_add}"):

        scheme = rename_scheme.replace("{to_add}", to_add)

        await interaction.response.send_message(
            f"Renaming channels with scheme: '{scheme}'",
            ephemeral=True)
        # refresh roles, because it bugged once, this will fix it hopefully
        await interaction.guild.fetch_roles()
        for role in interaction.guild.roles:
            if (lower_role < role < upper_role) and to_add not in role.name:
                await role.edit(name=scheme.replace("{name}", role.name))

        await interaction.followup.send("Done")

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="clone_category_with_new_roles",
                          description="Clone module channels. Prototype Channel/role represent how to model perms, "
                                      "using category as base.")
    @app_commands.guild_only
    async def clone_category_with_new_roles(self,
                                            interaction: discord.Interaction,
                                            source_category: discord.CategoryChannel,
                                            old_module_selection_channel: discord.TextChannel,
                                            prototype_channel: discord.TextChannel,
                                            prototype_role: discord.Role,
                                            destination_category: discord.CategoryChannel,
                                            new_roles_below: discord.Role,
                                            ):

        # TODO: this starts one role too low, maybe because everyone is role 0?
        # only simplify access
        role_position_below = new_roles_below.position
        old_channels: list[discord.TextChannel] = source_category.channels

        # respond so interaction doesn't time out
        await interaction.response.send_message(
            f"trying to clone {len(old_channels)} and roles from '{source_category.name}' to '{source_category.name}'",
            ephemeral=True)

        guild = interaction.guild

        log: list[str] = []  # log errors
        # get permissions that the module role shall have
        prototype_role_overwrites = prototype_channel.overwrites_for(prototype_role)

        created_role_channel_pairs: list[tuple[discord.Role, discord.TextChannel]] = []

        for old_channel in source_category.channels:
            # ignore selection channel
            if old_channel.id == old_module_selection_channel.id:
                continue

            # TODO: this messes HARD with the role order even tough the position should be clear
            #  I suggest saving the previous layout and doing a sanity / cleanup check afterwards.
            #  maybe we should do a snapshot before to at least reorder the rest relative to each other?
            # create new role with same base permission set at target position in hierarchy
            new_channel_role = await self.clone_role(prototype_role,
                                                     name=old_channel.name,
                                                     position_in_hierarchy=role_position_below)

            # configure overwrite for new channel
            # TODO: note to the user: make sure that the category doesn't allow unwanted roles like 'member'!
            dest_cat_overwrites = destination_category.overwrites
            dest_cat_overwrites[new_channel_role] = prototype_role_overwrites

            # create new channel
            new_channel = await guild.create_text_channel(old_channel.name,
                                                          reason="Clone command",
                                                          category=destination_category,
                                                          overwrites=dest_cat_overwrites
                                                          )

            created_role_channel_pairs.append((new_channel_role, new_channel))

        # TODO: we've got all the roles - should we fetch their positions and reorder until they've got the right spots?
        #  but this will cost an insane amount of api calls...
        # write log output
        log_msg = f"Incidents:\n" + "\n".join(log) if len(log) > 0 else "No incidents during creation reported"
        await interaction.followup.send(log_msg)

        # report role 'map' containing channel, role, role_id
        joined = "\n\n".join(
            f"{channel.mention} {role.mention} - {role.id}" for role, channel in created_role_channel_pairs)
        await interaction.followup.send(joined)

        # format for reaction role bots command
        rr_format = "Roles: `" + " ".join([f"<@&{role.id}>" for role, channel in created_role_channel_pairs]) + "`"
        await interaction.followup.send(rr_format)

        print(rr_format)

    async def ctx_revert_channel_creation(self,
                                    interaction: discord.Interaction,
                                    message: discord.Message
                                    ):
        """ Revert everything that was done with /clone_category_with_new_roles, works only on the output message of that command """
        async def iter_delete(to_iter: list[int], get_function):
            for mention in to_iter:
                try:
                    obj = get_function(mention)
                    await obj.delete(reason="revert")
                    logger.info(f"Deleted {obj.name}")
                except Exception as e:
                    logger.warning(f"Couldn't delete thing with id='{mention}', reason: {e}")

        resp: discord.InteractionResponse = interaction.response
        await resp.defer(ephemeral=True, thinking=True)
        followup: discord.Webhook = interaction.followup


        role_mentions = message.raw_role_mentions
        channel_mentions = message.raw_channel_mentions

        await iter_delete(role_mentions, interaction.guild.get_role)
        logger.info(f"Done with the roles")
        await followup.send("Done with the roles", ephemeral=True)
        await iter_delete(channel_mentions, interaction.guild.get_channel)
        logger.info(f"Done with the channels")
        await followup.send("Done with the channels", ephemeral=True)

        logger.info(f"Done with the whole remove process")
        await followup.send("Done. Good luck next time! :)", ephemeral=True)

    async def add_tutor_annotations(self,
                                    interaction: discord.Interaction,
                                    message: discord.Message
                                    ):
        """
        parses a message of the format:
        #module-channel-1
        @module-tutor-1
        @tutor-2

        #module-channel-n
        @module-tutor-n
        @module-tutor-n+1

        ...and sends the list of these tutors (as mentions) in the above-mentioned channel (pinning included)

        """

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Only admins can do that. Sorry.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True, thinking=True)  # okay discord. we got it.


        res_dict = await self.parse_message(message)

        # TODO: maybe move this to config?
        tutor_header = "Tutor:innen (evtl. unvollständig):\n"
        tutors: list[discord.Member]
        for channel, tutors in res_dict.items():

            logger.info(f"Creating message for: {channel.name}, num of tutors: {len(tutors)}")
            # mention the tutor manually - this accounts for members that might have left and would resolve to None.
            # we encode the true id in a "faulty" ping. that preserves the raw data and discord handles the
            # display as 'unknown'
            tutor_names = "\n".join(f"<@{tutor}>" for tutor in tutors)
            tutor_msg = tutor_header + tutor_names
            logger.debug(tutor_msg)
            msg = await channel.send(tutor_msg)
            await msg.pin()

        await interaction.followup.send("Done.")


    # This method was scratched with GPT4 and heavily modified by myself (honestly would have been faster on my own)
    # parsing just ins't beautiful, but it came out better than I first envisioned
    async def parse_message(self, message: discord.Message) -> dict[
        discord.TextChannel, list[int]]:
        """
        Parse a discord message and build a dictionary of channels to members.

        Args:
            message (discord.Message): The discord message to parse.

        Returns:
            dict[discord.TextChannel, list[int]: A dictionary where each key is a discord channel,
            and each value is a list of member-ids mentioned under that channel in the message.
        """
        guild = message.guild

        parsed_dict = {}
        lines = message.content.split('\n')
        current_channel = None

        for line in lines:
            # Ignore lines that have more than one mention or no mentions at all
            matches = re.findall(r'\d+', line)
            if len(matches) != 1:
                continue

            # found a valid line: either a channel- or a member-id
            elm_id = matches[0]

            # Check which type of mention it is
            # (mention must be at the start of the line, otherwise we ignore it)

            # Check if the line contains a channel mention
            if line.startswith('<#'):
                # Extract the channel ID from the mention
                current_channel = await guild.fetch_channel(elm_id)  # Get the channel object

                if current_channel is None:
                    logger.warning(f"Can't resolve channel id {elm_id} - continuing without adding that channel.")
                    continue

                parsed_dict[current_channel] = []  # Initialize the member list for this channel

            # Check if the line contains a user mention (prevent role mentions)
            elif line.startswith('<@') and not line.startswith("<@&"):
                if current_channel is None:
                    logger.warning(f"Current-channel is None, can't add member {elm_id} to dict. Continuing...")
                    continue

                # add member id
                parsed_dict[current_channel].append(elm_id)

        return parsed_dict


async def setup(bot):
    await bot.add_cog(Misc(bot))
