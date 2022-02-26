import os
import json
import typing

from pyyoutube import Api, PlaylistItem
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled


class YoutubeScraper:
    def __init__(
            self,
            api_key_dir: typing.Optional[str] = './api_key.txt',
            cache_dir: typing.Optional[str] = None,
    ):
        with open(api_key_dir, "r+") as file:
            api_key = file.read()
        self.py_youtube_api = Api(api_key=api_key)
        self.cache_dir = cache_dir

    def transcript_html_from_playlist(
            self,
            playlist_id: str,
            sep: str = '\n',
    ) -> str:
        return sep.join(
            self.transcript_html_lines_from_playlist_id(playlist_id)
        )

    def transcript_html_lines_from_playlist_id(
            self,
            playlist_id: str,
    ) -> typing.List[str]:
        transcript_dicts = self.transcript_dicts_from_playlist_id(playlist_id)
        lines = []
        for transcript_dict in transcript_dicts:
            id = transcript_dict['video_id']
            title = transcript_dict['video_title']
            transcript = transcript_dict['transcript']

            lines.append(f'<h1>{title}</h1>')
            lines.extend([
                self.srt_line_to_link(
                    video_id=id,
                    text=_srt['text'],
                    start=_srt['start']
                ) for _srt in transcript
            ])
        return lines

    def transcript_dicts_from_playlist_id(
            self,
            playlist_id: str,
            print_status: bool = True,
    ) -> typing.List[dict]:
        dicts = []
        playlist_items = self.playlist_items_from_playlist_id(playlist_id)
        for i, playlist_item in enumerate(playlist_items):
            if print_status:
                print(f"Scraping video {i + 1}/{len(playlist_items)}...", end='\r')
            this_dict = self.transcript_dict_from_playlist_item(playlist_item)
            dicts.append(this_dict)
        return dicts

    def check_cache_dir_defined(self):
        if not self.cache_dir:
            raise ValueError("No cache directory input.")

    def cache_file_dir(
            self,
            file_name: str,
            ext: typing.Optional[str] = '',
    ) -> str:
        self.check_cache_dir_defined()
        return os.path.join(
            self.cache_dir,
            file_name + ext,
        )

    def read_json_from_cache(
            self,
            file_name: str,
    ):
        self.check_cache_dir_defined()
        cache_file_dir = self.cache_file_dir(file_name, '.json')
        if os.path.isfile(cache_file_dir):
            with open(cache_file_dir) as file:
                return json.load(file)
        else:
            return None

    def write_json_to_cache(
            self,
            d: dict,
            file_name: str,
    ):
        self.check_cache_dir_defined()
        cache_file_dir = self.cache_file_dir(file_name, '.json')
        with open(cache_file_dir, 'w') as file:
            json.dump(d, file)

    def transcript_dict_from_playlist_item(
            self,
            playlist_item: PlaylistItem,
    ) -> dict:
        file_name = playlist_item.snippet.resourceId.videoId

        if local_json := self.read_json_from_cache(file_name):
            return local_json

        d = {}
        d['video_id'] = file_name
        this_video_title = playlist_item.snippet.title
        d['video_title'] = this_video_title
        srt = self.get_transcript(file_name)
        d['transcript'] = srt

        if self.cache_dir:
            self.write_json_to_cache(d, file_name)

        return d

    @staticmethod
    def srt_line_to_link(
            video_id: str,
            text: str,
            start: float,
    ) -> str:
        return f'<a href="https://youtu.be/{video_id}?t={int(start)}">{text}</a>'

    def playlist_items_from_playlist_id(
            self,
            playlist_id: str,
    ) -> typing.List[PlaylistItem]:
        return self.py_youtube_api.get_playlist_items(
            playlist_id=playlist_id,
            count=None
        ).items

    @staticmethod
    def get_transcript(
            video_id: str,
    ) -> typing.List[dict]:
        try:
            srt = YouTubeTranscriptApi.get_transcript(video_id)
        except TranscriptsDisabled as e:
            srt = []
        return srt
