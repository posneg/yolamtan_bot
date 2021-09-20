import asyncio
import datetime
import discord
import logging
import random
import string
import toml
from discord.ext import commands

class YolamtanBot(commands.Bot):
    """Our subclass of bot with built-in spaces for constants"""

    def __init__(self, *args, data_path, env_path, **kwargs):

        self.data_file = data_path
        self.env = toml.load(env_path)
        self.data = toml.load(self.data_file)

        super().__init__(*args, command_prefix=self.env['prefix'], **kwargs)

        # Set up logging
        bot_logfile = self.env['logs_loc'] + datetime.datetime.now().strftime("y%Ym%md%d.log")
        # Set up my own logger
        self.bot_logger = logging.getLogger(__name__)
        self.bot_logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(filename=bot_logfile, encoding='utf-8', mode='a')
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
        self.bot_logger.addHandler(handler)
        self.add_check(self._is_correct_channel)


    # When the bot is ready, setup the "game" and print out to console
    async def on_ready(self):
        game = discord.Game("in a shower of the blood of my friends *and* foes")
        await self.change_presence(status=discord.Status.online, activity=game)
        print('We have logged in as {0.user}'.format(self))

    # Add reactions for certain messages
    async def on_message(self, message):
        # Randomly react to ~1% of messages
        if (message.author != self.user
                and message.guild is not None
                and str(message.guild.id) in self.data['servers'].keys()
                and random.random() < 0.01):
            self.bot_logger.debug('Decided to react to following message:\n%s\n\nMESSAGE END', str(message.content))
            emote = message.guild.emojis[random.randint(0, len(message.guild.emojis) - 1)]
            await self._set_reaction(message, emote)

        # Run the rest of the commands
        await self.process_commands(message)


    # React to a message.
    # image is either an emoji, or the id of an emoji
    async def _set_reaction(self, message, image):
        if not isinstance(image, int):
            await message.add_reaction(image)
            self.bot_logger.debug("Logged reaction %s to message from user %s", str(image), str(message.author.id))
        else:
            for emoticon in self.emojis:
                if emoticon.id == image:
                    await message.add_reaction(emoticon)
                    self.bot_logger.debug("Logged reaction %s to message from user %s", emoticon.id, str(message.author))
                    break


    # Check to see if this is being sent in the correct channel
    def _is_correct_channel(self, ctx):
        #if self.is_owner(ctx.author):
        #    return True
        #elif ctx.guild is not None and str(ctx.guild.id) in data['servers'].keys():
        if ctx.guild is not None and str(ctx.guild.id) in self.data['servers'].keys():
            acceptable_channels = self.data['servers'][str(ctx.guild.id)]['bot_channels']
            return -1 in acceptable_channels or ctx.channel.id in acceptable_channels
        else:
            return False