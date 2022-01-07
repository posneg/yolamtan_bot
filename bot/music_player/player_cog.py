from discord import voice_client
from discord.ext import commands
from discord.player import FFmpegAudio
import ffmpeg

#import bot.music_player.player
from bot.music_player.player import Player

# Manages all of the players. 
# Handles requests directly from discord, passing them along to their appropriate players
class PlayerCog(commands.Cog):

    def __init__(self):
        self.players = {}

    def create_player_if_needed(self, guild_id):
        if not guild_id in self.players.keys():
            self.players[guild_id] = Player(guild_id)

    @commands.command(
        brief="Adds bot to voice channel",
        help="""Commands bot to join the voice channel the commanding user is in""",
        name="join_voice"
    )
    async def join_voice(self, ctx):
        if not ctx.message.author.voice:
            await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
            return
        elif ctx.voice_client and ctx.voice_client.is_connected():
            await ctx.send("Bot is already connected to a voice channel.")
            return
        else:
            self.create_player_if_needed(ctx.message.guild.id)
            channel = ctx.message.author.voice.channel
        await channel.connect()


    @commands.command(
        brief="Removes bot from voice channel",
        help="""Removes the bot from whichever voice channel it is currently in.""",
        name="leave_voice"
    )
    async def leave_voice(self, ctx):
        await ctx.voice_client.disconnect()
        del self.players[ctx.message.guild.id]


    @commands.command(
        brief="Plays a single song",
        help="""Plays a single song given an mp3's name. If a song is already playing,
        it adds the song to a queue to be played when the current song ends. Will
        automatically add bot to a voice channel if its not in one already.""",
        name="play_local"
    )
    async def play_local(self, ctx, song_name, filter=""):
        self.create_player_if_needed(ctx.message.guild.id)

        # if not ctx.voice_client or not ctx.voice_client.is_connected():
        #     await self.join_voice(ctx)

        await self.players[ctx.message.guild.id].play_local_song(ctx, song_name, filter)

    
    @commands.command(
        brief="Plays a single song from a url",
        help="""Plays a single song given a youtube link. If a song is already playing,
        it adds the song to a queue to be played when the current song ends. Will
        automatically add bot to a voice channel if its not in one already.""",
        name="play"
    )
    async def play(self, ctx, url, filter=""):
        self.create_player_if_needed(ctx.message.guild.id)

        await self.players[ctx.message.guild.id].play(ctx, url, filter)


    @commands.command(
        brief="Skips the current song",
        help="""Skips the song currently being played. Doesn't use voting yet.""",
        name="skip"
    )
    async def skip(self, ctx):
        await self.players[ctx.message.guild.id].skip(ctx)


    @commands.command(
        brief="Pauses music player",
        name="pause"
    )
    async def pause(self, ctx):
        await self.players[ctx.message.guild.id].pause(ctx)


    @commands.command(
        brief="Resumes the last song being played",
        name="resume"
    )
    async def resume(self, ctx):
        await self.players[ctx.message.guild.id].resume(ctx)


    @commands.command(
        brief="Stops the song currently being played",
        help="""Stops the song currently being played. You cannot resume play of this song.
        When you request to play a new song, it will start playing whatever was next
        in the queue.""",
        name="stop"
    )
    async def stop(self, ctx):
        await self.players[ctx.message.guild.id].stop(ctx)

    
    @play.before_invoke
    @play_local.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                #raise commands.CommandError("Author not connected to a voice channel.")