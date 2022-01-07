import discord
from discord.ext import commands
import ffmpeg
import queue

from bot.music_player.filters import filters
from bot.music_player import song

# Used for ytdl
import asyncio
import youtube_dl

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
    'options': '-vn -b:a 128k -af bass=g=2'
}

## Does it matter if ytdl is not player specific?
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
###########

class Player:
    def __init__(self, guild_id):
        self.guild_id = guild_id
        self.music_queue = queue.Queue()
        self.current_song = None


    def __str__(self):
        return "{Id: " + self.guild_id + "}"


    def get_guild_id(self):
        return self.guild_id


    def get_current_song(self):
        return self.current_song


    async def play_local_song(self, ctx, song_name, filter):
        local_song = self.create_local_audio_source(song_name, filter)
        self.music_queue.put(local_song)
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
    async def play(self, ctx, url, filter_name):
        async with ctx.typing():
            if ("" != filter_name):
                yt_object = await YTDLSource.from_url(url)
                file = yt_object['file']
                title = yt_object['data']['title']
                filename = file[:-4]
                extension = file[-3:]

                audio_source = filters[filter_name](filename,extension)
                duration = ffmpeg.probe(filename+"_"+filter_name+"."+extension)['format']['duration']
            else: # Same as with filter but doesn't pre-download.
                yt_object = await YTDLSource.from_url(url, stream=True)
                url_player = yt_object['file']
                title = yt_object['data']['title']

                audio_source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url_player, **ffmpeg_options))
                duration = yt_object['data']['duration']
            
            yt_song = song.Song(audio_source, title, duration)
            self.music_queue.put(yt_song)
        
            await ctx.send("Added "+title+" to queue. Duration: "+yt_song.get_duration_formatted())

            self.play_next_song_in_queue(ctx)


    def play_next_song_in_queue(self, ctx):
        vc = ctx.voice_client

        def after_song_end(error):
            if not error and not vc.is_paused() and not vc.is_playing() and not self.music_queue.empty():
                vc.play(self.music_queue.get().get_audio_source(), after=after_song_end)

        if not vc.is_playing() and not self.music_queue.empty():
            current_song = self.music_queue.get()
            vc.play(current_song.get_audio_source(), after=after_song_end)
            self.current_song = current_song


    async def skip(self, ctx):
        vc = ctx.voice_client
        if vc.is_playing():
            try:
                vc.stop()
                self.play_next_song_in_queue(ctx) 
            except:
                await ctx.send("Encountered a problem trying to skip!")

    async def get_current_song(self, ctx):
        vc = ctx.message.guild.voice_client
        if vc.is_playing:
            await ctx.send("Current song is "+self.current_song.get_title())
        else:
            await ctx.send("No song is playing")


    async def pause(self, ctx):
        vc = ctx.message.guild.voice_client
        if vc.is_playing():
            vc.pause()
        else:
            await ctx.send("The bot is not playing anything right now.")


    async def resume(self, ctx):
        vc = ctx.message.guild.voice_client
        if vc.is_paused():
            vc.resume()
        else:
            await ctx.send("The bot was not playing anything before this. Use play_local_song command.")


    async def stop(self, ctx):
        vc = ctx.message.guild.voice_client
        if vc.is_playing():
            vc.stop()
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
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        #return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
        return {'file': filename, 'data': data}