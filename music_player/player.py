import discord
import ffmpeg

# Unsused as of now. Start of a possible music player class
class Player:
  def __init__(self, guild_id):
    self.guild_id = guild_id

  def play_song(ctx):
    audio_source = discord.FFmpegPCMAudio('sweet.mp3')
    if not ctx.voice_client.is_playing():
        ctx.voice_client.play(audio_source, after=None)

  async def play_song_nightcore(ctx, song_name):
    inn = ffmpeg.input(song_name)
        
    filtered = (inn.filter('asetrate', 44100*1.2).filter('aresample', 44100).filter('atempo',1.0))
    outt = ffmpeg.output(filtered, song_name+'_nightcore.mp3')
    outt.run(overwrite_output=True)

    audio_source = discord.FFmpegPCMAudio(song_name+'_nightcore.mp3')
    if not ctx.voice_client.is_playing():
        ctx.voice_client.play(audio_source, after=None)