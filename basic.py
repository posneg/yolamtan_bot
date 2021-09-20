import discord
import logging
import string
from discord.ext import commands

from constants import *
from bot import YolamtanBot
from role_commands import color_roles
from role_commands import pronoun_roles


if __name__ == '__main__':
    # Add role commands
    bot = YolamtanBot(data_path=DATA_FILE, env_path=ENV_FILE)

    # Set up discord.py's logger (Keep separate from my own)
    discord_logger = logging.getLogger('discord')
    discord_logger.setLevel(logging.DEBUG)
    discord_logfile = bot.env['logs_loc'] + 'discord.log'
    discord_handler = logging.FileHandler(filename=discord_logfile, encoding='utf-8', mode='w')
    discord_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    discord_logger.addHandler(discord_handler)

    bot.add_cog(color_roles.ColorRoles(bot))
    bot.add_cog(pronoun_roles.PronounRoles(bot))
    bot.run(bot.env['token'])