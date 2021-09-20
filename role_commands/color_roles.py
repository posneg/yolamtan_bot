import discord
import logging
import random
from discord.ext import commands

from yolamtanBot.bot import YolamtanBot


class ColorRoles(commands.Cog):

    def __init__(self, bot: YolamtanBot):
        self.bot = bot


    #Command to set a user's color
    @commands.command(
        brief="Sets a user's color",
        help="""Sets a user's color through the use of user ID based roles.
    Using the optional hex_code argument, one can pass in a valid 6-digit hexadecimal color to use.
    Alternatively, they may leave that field blank for a random color""",
        usage='<hex_code>'
    )
    async def color(self, ctx: commands.Context, *args):
        if len(args) == 0:
            red_val = random.randint(0, 0xFF)
            gre_val = random.randint(0, 0xFF)
            blu_val = random.randint(0, 0xFF)
            role_color = discord.Color.from_rgb(red_val, gre_val, blu_val)
            hexcode = "{0}".format(hex(role_color.value)[2:])
        else:
            hexcode = args[0]
            role_color = 0
            if len(hexcode) != 6:
                await ctx.send('Hexcode \'{0}\' is not a valid hexadecimal code'.format(hexcode))
                self.bot.bot_logger.info('User %s provided invalid hexcode \'%s\'', str(ctx.author), hexcode)
                return
            try:
                role_color = discord.Color(int(hexcode, 16))
            except ValueError:
                await ctx.send('Hexcode \'{0}\' is not a valid hexadecimal code'.format(hexcode))
                self.bot.bot_logger.info('User %s provided invalid hexcode \'%s\'', str(ctx.author), hexcode)
                return

        user_id = ctx.author.id
        user_role = discord.utils.find(lambda r: r.name == str(user_id), ctx.guild.roles)

        if user_role is not None:
            await user_role.edit(color=role_color)
            if user_role not in ctx.author.roles:
                await ctx.author.add_roles(user_role, reason='Adding missing color role')
                self.bot.bot_logger.debug('Gave color role to user %s', ctx.author)
        else:
            user_role = await ctx.guild.create_role(name=str(user_id), color=role_color)
            await ctx.author.add_roles(user_role, reason='Color change')
            self.bot.bot_logger.debug('Gave color role to user %s', ctx.author)
        await ctx.send('Color for {0.mention} set to {1}'.format(ctx.author, hexcode))
        self.bot.bot_logger.debug('Color for %s set to %s', str(ctx.author), hexcode)