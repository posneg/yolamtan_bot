from async_timeout import timeout
import discord
from discord.ext import commands
import ffmpeg
from threading import Lock

from bot.music_player.filters import filters
from bot.music_player import song

# Used for ytdl
import asyncio
import yt_dlp
from bot import yolamtanbot

# Suppress noise about console usage from errors
yt_dlp.utils.bug_reports_message = lambda: ''

#### YTDL OPTIONS
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

# 'options': '-vn -b:a 128k -af bass=g=2'
ffmpeg_options = {
    'options': '-vn -b:a 256k -af bass=g=2'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)
###########

class Player:
    def __init__(self, guild_id, bot: yolamtanbot.YolamtanBot, ctx: commands.Context):
        self.guild_id = guild_id
        self.music_queue = asyncio.Queue()
        self.next = asyncio.Event() 
        self.current_song = None
        self._ctx = ctx  # context the bot was created in
        self.bot = bot
        self.lock = Lock()
        self.alive = True
        self.volume = 0.5
        self.bot.bot_logger.debug('Inititalizing player for guild id: %s', guild_id)
        
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.play_music())


    def __str__(self):
        return "{Id: " + self.guild_id + "}"


    async def play_local_song(self, ctx, song_name, filter):
        self.bot.bot_logger.debug('Attempting to play local song: %s', song_name)
        local_song = self.create_local_audio_source(song_name, filter)
        await self.music_queue.put(local_song)
        self.bot.bot_logger.debug('Added local song %s to queue', song_name)
        await ctx.send("Added "+song_name+" to queue. Duration: "+local_song.get_duration_formatted())


    def create_local_audio_source(self, song_name, filter_name):
        if ("" != filter_name):
            audio_source = filters[filter_name](song_name,"mp3")
            duration = ffmpeg.probe(song_name+"_"+filter_name+".mp3")['format']['duration']
        else:
            audio_source = discord.FFmpegPCMAudio(song_name+".mp3", **ffmpeg_options)
            duration = ffmpeg.probe(song_name+".mp3")['format']['duration']

        return song.Song(audio_source, song_name, duration)


    # Plays from a url (almost anything yt_dlp supports)
    async def play(self, ctx, search_input):
        async with ctx.typing():
            # Unusued filter code, will be used in a seperate filter-supported command
            # if ("" != filter_name):
            #     self.bot.bot_logger.debug('Filter parameter %s given', filter_name)
            #     self.bot.bot_logger.debug('Getting audio from url: %s', url)
            #     yt_object = await YTDLSource.from_url(url)
            #     file = yt_object['file']
            #     title = yt_object['data']['title']
            #     filename = ''.join(file.split('.')[:-1])
            #     extension = file.split('.')[-1]
            #     self.bot.bot_logger.debug('Retrieved song: %s', title)

            #     audio_source = filters[filter_name](filename,extension)
            #     self.bot.bot_logger.debug('Retrieved audio source for filtered song %s', title)
            #     duration = ffmpeg.probe(filename+"_"+filter_name+"."+extension)['format']['duration']


            # Still getting youtube url here so that we can get song info and return the retrieved song to chat
            self.bot.bot_logger.debug('Getting audio from search input: %s', search_input)
            yt_object = await YTDLSource.from_url(search_input, stream=True)
            url = yt_object['player_url']
            title = yt_object['data']['title']
            self.bot.bot_logger.debug('Retrieved song: %s', title)

            duration = yt_object['data']['duration']
            
            yt_song = song.Song(url, search_input, title, duration)
            await self.music_queue.put(yt_song)
            self.bot.bot_logger.debug('Added %s to queue', title)
        
            await ctx.send("Added **"+title+"** to queue.\nDuration: "+yt_song.get_duration_formatted()+"")


    async def play_music(self):
        while True:
            self.next.clear()

            try:
                # 30 minutes of no songs and bot times out
                async with timeout(1800):
                    self.bot.bot_logger.debug("Looking for next song in the queue")
                    self.current_song = await self.music_queue.get()
            except asyncio.TimeoutError:
                await self.die()
                return

            self.bot.bot_logger.debug("Playing song %s", self.current_song.get_title())

            # Youtube streams expire so we have to get it here
            self.bot.bot_logger.debug('Getting audio from url again: %s', self.current_song.get_url())
            yt_object = await YTDLSource.from_url(self.current_song.get_search_input(), stream=True)
            title = yt_object['data']['title']
            self.bot.bot_logger.debug('Retrieved song: %s again', title)
            audio_source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(source=yt_object['player_url'], **ffmpeg_options))
            audio_source.volume = self.volume
            self.current_song.set_audio_source(audio_source)
            self.bot.bot_logger.debug('Audio source retrieved for %s', self.current_song.get_title())

            self._ctx.voice_client.play(audio_source, after=self.play_next_song)
            
            # Wait here until self.next.set() is called
            await self.next.wait()


    def play_next_song(self, error=None):
        self.bot.bot_logger.debug('Ended song %s', self.current_song.get_title())
        self.current_song.get_audio_source().cleanup()
        self.current_song = None

        if error:
            self.bot.bot_logger.error('Encountered error in playing next song %s', error)
        
        # Attempt to play next song
        self.next.set()
            

    async def skip(self, ctx):
        self.bot.bot_logger.debug('Attempting to skip')
        self.lock.acquire()
        vc = ctx.voice_client
        if vc.is_playing():
            vc.stop()
            self.bot.bot_logger.debug('Stopped current song. Callback should start next song.')
        self.lock.release()


    async def pause(self, ctx):
        self.bot.bot_logger.debug('Attempting to pause')
        self.lock.acquire()
        vc = ctx.message.guild.voice_client
        if vc.is_playing():
            vc.pause()
            self.bot.bot_logger.debug('Paused voice client')
        else:
            await ctx.send("The bot is not playing anything right now.")
        self.lock.release()


    async def resume(self, ctx):
        self.bot.bot_logger.debug('Attempting to resume song')
        self.lock.acquire()
        vc = ctx.message.guild.voice_client
        if vc.is_paused():
            vc.resume()
            self.bot.bot_logger.debug('Resumed song')
        else:
            await ctx.send("The bot was not playing anything before this. Use play command.")
        self.lock.release()


    # Removes bot from voice channel from within the player
    async def die(self):
        self.bot.bot_logger.debug("Killing player for guild %s with die function", self.guild_id)
        self.alive = False
        self.music_queue._queue.clear()

    def is_alive(self):
        return self.alive

    def get_ctx(self):
        return self._ctx

    def get_guild_id(self):
        return self.guild_id

    def get_current_song(self):
        return self.current_song

    def get_queue_size(self):
        return self.music_queue.qsize()


    async def get_current_song(self, ctx):
        vc = ctx.message.guild.voice_client
        if vc.is_playing:
            await ctx.send("Now Playing: **"+self.current_song.get_title() + "**")
        else:
            await ctx.send("No song is playing")



class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(self, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        link = data['url'] if stream else ytdl.prepare_filename(data)
        return {'player_url': link, 'data': data}