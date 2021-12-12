from discord import voice_client
from discord.ext import commands
from discord.player import FFmpegAudio
import ffmpeg

import bot.music_player.player

class PlayerCog(commands.Cog):

    def __init__(self):
        # For right now, I'm using a single music player.
        self.player = bot.music_player.player.Player('Fake Guild ID')

        # if you want a dictionary of individual players or such,
        # this is where you'd put it.  Something like:
        # self.players = {}


    @commands.command(
        brief="Adds bot to voice channel",
        help="""Commands bot to join the voice channel the commanding user is in""",
        name="join_voice"
    )
    async def join_voice(self, ctx):
        if not ctx.message.author.voice:
            await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
            return
        else:
            channel = ctx.message.author.voice.channel
        await channel.connect()


    @commands.command(
        brief="Removes bot from voice channel",
        help="""Removes the bot from whichever voice channel it is currently in.""",
        name="leave_voice"
    )
    async def leave_voice(self, ctx):
        await ctx.voice_client.disconnect()


    @commands.command(
        brief="Plays a single song",
        help="""Plays a single song given an mp3's name. If a song is already playing,
        it adds the song to a queue to be played when the current song ends. Will
        automatically add bot to a voice channel if its not in one already.""",
        name="play"
    )
    async def play(self, ctx, song_name, filter=""):
        if not ctx.voice_client or not ctx.voice_client.is_connected():
            await join_voice(ctx)

        await self.player.play_song(ctx, song_name, filter)


    @commands.command(
        brief="Skips the current song",
        help="""Skips the song currently being played. Doesn't use voting yet.""",
        name="skip"
    )
    async def skip(self, ctx):
        await self.player.skip(ctx)


    @commands.command(
        brief="Pauses music player",
        name="pause"
    )
    async def pause(self, ctx):
        await self.player.pause(ctx)


    @commands.command(
        brief="Resumes the last song being played",
        name="resume"
    )
    async def resume(self, ctx):
        await self.player.resume(ctx)


    @commands.command(
        brief="Stops the song currently being played",
        help="""Stops the song currently being played. You cannot resume play of this song.
        When you request to play a new song, it will start playing whatever was next
        in the queue.""",
        name="stop"
    )
    async def stop(self, ctx):
        await self.player.stop(ctx)