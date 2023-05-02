import math

class Song:
    def __init__(self, url, search_input, title="", duration=0.0):
        self.url = url
        self.audio_source = None
        self.title = title
        self.duration = float(duration)
        self.search_input = search_input


    def get_search_input(self):
        return self.search_input


    def get_url(self):
        return self.url


    def set_audio_source(self, source):
        self.audio_source = source


    def get_audio_source(self):
        return self.audio_source


    def get_title(self):
        return self.title


    # In seconds
    def get_duration(self):
        return self.duration


    def get_duration_formatted(self):
        if (0 != self.duration or "" != self.duration):
            minutes = math.floor(self.duration/60.0)
            seconds = math.floor(self.duration%60.0)
            seconds_tenth_place = math.floor(seconds/10)
            seoncds_first_place = math.floor(seconds%10)
            return str(minutes) + "." + str(seconds_tenth_place) + str(seoncds_first_place) + " min"
        else:
            return "Unknown"


    
    