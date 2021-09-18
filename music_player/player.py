import discord
import ffmpeg
import queue
from datetime import datetime
import math
# I cannot figure out how to import the song file into here 
# from song import Song

# These filters should be in their own file ##################################
def nightcore(song_name):
    stream = ffmpeg.input(song_name+".mp3")
    stream = ffmpeg.filter(stream, 'asetrate', 44100*1.2)
    stream = ffmpeg.filter(stream, 'aresample', 44100)
    stream = ffmpeg.filter(stream, 'atempo', 1.0)
    stream = ffmpeg.output(stream, song_name+'_nightcore.mp3')
    stream.run(overwrite_output=True)

    audio_source = discord.FFmpegPCMAudio(song_name+'_nightcore.mp3')
    return audio_source


def smothered(song_name):
    stream = ffmpeg.input(song_name+".mp3")
    stream = ffmpeg.filter(stream, "firequalizer", "if(lt(f,1000), 0, -INF)")
    stream = ffmpeg.output(stream, song_name+'_smothered.mp3')
    stream.run(overwrite_output=True)

    audio_source = discord.FFmpegPCMAudio(song_name+'_smothered.mp3')
    return audio_source


def bassboost(song_name):
    stream = ffmpeg.input(song_name+'.mp3')
    stream = ffmpeg.filter(stream, "bass", gain=15)
    stream = ffmpeg.output(stream, song_name+'_bassboost.mp3')
    stream.run(overwrite_output=True)

    audio_source = discord.FFmpegPCMAudio(song_name+'_bassboost.mp3')
    return audio_source


def chipmunk(song_name):
    stream = ffmpeg.input(song_name+'.mp3')
    stream = ffmpeg.filter(stream, 'asetrate', 44100*1.4)
    stream = ffmpeg.filter(stream, 'aresample', 44100)
    stream = ffmpeg.filter(stream, 'atempo', 1.05)
    stream = ffmpeg.output(stream, song_name+'_chipmunk.mp3')
    stream.run(overwrite_output=True)
        
    audio_source = discord.FFmpegPCMAudio(song_name+'_chipmunk.mp3')
    return audio_source


def deep(song_name):
    stream = ffmpeg.input(song_name+".mp3")
    stream = ffmpeg.filter(stream, 'asetrate', 44100*.8)
    stream = ffmpeg.filter(stream, 'aresample', 44100)
    stream = ffmpeg.filter(stream, 'atempo', 1.2)
    stream = ffmpeg.output(stream, song_name+'_deep.mp3')
    stream.run(overwrite_output=True)

    audio_source = discord.FFmpegPCMAudio(song_name+'_deep.mp3')
    return audio_source


def deeper(song_name):
    stream = ffmpeg.input(song_name+".mp3")
    stream = ffmpeg.filter(stream, 'asetrate', 44100*.6)
    stream = ffmpeg.filter(stream, 'aresample', 44100)
    stream = ffmpeg.filter(stream, 'atempo', 1.2)
    stream = ffmpeg.output(stream, song_name+'_deeper.mp3')
    stream.run(overwrite_output=True)

    audio_source = discord.FFmpegPCMAudio(song_name+'_deeper.mp3')
    return audio_source


filters = {
    'nightcore': nightcore,
    'smothered': smothered,
    'bassboost': bassboost,
    'chipmunk': chipmunk,
    'deep': deep,
    'deeper': deeper
}

## End filter functions ############################


## Start song class #########################
class Song:
    def __init__(self, audio_source, title="", duration=0.0):
        self.audio_source = audio_source
        self.title = title
        self.duration = float(duration)


    def get_audio_source(self):
        return self.audio_source


    def get_title(self):
        return self.title


    # In seconds
    def get_duration(self):
        return self.duration

    
    def get_duration_formatted(self):
        minutes = math.floor(self.duration/60.0)
        seconds = math.floor(self.duration%60.0)
        seconds_tenth_place = math.floor(seconds/10)
        seoncds_first_place = math.floor(seconds%10)
        return str(minutes) + "." + str(seconds_tenth_place) + str(seoncds_first_place) + " min"


################# END SONG class ######################################


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


    async def play_song(self, ctx, song_name, filter):
        song = self.create_audio_source(song_name, filter)
        self.music_queue.put(song)
        await ctx.send("Added "+song_name+" to queue. Duration: "+song.get_duration_formatted())

        self.play_next_song_in_queue(ctx)


    def play_next_song_in_queue(self, ctx):
        vc = ctx.voice_client

        def after_song_end(error):
            if not error and not vc.is_paused() and not vc.is_playing() and not self.music_queue.empty():
                vc.play(self.music_queue.get().get_audio_source(), after=after_song_end)

        if not vc.is_playing() and not self.music_queue.empty():
            song = self.music_queue.get()
            vc.play(song.get_audio_source(), after=after_song_end)
            self.current_song = song


    def create_audio_source(self, song_name, filter_name):
        if ("" != filter_name):
            audio_source = filters[filter_name](song_name)
            duration = ffmpeg.probe(song_name+"_"+filter_name+".mp3")['format']['duration']
        else:
            audio_source = discord.FFmpegPCMAudio(song_name+".mp3", options='-vn -b:a 128k -af bass=g=2')
            duration = ffmpeg.probe(song_name+".mp3")['format']['duration']

        return Song(audio_source, song_name, duration)


    async def skip(self, ctx):
        vc = ctx.voice_client
        if vc.is_playing():
            if not self.music_queue.empty():
                vc.stop()
                self.play_next_song_in_queue(ctx) 
            else:
                await ctx.send("There are no more songs in the queue!")


    async def pause(self, ctx):
        vc = ctx.voice_client
        if vc.is_playing():
            vc.pause()
        else:
            await ctx.send("The bot is not playing anything right now.")


    async def resume(self, ctx):
        vc = ctx.voice_client
        if vc.is_paused():
            vc.resume()
        else:
            await ctx.send("The bot was not playing anything before this. Use play_song command.")


    async def stop(self, ctx):
        vc = ctx.voice_client
        if vc.is_playing():
            vc.stop()
        else:
            await ctx.send("The bot is not playing anything right now.")


