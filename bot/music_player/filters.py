import ffmpeg
import discord

def nightcore(filename, extension):
    stream = ffmpeg.input(filename+"."+extension)
    stream = ffmpeg.filter(stream, 'asetrate', 44100*1.2)
    stream = ffmpeg.filter(stream, 'aresample', 44100)
    stream = ffmpeg.filter(stream, 'atempo', 1.0)
    stream = ffmpeg.output(stream, filename+'_nightcore.'+extension)
    stream.run(overwrite_output=True)

    audio_source = discord.FFmpegPCMAudio(filename+'_nightcore.'+extension)
    return audio_source


def smothered(filename, extension):
    stream = ffmpeg.input(filename+"."+extension)
    stream = ffmpeg.filter(stream, "firequalizer", "if(lt(f,1000), 0, -INF)")
    stream = ffmpeg.output(stream, filename+'_smothered.'+extension)
    stream.run(overwrite_output=True)

    audio_source = discord.FFmpegPCMAudio(filename+'_smothered.'+extension)
    return audio_source


def bassboost(filename, extension):
    stream = ffmpeg.input(filename+"."+extension)
    stream = ffmpeg.filter(stream, "bass", gain=15)
    stream = ffmpeg.output(stream, filename+'_bassboost.'+extension)
    stream.run(overwrite_output=True)

    audio_source = discord.FFmpegPCMAudio(filename+'_bassboost.'+extension)
    return audio_source


def chipmunk(filename, extension):
    stream = ffmpeg.input(filename+"."+extension)
    stream = ffmpeg.filter(stream, 'asetrate', 44100*1.4)
    stream = ffmpeg.filter(stream, 'aresample', 44100)
    stream = ffmpeg.filter(stream, 'atempo', 1.05)
    stream = ffmpeg.output(stream, filename+'_chipmunk.'+extension)
    stream.run(overwrite_output=True)
        
    audio_source = discord.FFmpegPCMAudio(filename+'_chipmunk.'+extension)
    return audio_source


def deep(filename, extension):
    stream = ffmpeg.input(filename+"."+extension)
    stream = ffmpeg.filter(stream, 'asetrate', 44100*.8)
    stream = ffmpeg.filter(stream, 'aresample', 44100)
    stream = ffmpeg.filter(stream, 'atempo', 1.2)
    stream = ffmpeg.output(stream, filename+'_deep.'+extension)
    stream.run(overwrite_output=True)

    audio_source = discord.FFmpegPCMAudio(filename+'_deep.'+extension)
    return audio_source


def deeper(filename, extension):
    stream = ffmpeg.input(filename+"."+extension)
    stream = ffmpeg.filter(stream, 'asetrate', 44100*.6)
    stream = ffmpeg.filter(stream, 'aresample', 44100)
    stream = ffmpeg.filter(stream, 'atempo', 1.2)
    stream = ffmpeg.output(stream, filename+'_deeper.'+extension)
    stream.run(overwrite_output=True)

    audio_source = discord.FFmpegPCMAudio(filename+'_deeper.'+extension)
    return audio_source


filters = {
    'nightcore': nightcore,
    'smothered': smothered,
    'bassboost': bassboost,
    'chipmunk': chipmunk,
    'deep': deep,
    'deeper': deeper
}
