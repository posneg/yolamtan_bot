import discord
import toml
import logging
from discord.ext import commands

from yolamtanBot.bot import YolamtanBot

class PronounRoles(commands.Cog):

    def __init__(self, bot: YolamtanBot):
        self.bot = bot


    @commands.command(
        brief="Sets a user's own pronoun role.",
        help="Sets a user's own pronoun role. If the user already has the provided pronoun role, removes it instead.",
        name='pronoun'
    )
    async def set_pronoun(self, ctx: commands.Context, pronoun):
        if 'pronoun_roles' not in self.bot.data['servers'][str(ctx.guild.id)]:
            await ctx.send('Pronoun roles are not yet supported for this server. Please contact an admin for assistance.')
            return

        pronoun = pronoun.lower()
        if pronoun in self.bot.data['servers'][str(ctx.guild.id)]['pronoun_roles']:
            pronoun_role = ctx.guild.get_role(self.bot.data['servers'][str(ctx.guild.id)]['pronoun_roles'][pronoun])
            if pronoun_role not in ctx.author.roles:
                await ctx.author.add_roles(pronoun_role, reason='Pronoun assignment')
                self.bot.bot_logger.debug('Pronoun role %s assigned to user %s', pronoun_role.name, ctx.author.name)
                await ctx.send('Pronoun role {1} added for {0.mention}'.format(ctx.author, pronoun_role.name))
            else:
                await ctx.author.remove_roles(pronoun_role, reason='Pronoun removal')
                self.bot.bot_logger.debug('Pronoun role %s removed from user %s', pronoun_role.name, ctx.author.name)
                await ctx.send('Pronoun role {1} removed from {0.mention}'.format(ctx.author, pronoun_role.name))
        else:
            await ctx.send(
                'Pronoun role \'{0}\' is not yet available on this guild.  Please contact an admin for assistance.'
                .format(pronoun)
            )


    @commands.command()
    @commands.has_guild_permissions(administrator=True)
    @commands.max_concurrency(1, wait=True)
    async def create_pronoun_role(self, ctx: commands.Context, role_name, shorthand):
        shorthand = shorthand.lower()
        if 'pronoun_roles' not in self.bot.data['servers'][str(ctx.guild.id)]:
            self.bot.bot_logger.info('Enabling pronoun roles for guild %s', ctx.guild.name)
            self.bot.data['servers'][str(ctx.guild.id)]['pronoun_roles'] = {}

        existing_role = discord.utils.get(ctx.guild.roles, name=role_name)
        if existing_role is not None:
            self.bot.data['servers'][str(ctx.guild.id)]['pronoun_roles'][shorthand] = existing_role.id
            await ctx.send("Set up pronoun role {0.name}".format(new_role))
        else:
            new_role = await ctx.guild.create_role(name=role_name, reason="New pronoun role")
            self.bot.data['servers'][str(ctx.guild.id)]['pronoun_roles'][shorthand] = new_role.id
            await ctx.send("Created new pronoun role {0.name}".format(new_role))

        self.bot.bot_logger.debug('Writing out the self.bot.data dictionary')
        with open(self.bot.DATA_FILE, "w", encoding="utf-8") as f:
            toml.dump(self.bot.data, f)


    @commands.command(
        brief='Lists the available pronoun roles'
    )
    async def list_pronouns(self, ctx: commands.Context):
        if 'pronoun_roles' not in self.bot.data['servers'][str(ctx.guild.id)]:
            await ctx.send('Pronoun roles are not yet supported for this server. Please contact an admin for assistance.')
            return

        pronoun_roles = self.bot.data['servers'][str(ctx.guild.id)]['pronoun_roles']
        output_string = "```The following pronoun roles are available:\n"
        for (role_string, role_id) in pronoun_roles.items():
            pronoun_role = ctx.guild.get_role(role_id)
            output_string += "\n$pronoun {1} - provides role {0}".format(pronoun_role.name, role_string)
        output_string += "```"
        await ctx.send(output_string)