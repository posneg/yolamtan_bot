from music_player.player import Player
import discord
import logging
from discord import voice_client
from discord.ext import commands
from discord.player import FFmpegAudio
import ffmpeg

from constants import *
from bot import YolamtanBot
from role_commands import color_roles
from role_commands import pronoun_roles


########### This code is for the music player ####################
# I think theres a way to register commands from a separate file somehow


@bot.command(
    brief="Adds bot to voice channel",
    help="""Commands bot to join the voice channel the commanding user is in""",
    name="join_voice"
)
async def join_voice(ctx):
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    else:
        channel = ctx.message.author.voice.channel
    await channel.connect()


@bot.command(
    brief="Removes bot from voice channel",
    help="""Removes the bot from whichever voice channel it is currently in.""",
    name="leave_voice"
)
async def leave_voice(ctx):
    await ctx.voice_client.disconnect()


@bot.command(
    brief="Plays a single song",
    help="""Plays a single song given an mp3's name. If a song is already playing,
    it adds the song to a queue to be played when the current song ends. Will
    automatically add bot to a voice channel if its not in one already.""",
    name="play"
)
async def play(ctx, song_name, filter=""):
    if not ctx.voice_client or not ctx.voice_client.is_connected():
        await join_voice(ctx)

    await player.play_song(ctx, song_name, filter)


@bot.command(
    brief="Skips the current song",
    help="""Skips the song currently being played. Doesn't use voting yet.""",
    name="skip"
)
async def skip(ctx):
    await player.skip(ctx)


@bot.command(
    brief="Pauses music player",
    name="pause"
)
async def pause(ctx):
    await player.pause(ctx)


@bot.command(
    brief="Resumes the last song being played",
    name="resume"
)
async def resume(ctx):
    await player.resume(ctx)


@bot.command(
    brief="Stops the song currently being played",
    help="""Stops the song currently being played. You cannot resume play of this song.
    When you request to play a new song, it will start playing whatever was next
    in the queue.""",
    name="stop"
)
async def stop(ctx):
    await player.stop(ctx)


########### Music player code cutoff ########################


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
