import math
import random
from xmlrpc import client
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from bot import yolamtanbot


class SpotifyControls:
    def __init__(self, bot: yolamtanbot.YolamtanBot):
        self.bot = bot
        auth_manager = SpotifyClientCredentials(client_id=bot.env['spotify_client_id'], client_secret=bot.env['spotify_client_secret'])
        self.sp = spotipy.Spotify(auth_manager=auth_manager)

    # Returns random song name and artist as a string
    def get_random_song(self):
        random_offset = math.floor(random.random() * 999)
        random_search = self.get_random_search_string()

        self.bot.bot_logger.debug('Retrieving random song from search string: %s and offset %s', random_search, random_offset)

        result = self.sp.search(q=random_search, type='track', offset=random_offset, limit=1)

        song_url = result['tracks']['items'][0]['external_urls']['spotify']
        song_name = result['tracks']['items'][0]['name']
        artist = result['tracks']['items'][0]['artists'][0]['name']

        self.bot.bot_logger.debug('Random song request returned song %s by %s. URL: %s', song_name, artist, song_url)

        return song_name + ' ' + artist

    def get_random_search_string(self):
        # A list of all characters that can be chosen.
        characters = 'abcdefghijklmnopqrstuvwxyz'

        # Gets a random character from the characters string.
        random_char = characters[(math.floor(random.random() * len(characters)))]
        random_search_str = ''

        # Places the wildcard character at the beginning, or both beginning and end, randomly.
        if (round(random.random()) == 0):
            random_search_str = random_char + '%20'
        else:
            random_search_str = random_char + '%20'
        
        return random_search_str


