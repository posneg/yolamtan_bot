from discord.ext import tasks, commands
from bot import yolamtanbot
from bot.music_player.player import Player

# Manages all of the players. 
# Handles requests directly from discord, passing them along to their appropriate players
class PlayerCog(commands.Cog):

    def __init__(self, bot: yolamtanbot.YolamtanBot):
        self.players = {}
        self.bot = bot
        self.bot.bot_logger.debug('Initializing player cog')

        self.check_for_dead_players.start()
        
    async def create_player_if_needed(self, guild_id, ctx):
        if not guild_id in self.players.keys():
            self.bot.bot_logger.debug('Creating new player for guild id: %s', guild_id)
            self.players[guild_id] = Player(guild_id, self.bot, ctx)

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
            await self.create_player_if_needed(ctx.message.guild.id, ctx)
            channel = ctx.message.author.voice.channel
            await ctx.send("Hello! :notes:")
  
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
        await ctx.send("Goodbye :wave:")
        if (ctx.voice_client):
            await ctx.voice_client.disconnect()
        self.players.pop(ctx.message.guild.id)
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
        await self.create_player_if_needed(ctx.message.guild.id, ctx)

        await self.players[ctx.message.guild.id].play_local_song(ctx, song_name, filter)

    
    @commands.command(
        brief="Plays a single song from a url",
        help="""Plays a single song given a youtube link. If a song is already playing,
        it adds the song to a queue to be played when the current song ends. Will
        automatically add bot to a voice channel if its not in one already.""",
        name="play"
    )
    @commands.max_concurrency(1, per=commands.BucketType.guild, wait=True)
    async def play(self, ctx, *, search_input):
        self.bot.bot_logger.debug('Recieved play command with search input %s', search_input)
        await self.create_player_if_needed(ctx.message.guild.id, ctx)

        await self.players[ctx.message.guild.id].play(ctx, search_input)


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

    @tasks.loop(seconds=10.0)
    async def check_for_dead_players(self):
        self.bot.bot_logger.debug("Checking for dead players")
        players_to_delete = []

        for id in self.players:
            if not self.players[id].is_alive():
                self.bot.bot_logger.debug("Playing for server %s has elimated itself and will play no more.", id)
                players_to_delete.append(id)

        for id in players_to_delete:
            await self.leave_voice(self.players[id].get_ctx())



    @play.before_invoke
    @play_local.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")    