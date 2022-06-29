import discord
from discord.ext import commands
import ffmpeg
import queue

from bot.music_player.filters import filters
from bot.music_player import song

# Used for ytdl
import asyncio
import youtube_dl
from bot import yolamtanbot

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

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

## Does it matter if ytdl is not player specific?
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
###########

class Player:
    def __init__(self, guild_id, bot: yolamtanbot.YolamtanBot):
        self.guild_id = guild_id
        self.music_queue = queue.Queue()
        self.current_song = None
        self.bot = bot
        self.bot.bot_logger.debug('Inititalizing player for guild id: %s', guild_id)


    def __str__(self):
        return "{Id: " + self.guild_id + "}"


    def get_guild_id(self):
        return self.guild_id


    def get_current_song(self):
        return self.current_song


    async def get_current_song(self, ctx):
        vc = ctx.message.guild.voice_client
        if vc.is_playing:
            await ctx.send("Current song is "+self.current_song.get_title())
        else:
            await ctx.send("No song is playing")


    async def play_local_song(self, ctx, song_name, filter):
        self.bot.bot_logger.debug('Attempting to play local song: %s', song_name)
        local_song = self.create_local_audio_source(song_name, filter)
        self.music_queue.put(local_song)
        self.bot.bot_logger.debug('Added local song %s to queue', song_name)
        await ctx.send("Added "+song_name+" to queue. Duration: "+local_song.get_duration_formatted())

        self.play_next_song_in_queue(ctx)

    def create_local_audio_source(self, song_name, filter_name):
        if ("" != filter_name):
            audio_source = filters[filter_name](song_name,"mp3")
            duration = ffmpeg.probe(song_name+"_"+filter_name+".mp3")['format']['duration']
        else:
            audio_source = discord.FFmpegPCMAudio(song_name+".mp3", **ffmpeg_options)
            duration = ffmpeg.probe(song_name+".mp3")['format']['duration']

        return song.Song(audio_source, song_name, duration)

    # Plays from a url (almost anything youtube_dl supports)
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

            self.bot.bot_logger.debug('Getting audio from search input: %s', search_input)
            yt_object = await YTDLSource.from_url(search_input, stream=True)
            url_player = yt_object['file']
            title = yt_object['data']['title']
            self.bot.bot_logger.debug('Retrieved song: %s', title)

            audio_source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url_player, **ffmpeg_options))
            self.bot.bot_logger.debug('Audio source retrieved for %s', title)
            duration = yt_object['data']['duration']
            
            yt_song = song.Song(audio_source, title, duration)
            self.music_queue.put(yt_song)
            self.bot.bot_logger.debug('Added %s to queue', title)
        
            await ctx.send("Added "+title+" to queue. Duration: "+yt_song.get_duration_formatted())

            self.play_next_song_in_queue(ctx)


    def play_next_song_in_queue(self, ctx):
        vc = ctx.voice_client

        def after_song_end(error):
            self.bot.bot_logger.debug('Ended song')
            if not error and not vc.is_paused() and not vc.is_playing() and not self.music_queue.empty():
                current_song = self.music_queue.get()
                coro = vc.play(current_song.get_audio_source(), after=after_song_end)

                fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
                
                try:
                    fut.result()
                    self.bot.bot_logger.debug('Playing song from callback: %s', current_song.get_title())
                except:
                    self.bot.bot_logger.debug('Error occurred when trying to play next song in queue')
                    pass


        if not vc.is_playing() and not self.music_queue.empty():
            current_song = self.music_queue.get()
            self.bot.bot_logger.debug('Playing song: %s', current_song.get_title())
            vc.play(current_song.get_audio_source(), after=after_song_end)
            self.current_song = current_song
            

    async def skip(self, ctx):
        self.bot.bot_logger.debug('Attempting to skip')
        vc = ctx.voice_client
        if vc.is_playing():
            vc.stop()
            self.bot.bot_logger.debug('Stopped current song. Callback should start next song.')


    async def pause(self, ctx):
        vc = ctx.message.guild.voice_client
        self.bot.bot_logger.debug('Attempting to pause')
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


    async def stop(self, ctx):
        self.bot.bot_logger.debug('Attempting to stop voice client')
        vc = ctx.message.guild.voice_client
        if vc.is_playing():
            vc.stop()
            self.bot.bot_logger.debug('Stoped voice client')
        else:
            await ctx.send("The bot is not playing anything right now.")




class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data
        self.filename = ""

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(self, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return {'file': filename, 'data': data}