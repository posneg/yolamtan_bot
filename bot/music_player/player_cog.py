from discord.ext import commands

from bot import yolamtanbot

#import bot.music_player.player
from bot.music_player.player import Player

# Manages all of the players. 
# Handles requests directly from discord, passing them along to their appropriate players
class PlayerCog(commands.Cog):

    def __init__(self, bot: yolamtanbot.YolamtanBot):
        self.bot.bot_logger.debug('Initializing player cog')
        self.players = {}
        self.bot = bot

    def create_player_if_needed(self, guild_id):
        if not guild_id in self.players.keys():
            self.bot.bot_logger.debug('Creating new player for guild id: %s', guild_id)
            self.players[guild_id] = Player(guild_id, self.bot)

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
            self.create_player_if_needed(ctx.message.guild.id)
            channel = ctx.message.author.voice.channel
  
        self.bot.bot_logger.debug('Attempting to connect to channel in guild id: %s', ctx.message.guild.id)
        await channel.connect()


    @commands.command(
        brief="Removes bot from voice channel",
        help="""Removes the bot from whichever voice channel it is currently in.""",
        name="leave_voice"
    )
    async def leave_voice(self, ctx):
        # Add some kind of error handling for when the bot is disconnected by force? 
        # It gets buggy if the bot isn't disconnected through here
        await ctx.voice_client.disconnect()
        del self.players[ctx.message.guild.id]
        self.bot.bot_logger.debug('Disconnected and deleted player in guild id: %s', ctx.message.guild.id)


    @commands.command(
        brief="Plays a single song",
        help="""Plays a single song given an mp3's name. If a song is already playing,
        it adds the song to a queue to be played when the current song ends. Will
        automatically add bot to a voice channel if its not in one already.""",
        name="play_local"
    )
    async def play_local(self, ctx, song_name, filter=""):
        self.bot.bot_logger.debug('Recieved play_local command on song %s', song_name)
        self.create_player_if_needed(ctx.message.guild.id)

        await self.players[ctx.message.guild.id].play_local_song(ctx, song_name, filter)

    
    @commands.command(
        brief="Plays a single song from a url",
        help="""Plays a single song given a youtube link. If a song is already playing,
        it adds the song to a queue to be played when the current song ends. Will
        automatically add bot to a voice channel if its not in one already.""",
        name="play"
    )
    async def play(self, ctx, url):
        self.bot.bot_logger.debug('Recieved play command on url %s', url)
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