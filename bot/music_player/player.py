from async_timeout import timeout
from collections import deque
import discord
from discord.ext import commands
import ffmpeg

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
    'compat-options': 'format-sort', # audio plays clearer for me using the old youtube_dl "best" format opts
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
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -b:a 256k -af bass=g=2'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)
###########

class Player:
    def __init__(self, guild_id, bot: yolamtanbot.YolamtanBot, ctx: commands.Context):
        self.guild_id = guild_id
        self.music_queue = deque()
        self.queue_count = asyncio.Semaphore(value=0)
        self.next = asyncio.Event() 
        self.current_song = None
        self._ctx = ctx  # context the bot was created in
        self.bot = bot
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
        self.music_queue.append(local_song)
        self.queue_count.release()
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
    async def play(self, ctx, search_input, play_next=False):
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
            if not play_next:
                self.music_queue.append(yt_song)
            else:
                self.music_queue.appendleft(yt_song)
            self.bot.bot_logger.debug('Added %s to queue', title)

            self.queue_count.release()

            await ctx.send("Added **"+title+"** to queue.\nDuration: "+yt_song.get_duration_formatted()+"")


    async def play_music(self):
        while True:
            self.next.clear()

            try:
                # 30 minutes of no songs and bot times out
                async with timeout(1800):
                    self.bot.bot_logger.debug("Looking for next song in the queue")
                    await self.queue_count.acquire()
                    self.current_song = self.music_queue.popleft()
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
        vc = ctx.voice_client
        if vc.is_playing():
            vc.stop()
            self.bot.bot_logger.debug('Stopped current song. Callback should start next song.')


    async def pause(self, ctx):
        self.bot.bot_logger.debug('Attempting to pause')
        vc = ctx.message.guild.voice_client
        if vc.is_playing():
            vc.pause()
            self.bot.bot_logger.debug('Paused voice client')
        else:
            await ctx.send("The bot is not playing anything right now.")


    async def resume(self, ctx):
        self.bot.bot_logger.debug('Attempting to resume song')
        vc = ctx.message.guild.voice_client
        if vc.is_paused():
            vc.resume()
            self.bot.bot_logger.debug('Resumed song')
        else:
            await ctx.send("The bot was not playing anything before this. Use play command.")


    # Removes bot from voice channel from within the player
    async def die(self):
        self.bot.bot_logger.debug("Killing player for guild %s with die function", self.guild_id)
        self.alive = False
        self.music_queue.clear()

    def is_alive(self):
        return self.alive

    def get_ctx(self):
        return self._ctx

    def get_guild_id(self):
        return self.guild_id

    async def get_current_song(self, ctx):
        vc = ctx.message.guild.voice_client
        if self.current_song is not None:
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