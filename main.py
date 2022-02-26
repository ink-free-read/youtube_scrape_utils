import os
import json

from pyyoutube import Api
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled


class YoutubeScraper:
    def __init__(self, api_key_dir='./api_key.txt', cache_dir=None):
        with open(api_key_dir, "r+") as file:
            api_key = file.read()
        self.py_youtube_api = Api(api_key=api_key)
        self.cache_dir = cache_dir

    def transcript_html_from_playlist(self, playlist_id, sep='\n'):
        return sep.join(
            self.transcript_html_lines_from_playlist(playlist_id)
        )

    def transcript_html_lines_from_playlist(self, playlist_id):
        transcript_dicts = self.transcript_dicts_from_playlist_id(playlist_id)
        lines = []
        for transcipt_dict in transcript_dicts:
            id = transcipt_dict['video_id']
            title = transcipt_dict['video_title']
            transcript = transcipt_dict['transcript']

            lines.append(f'<h1>{title}</h1>')
            lines.extend([
                self.srt_line_to_link(
                    video_id=id,
                    text=_srt['text'],
                    start=_srt['start']
                ) for _srt in transcript
            ])
        return lines

    def transcript_dicts_from_playlist_id(self, playlist_id):
        dicts = []
        playlist_items = self.playlist_items_from_playlist_id(playlist_id)
        for i, playlist_item in enumerate(playlist_items):
            print(f"Scraping video {i + 1}/{len(playlist_items)}...", end='\r')
            this_dict = self.transcript_dict_from_playlist(playlist_item)
            #if this_dict['transcript'] and self.cache_dir:

            dicts.append(this_dict)
        return dicts

    def check_cache_dir_defined(self):
        if not self.cache_dir:
            raise ValueError("No cache directory input.")

    def cache_file_dir(self, file_name, ext=''):
        self.check_cache_dir_defined()
        return os.path.join(
            self.cache_dir,
            file_name + ext,
        )

    def read_json_from_cache(self, fn):
        self.check_cache_dir_defined()
        cache_file_dir = self.cache_file_dir(fn, '.json')
        if os.path.isfile(cache_file_dir):
            with open(cache_file_dir) as file:
                return json.load(file)
        else:
            return None

    def write_json_to_cache(self, fn):
        self.check_cache_dir_defined()
        cache_file_dir = self.cache_file_dir(fn, '.json')
        with open(cache_file_dir, 'w') as file:
            json.dump(d, file)

    def transcript_dict_from_playlist(self, playlist_item):
        fn = playlist_item.snippet.resourceId.videoId

        if local_json := self.read_json_from_cache(fn):
            return local_json

        d = {}
        d['video_id'] = fn
        this_video_id = playlist_item.snippet.title
        d['video_title'] = this_video_id
        srt = self.get_transcript(fn)
        d['transcript'] = srt

        if self.cache_dir:
            self.write_json_to_cache(fn)

        return d

    def srt_line_to_link(self, video_id, text, start):
        return f'<a href="https://youtu.be/{video_id}?t={int(start)}">{text}</a>'

    def playlist_items_from_playlist_id(self, playlist_id):
        return self.py_youtube_api.get_playlist_items(
            playlist_id=playlist_id,
            count=None
        ).items

    def video_ids_from_playlist_id(self, playlist_id):
        playlist_items = self.playlist_items_from_playlist_id
        video_ids = [v.snippet.resourceId.videoId for v in playlist_items]
        return video_ids

    def get_transcript(self, video_id):
        try:
            srt = YouTubeTranscriptApi.get_transcript(video_id)
        except TranscriptsDisabled as e:
            srt = []
        return srt
