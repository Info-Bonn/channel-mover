import asyncio
import json
import re
import time
import traceback
from collections import defaultdict
from pathlib import Path
from pprint import pprint
from typing import Literal, Optional

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks
from discord.ext.commands import guild_only

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

        self.ctx_clear_reactions = app_commands.ContextMenu(
            name='clear_reactions',
            callback=self.remove_reactions,
        )

        self.bot.tree.add_command(self.ctx_tutor_message)
        self.bot.tree.add_command(self.ctx_revert_channels)
        self.bot.tree.add_command(self.ctx_clear_reactions)

        self.tutor_storage: dict[discord.TextChannel, list[int]] = defaultdict(list)


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

    # TODO: iterate over old channels an dget roles from there instead of using an interval
    #  the role interval might be screwed due to discord not being able to create roles at a fixed position
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
    @app_commands.command(name="mk_role_down")
    @app_commands.guild_only
    async def mk_role(self, interaction: discord.Interaction,
                            name: str):

        await interaction.response.defer(ephemeral=True, thinking=True)

        role = await interaction.guild.create_role(name=name)
        await role.edit(position=1)


        await interaction.followup.send("Done", ephemeral=True)


    async def remove_reactions(self, interaction: discord.Interaction,
                               message: discord.Message):

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Only admins can do that. Sorry.", ephemeral=True)
            return

        resp: discord.InteractionResponse = interaction.response
        await resp.defer(ephemeral=True, thinking=True)

        RR_BOT_ID = 858052858418036736
        rr_bot = interaction.guild.get_member(RR_BOT_ID)

        if rr_bot is None:
            await interaction.followup.send(f"cant fetch reaction role bot with id {RR_BOT_ID}")
            return

        for reaction in message.reactions:
            reactors = [user async for user in reaction.users()]
            logger.info(f"Processing Reaction: {reaction}")

            for reactor in reactors:
                if reactor.id == rr_bot.id:
                    logger.info(f"Found RR Bot. Not removing.")
                    continue

                logger.info(f"removing {reaction} for {reactor}")
                await reaction.remove(reactor)

        logger.info("Done")
        await interaction.followup.send(f"wiped")


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

        for k, v in res_dict.items():
            self.tutor_storage[k].extend(v)

        logger.info(f"added message {message.id} to pool.")

        await interaction.followup.send(f"Added message {message.id}.")


    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="rm_tutor",
                          description="Remove tutor from storage")
    @app_commands.guild_only
    async def rm_tutor(
            self,
            interaction: discord.Interaction,
            member: discord.Member
    ):

        await interaction.response.defer(ephemeral=True, thinking=True)  # okay discord. we got it.

        v: list[int]
        found_times = 0
        for k, v in self.tutor_storage.items():
            if member.id in v:
                found_times +=1
                v.remove(member.id)
                self.tutor_storage[k] = v
                logger.info(f"removed tutor {member.id} from '{k}'")

        await interaction.followup.send(f"removed tutor {member.name}, {member.id} from {found_times} channels.", ephemeral=True)


    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="finish_channels",
                          description="finish channels for semester")
    @app_commands.guild_only
    async def commit(self, interaction: discord.Interaction, category: discord.CategoryChannel, old_semester: str):
        await interaction.response.defer(ephemeral=True, thinking=True)  # okay discord. we got it.

        header = f"**Achtung** hier drüber beginnt das Semester {old_semester}."

        for channel in category.channels:

            new_msg = header

            tutors: list[int] = self.tutor_storage[channel]

            if tutors:
                tutor_header = f"\n\nTutor:innen im {old_semester} waren (evtl. unvollständig):\n"

                tutors = list(set(tutors))
                logger.info(f"Creating message for: {channel.name}, num of tutors: {len(tutors)}")
                # mention the tutor manually - this accounts for members that might have left and would resolve to None.
                # we encode the true id in a "faulty" ping. that preserves the raw data and discord handles the
                # display as 'unknown'
                tutor_names = "\n".join(f"<@{tutor}>" for tutor in tutors)
                new_msg = new_msg + tutor_header + tutor_names

            logger.info(new_msg)
            msg = await channel.send(new_msg)
            logger.info(f"Sent message to {channel.name}, {channel.id}")
            await msg.pin()

        await interaction.followup.send(f"Sent messages...", ephemeral=True)



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

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="role_backup",
                          description="Clone module channels. Prototype Channel/role represent how to model perms, "
                                      "using category as base.")
    @app_commands.guild_only
    async def role_backup(self, interaction: discord.Interaction):

        resp: discord.InteractionResponse = interaction.response
        await resp.defer(ephemeral=True, thinking=True)

        roles = await interaction.guild.fetch_roles()

        statistics = {}
        for role in roles:
            role_info = {
                "role_name": role.name,
                "count": len(role.members),
                "members": [m.id for m in role.members],
                "role_pos": role.position
            }
            statistics[role.id] = role_info

        file_name = f"data/role_info_{time.time()}.json"
        file = Path(file_name)
        file.touch()
        text = json.dumps(statistics, indent=4)
        file.write_text(text)
        print(file_name)

        await interaction.followup.send(f"Written to: {file.absolute()}", ephemeral=True, file=discord.File(file))

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="toggle_role_for_category",
                          description="Give role read+view permissions or remove them. "
                                      "On removal you can delete the overwrite in general.")
    @app_commands.guild_only
    async def toggle_role_for_category(
            self,
            interaction: discord.Interaction,
            category: discord.CategoryChannel,
            role: discord.Role,
            read: bool,
            delete: bool = False
    ):
        resp: discord.InteractionResponse = interaction.response
        await resp.defer(ephemeral=True, thinking=True)
        for channel in category.channels:
            read_messages: Optional[bool]

            # we wanna set permissions explicitly (allow or forbid)
            if read or (not read and not delete):
                overwrite = discord.PermissionOverwrite(read_messages=read, view_channel=read)
            # we wanna delete
            elif not read and delete:
                overwrite = None
            # ???
            else:
                await interaction.followup.send(
                    f"The chosen config is not possible in channel {channel.mention}, doing nothing fot it"
                )
                continue

            await channel.set_permissions(
                role,
                overwrite=overwrite
            )
            print(f"Done for {channel.name}, {channel.id}")

        await interaction.followup.send("Done :)")

    @commands.has_permissions(administrator=True)
    @commands.command(name="collect")
    async def collect_roles(self, ctx: commands.Context,):
        guild = ctx.guild

        role_dict = defaultdict(list)

        for role in guild.roles:
            name = role.name.split(" ")[0]
            role_dict[name].append(role.name)

        pprint(role_dict)

        data_file = Path("data/roles_dump.json")
        data_file.write_text(json.dumps(role_dict, indent=4))

        print(f"written to {data_file.as_posix()}")


    @staticmethod
    def get_role_by_name(guild: discord.Guild, role_name: str) -> discord.Role | None:
        res = list(filter(lambda x: x.name == role_name, guild.roles))

        if len(res) == 1:
            return res[0]

        if len(res) > 1:
            logger.warning(f"Multiple roles with name '{role_name}' found, returning None")

        return None

    @commands.has_permissions(administrator=True)
    @commands.command("merge")
    async def merge(self, ctx: commands.Context):
        roles_file = Path("data/roles_dump-edited.json")
        roles_file = Path("data/fix.json")
        roles_dict: dict[str, list[str]] = json.loads(roles_file.read_text())

        # pprint(roles_dict)

        guild = ctx.guild
        member_interaction_count = 0
        for role in guild.roles:

            no_move = False
            for k, v in roles_dict.items():
                if role.name in v:
                    role_list = v
                    break
            else:
                logger.warning(f"cant find role {role.name=}, {role.id} in mapping, skipping role...")
                continue

            if k.startswith("[NO MOVE]"):
                no_move = True
                k = k.replace("[NO MOVE]", "")


            current_role_candidates = list(filter(lambda x: "(" not in x , role_list))
            if not current_role_candidates:
                logger.warning(f"There is no candidate role for {role.name}, skipping role")
                continue

            current_role = self.get_role_by_name(guild, min(current_role_candidates)) or self.get_role_by_name(guild, k)
            if current_role is None:
                logger.warning(f"cant find role '{min(current_role_candidates)}' on guild, current_role is None")


            if len(role_list) == 1:
                old_role_name = f"{k} (old)"
                logger.info(f"Only one role for key={k}, creating role with name '{old_role_name}'")
                old_role = None
                # TODO discord interaction (create role)
                old_role = await guild.create_role(name=old_role_name, reason="did not exist yet")


            else:
                old_role_renamed_candidates = list(filter(lambda x: "(old)" in x , role_list))
                if len(old_role_renamed_candidates) == 1:
                    orc = old_role_renamed_candidates[0]
                    old_role = self.get_role_by_name(guild, orc)
                    if old_role is None:
                        logger.warning(f"Cant find '{orc}',, skipping...")
                        continue
                    logger.info(f"Found old role {old_role.name}, {role.id}")
                else:
                    old_role_candidates = list(filter(lambda x: "(" in x , role_list))
                    orc = max(old_role_candidates)
                    old_role = self.get_role_by_name(guild, orc)

                if old_role is None:
                    logger.warning(f"cant find role old role {orc} guild, skipping role...")
                    continue

            if current_role == old_role:
                logger.error(f"Old role cannot be same as current role (skipping): {role=} ")
                continue

            if role == current_role and role.name != k:
                logger.info(f"Renaming role '{role.name}' to '{k}', {role.id=}")
                # TODO discord interaction (rename role)
                role = await current_role.edit(name=k)


            if role == old_role:
                logger.info(f"{role} is old role, not moving anyone. done with role.")
                old_role_name = f"{k} (old)"
                if old_role.name != old_role_name:
                    logger.info(f"renaming role old role '{role.name}' to '{old_role_name}'")
                    old_role = await old_role.edit(name=old_role_name)

                continue

            if no_move and role == current_role:
                logger.info(f"Skipping moving of members for role: '{role.name}', {role.id}")
                continue

            logger.info(f"Starting to move members from role {role} to {old_role}")
            for member in role.members:
                logger.debug(f"handling user {member.name}")
                if old_role not in member.roles:
                    # TODO discord interaction (give member old role)
                    await member.add_roles(old_role)
                    member_interaction_count += 1

                # TODO discord interaction (remove member from current role)
                await member.remove_roles(role)
                member_interaction_count += 1
                # TODO async sleep
                await asyncio.sleep(0.4)  # please the goods of rate-limit

                if member_interaction_count % 500 == 0:
                    await ctx.send(f"{member_interaction_count} / ~24000")

                if member_interaction_count % 200 == 0:
                    logger.debug(f"{member_interaction_count} / ~24000")

            role = await guild.fetch_role(role.id)
            if len(role.members) == 0 and role != old_role and role != current_role:
                # TODO discord interaction (delete role)
                await role.delete(reason="Good bye...")
                logger.info(f"Role {role=} is now empty, and neither current nor old role. deleting...")
                # logger.info(f"Role {role.name}, {role.id} is ready for deletion")
            else:
                logger.warning(f"Role {role=} is smh not empty, not ready for deletion...")

        print(f"Done, total member interactions: {member_interaction_count}")
        await ctx.send(f"Command finished.")


    @commands.has_permissions(administrator=True)
    @commands.command("sort")
    async def sort(self, ctx: commands.Context):
        roles_file = Path("data/roles_dump-edited.json")
        roles_dict: dict[str, list[str]] = json.loads(roles_file.read_text())

        guild = ctx.guild
        for key in roles_dict:
            logger.info(f"key: {key}")
            role = self.get_role_by_name(guild, key)
            old_role = self.get_role_by_name(guild, f"{key} (old)")

            if old_role is None:
                logger.warning(f"No old role found for {key}. skipping...")
                continue
            if role is None:
                logger.warning(f"No current role found for {key}. skipping...")
                continue

            if role.position == old_role.position + 1:
                print(f"Skipping {key} - already grouped correctly")
                continue

            logger.info(f"moving {role.name}, {role.id} below {role.name}, {role.id}")
            await old_role.edit(position=role.position - 1)

            guild = await self.bot.fetch_guild(guild.id)

        logger.info(f"Command done")


async def setup(bot):
    await bot.add_cog(Misc(bot))
