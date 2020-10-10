import discord
import asyncio
import string
import random
import sys
import logging
from discord.ext import commands
import toml

env = toml.load('./env.toml')
DATA_FILE = './storage_test.toml'
data = toml.load(DATA_FILE)


bot = commands.Bot(command_prefix=env['prefix'])


## Set up logging
import datetime
bot_logfile = env['logs_loc'] + datetime.datetime.now().strftime("y%Ym%md%d.log")
# Set up discord.py's logger (Keep separate from my own)
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.DEBUG)
discord_logfile = env['logs_loc'] + 'discord.log'
discord_handler = logging.FileHandler(filename=discord_logfile, encoding='utf-8', mode='w')
discord_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
discord_logger.addHandler(discord_handler)

# Set up my own logger
bot_logger = logging.getLogger(__name__)
bot_logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename=bot_logfile, encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
bot_logger.addHandler(handler)


@bot.event
async def on_message(message):

    # Randomly react to ~1% of messages
    if (message.author != bot.user
            and message.guild is not None
            and str(message.guild.id) in data['servers'].keys()
            and random.random() < .01):
        bot_logger.debug('Decided to react to following message:\n%s\n\nMESSAGE END', str(message.content))
        emote = message.guild.emojis[random.randint(0, len(message.guild.emojis) - 1)]
        await set_reaction(message, emote)

    # Run the rest of the commands
    await bot.process_commands(message)

# Check to see if this is being sent in the correct channel
def is_correct_channel():
    def predicate(ctx):
        if ctx.guild is not None and ctx.guild.id in data['servers'].keys():
                acceptable_channels = data['servers'][str(ctx.guild.id)]['bot_channels']
                return -1 in acceptable_channels or ctx.channel.id in acceptable_channels
        else:
            return False
    return commands.check(predicate)


#Command to set a user's color
@bot.command(
    brief="Sets a user's color",
    help="""Sets a user's color through the use of user ID based roles.
Using the optional hex_code argument, one can pass in a valid 6-digit hexadecimal color to use.
Alternatively, they may leave that field blank for a random color""",
    usage='<hex_code>',
    hidden=True
)
@commands.check(is_correct_channel())
async def color(ctx, *args):
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
            bot_logger.info('User %s provided invalid hexcode \'%s\'', str(ctx.author), hexcode)
            return
        try:
            role_color = discord.Color(int(hexcode, 16))
        except ValueError:
            await ctx.send('Hexcode \'{0}\' is not a valid hexadecimal code'.format(hexcode))
            bot_logger.info('User %s provided invalid hexcode \'%s\'', str(ctx.author), hexcode)
            return

    user_id = ctx.author.id
    user_role = discord.utils.find(lambda r: r.name == str(user_id), ctx.guild.roles)

    if user_role is not None:
        await user_role.edit(color=role_color)
        if user_role not in ctx.author.roles:
            await ctx.author.add_roles(user_role, reason='Adding missing color role')
            bot_logger.debug('Gave color role to user %s', ctx.author)
    else:
        user_role = await ctx.guild.create_role(name=str(user_id), color=role_color)
        await ctx.author.add_roles(user_role, reason='Color change')
        bot_logger.debug('Gave color role to user %s', ctx.author)
    await ctx.send('Color for {0.mention} set to {1}'.format(ctx.author, hexcode))
    bot_logger.debug('Color for %s set to %s', str(ctx.author), hexcode)


@bot.command(
    brief="Sets a user's color role",
    help="""Sets a user's color role to the role identified by the string provided.""",
    name='color_role'
)
@commands.check(is_correct_channel())
async def set_color_role(ctx, *, role_name):
    # Extract the color_roles data so it's more easily accessible
    color_roles = data['servers'][str(ctx.guild.id)].get('color_roles')
    if color_roles is None:
        color_roles = {}
        data['servers'][str(ctx.guild.id)]['color_roles'] = color_roles
    # First things first -- does the user already have a color role?
    if any(str(r.id) in color_roles for r in ctx.author.roles):
        await ctx.send("You may only have one color role at a time.  Please remove your color role via the unset_color command")
        return

    # Next, check if the desired role already exists.
    correctly_named = filter(lambda r: r.name == role_name, ctx.guild.roles)
    for role in correctly_named:
        data_entry = color_roles.get(str(role.id))
        if data_entry is not None:
            await ctx.author.add_roles(role, reason='Applying color role to new user')
            await ctx.send("Applied the color role {0.mention} to user {1.mention}.  The current owner of this role is {2.mention}"
                .format(role, ctx.author, ctx.guild.get_member(data_entry['owner'])))
            bot_logger.debug('Color role for %s set to %s', str(ctx.author), str(role))
            return

    # If the above code did not return, this must be a new role.  Create it!
    bot_logger.debug('Creating new color role %s', role_name)
    new_color_role = await ctx.guild.create_role(name=role_name)
    await ctx.author.add_roles(new_color_role, reason='Applying new color role to user')
    color_roles[str(new_color_role.id)] = {"owner": ctx.author.id}
    await ctx.send('Created new color role {0.mention}.  {1.mention} is the owner of this role.'.format(new_color_role, ctx.author))
    bot_logger.debug('Writing out the data dictionary')
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        toml.dump(data, f)


