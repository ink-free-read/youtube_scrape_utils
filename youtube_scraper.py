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
        """Constructor for YoutubeScraper

        >>> scraper = YoutubeScraper("api_key.txt", cache_dir='./subtitles')
        >>> html = scraper.transcript_html_from_playlist(playlist_id)

        :param api_key_dir: Path to text file containing api key for use with YouTube v3 API.
        :param cache_dir: Cache dir for transcript JSON files.
                          Does not cache if not provided.
        """
        with open(api_key_dir, "r+") as file:
            api_key = file.read()
        self.py_youtube_api = Api(api_key=api_key)
        self.cache_dir = cache_dir

    def transcript_html_from_playlist(
            self,
            playlist_id: str,
            sep: str = '\n',
    ) -> str:
        """
        Returns HTML report including transcript of all videos in input playlist,
        with timestamped links to video on each transcript line.

        :param playlist_id: YouTube playlist ID to scrape videos from.
                            Passed to transcript_html_lines_from_playlist_id().
        :param sep: Separator to join individual transcript report lines
        :return: HTML report as string
        """
        return sep.join(
            self.transcript_html_lines_from_playlist_id(playlist_id)
        )

    def transcript_html_lines_from_playlist_id(
            self,
            playlist_id: str,
    ) -> typing.List[str]:
        """
        Returns HTML report lines including transcript of all videos in input
        playlist, with timestamped links to video on each transcript line.

        :param playlist_id: YouTube playlist ID to scrape videos from
        :return: HTML lines
        """
        transcript_dicts = self.transcript_dicts_from_playlist_id(playlist_id)
        lines = []
        for transcript_dict in transcript_dicts:
            id = transcript_dict['video_id']
            title = transcript_dict['video_title']
            transcript = transcript_dict['transcript']

            lines.append(f'<h1>{title}</h1>')
            lines.extend([
                self.transcript_line_to_link(
                    video_id=id,
                    text=_transcript['text'],
                    start=_transcript['start']
                ) for _transcript in transcript
            ])
        return lines

    def transcript_dicts_from_playlist_id(
            self,
            playlist_id: str,
            print_status: bool = True,
    ) -> typing.List[dict]:
        """
        Get information dictionaries from each video in playlist, including
        transcript.

        :param playlist_id: YouTube playlist ID to scrape videos from
        :param print_status: Boolean flag for whether to print status of
                             scraping. Helpful if cache is not used.
        :return: List of dictionaries with information on each video in
                 input playlist, including transcripts.
        """
        dicts = []
        playlist_items = self.playlist_items_from_playlist_id(playlist_id)
        for i, playlist_item in enumerate(playlist_items):
            if print_status:
                print(f"Scraping video {i + 1}/{len(playlist_items)}...", end='\r')
            this_dict = self.transcript_dict_from_playlist_item(playlist_item)
            dicts.append(this_dict)
        return dicts

    def check_cache_dir_defined(self):
        """
        Raises error if no cache_dir defined. Used to check before executing
        cache related functionality.
        """
        if not self.cache_dir:
            raise ValueError("No cache directory input.")

    def cache_file_dir(
            self,
            file_name: str,
            ext: typing.Optional[str] = '',
    ) -> str:
        """
        Returns full path to a cache file with a given file_name

        :param file_name: file_name inside self.cache_dir
        :param ext: extension, if desired
        :return: full path to cache file with this file_name
        """
        self.check_cache_dir_defined()
        return os.path.join(
            self.cache_dir,
            file_name + ext,
        )

    def read_json_from_cache(
            self,
            file_name: str,
    ) -> dict:
        """
        Reads JSON with file_name from cache

        :param file_name: JSON file_name to read
        :return: JSON as python object
        """
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
        """
        Writes JSON with file_name to cache

        :param d: Dictionary to write to JSON
        :param file_name: JSON file_name to write to
        :return: JSON as python object
        """
        self.check_cache_dir_defined()
        cache_file_dir = self.cache_file_dir(file_name, '.json')
        with open(cache_file_dir, 'w') as file:
            json.dump(d, file)

    def transcript_dict_from_playlist_item(
            self,
            playlist_item: PlaylistItem,
    ) -> dict:
        """
        Get information from this specific PlaylistItem (i.e. video) as
        dictionary, including transcript of PlaylistItem.

        :param playlist_item: PlaylistItem to source information on
        :return: Information dictionary of PlaylistItem
        """
        file_name = playlist_item.snippet.resourceId.videoId

        if local_json := self.read_json_from_cache(file_name):
            return local_json

        d = {}
        d['video_id'] = file_name
        this_video_title = playlist_item.snippet.title
        d['video_title'] = this_video_title
        transcript = self.get_transcript(file_name)
        d['transcript'] = transcript

        if self.cache_dir:
            self.write_json_to_cache(d, file_name)

        return d

    @staticmethod
    def transcript_line_to_link(
            video_id: str,
            text: str,
            start: float,
    ) -> str:
        """
        Default method to convert transcript line to html

        :param video_id: Video ID to link to in this html line
        :param text: Text to represent this link (likely the text from
                     the transcript)
        :param start: The start time of the caption, used to create URL to
                      direct timestamp in the desired video, via URL args.
        :return: HTML representation of timestamped transcript
        """
        return f'<a href="https://youtu.be/{video_id}?t={int(start)}">{text}</a>'

    def playlist_items_from_playlist_id(
            self,
            playlist_id: str,
    ) -> typing.List[PlaylistItem]:
        """
        Finds all PlaylistItems from the input playlist identified by
        playlist_id

        :param playlist_id: Playlist ID to source videos from
        :return: list of PlaylistItems in playlist with playlist_id
        """
        return self.py_youtube_api.get_playlist_items(
            playlist_id=playlist_id,
            count=None
        ).items

    @staticmethod
    def get_transcript(
            video_id: str,
    ) -> typing.List[dict]:
        """
        Finds transcript as list of dictionaries, or empty list if no
        transcripts can be found on this video.

        :param video_id: video_id to get transcript from
        :return: transcript representation
        """
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
        except TranscriptsDisabled as e:
            transcript = []
        return transcript