@bot.command(
    brief="Removes a user's color role.",
    name='unset_color'
)
@commands.check(is_correct_channel())
async def unset_color_role(ctx):
    # Extract the color_roles data so it's more easily accessible
    color_roles = data['servers'][str(ctx.guild.id)].get('color_roles')
    if color_roles is None:
        return

    for possible_color in ctx.author.roles:
        data_entry = color_roles.get(str(possible_color.id))
        if data_entry is not None:
            bot_logger.debug("Remove color role %s from user %s", str(possible_color), str(ctx.author))
            await ctx.author.remove_roles(possible_color, reason='Unset color role')
            await ctx.send('Removed role {0} from user {1.mention}'.format(str(possible_color),ctx.author))
            if data_entry.get('owner') == ctx.author.id and len(possible_color.members) > 0:
                data_entry['owner'] = possible_color.members[0].id
            elif data_entry.get('owner') == ctx.author.id:
                await possible_color.delete(reason='Removing unused color role')
                await ctx.send('Deleted above color role after the role\'s last user left')
                del data_entry['owner']


@bot.command(
    brief="Sets a user's own pronoun role.",
    help="Sets a user's own pronoun role. If the user already has the provided pronoun role, removes it instead.",
    name='pronoun'
)
@commands.check(is_correct_channel())
async def set_pronoun(ctx, pronoun):
    if 'pronoun_roles' not in data['servers'][str(ctx.guild.id)]:
        await ctx.send('Pronoun roles are not yet supported for this server. Please contact an admin for assistance.')
        return

    pronoun = pronoun.lower()
    if pronoun in data['servers'][str(ctx.guild.id)]['pronoun_roles']:
        pronoun_role = ctx.guild.get_role(data['servers'][str(ctx.guild.id)]['pronoun_roles'][pronoun])
        if pronoun_role not in ctx.author.roles:
            await ctx.author.add_roles(pronoun_role, reason='Pronoun assignment')
            bot_logger.debug('Pronoun role %s assigned to user %s', pronoun_role.name, ctx.author.name)
            await ctx.send('Pronoun role {1} added for {0.mention}'.format(ctx.author, pronoun_role.name))
        else:
            await ctx.author.remove_roles(pronoun_role, reason='Pronoun removal')
            bot_logger.debug('Pronoun role %s removed from user %s', pronoun_role.name, ctx.author.name)
            await ctx.send('Pronoun role {1} removed from {0.mention}'.format(ctx.author, pronoun_role.name))
    else:
        await ctx.send(
            'Pronoun role \'{0}\' is not yet available on this guild.  Please contact an admin for assistance.'
            .format(pronoun)
        )


@bot.command(
    brief='Lists the available pronoun roles'
)
@commands.check(is_correct_channel())
async def list_pronouns(ctx):
    if 'pronoun_roles' not in data['servers'][str(ctx.guild.id)]:
        await ctx.send('Pronoun roles are not yet supported for this server. Please contact an admin for assistance.')
        return

    pronoun_roles = data['servers'][str(ctx.guild.id)]['pronoun_roles']
    output_string = "```The following pronoun roles are available:\n"
    for (role_string, role_id) in pronoun_roles.items():
        pronoun_role = ctx.guild.get_role(role_id)
        output_string += "\n$pronoun {1} - provides role {0}".format(pronoun_role.name, role_string)
    output_string += "```"
    await ctx.send(output_string)


#Command to close the bot cleanly
@bot.command(hidden=True)
@commands.is_owner()
async def close_bot(ctx):
    bot_logger.info('Received close_bot command from owner.  Exiting')
    await bot.close()


@bot.command()
@commands.check(is_correct_channel())
@commands.has_guild_permissions(administrator=True)
@commands.max_concurrency(1, wait=True)
async def create_pronoun_role(ctx, role_name, shorthand):
    shorthand = shorthand.lower()
    if 'pronoun_roles' not in data['servers'][str(ctx.guild.id)]:
        bot_logger.info('Enabling pronoun roles for guild %s', ctx.guild.name)
        data['servers'][str(ctx.guild.id)]['pronoun_roles'] = {}

    existing_role = discord.utils.get(ctx.guild.roles, name=role_name)
    if existing_role is not None:
        data['servers'][str(ctx.guild.id)]['pronoun_roles'][shorthand] = existing_role.id
        await ctx.send("Set up pronoun role {0.name}".format(new_role))
    else:
        new_role = await ctx.guild.create_role(name=role_name, reason="New pronoun role")
        data['servers'][str(ctx.guild.id)]['pronoun_roles'][shorthand] = new_role.id
        await ctx.send("Created new pronoun role {0.name}".format(new_role))

    bot_logger.debug('Writing out the data dictionary')
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        toml.dump(data, f)


#When the bot is ready, setup the "game" and print out to console
@bot.event
async def on_ready():
    game = discord.Game("with various limbs")
    await bot.change_presence(status=discord.Status.online, activity=game)
    print('We have logged in as {0.user}'.format(bot))


# React to a message.
# image is either an emoji, or the id of an emoji
async def set_reaction(message, image):
    if not isinstance(image, int):
        await message.add_reaction(image)
        bot_logger.debug("Logged reaction %s to message from user %s", str(image), str(message.author.id))
    else:
        for emoticon in self.emojis:
            if emoticon.id == image:
                await message.add_reaction(emoticon)
                bot_logger.debug("Logged reaction %s to message from user %s", emoticon.id, str(message.author))
                break

#        help_string = ('{0.display_name}\'s discord bot.\n\n'.format(owner) +
#                        'Available commands:\n**$help**: Displays this help text\n' +
#                        '**$color**: Sets your user\'s role color to a random hex value\n' +
#                        '**$color [hex_code]**: Sets your user\'s role color to the provided hex code')


if __name__ == '__main__':
    bot.run(env['token'])