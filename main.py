from pyyoutube import Api
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled


class YoutubeScraper:
    def __init__(self, api_key_dir='./api_key.txt'):
        with open(api_key_dir, "r+") as file:
            api_key = file.read()
        self.py_youtube_api = Api(api_key=api_key)

    def transcript_html_from_playlist(self, playlist_id, sep='\n'):
        return sep.join(
            self.transcript_html_lines_from_playlist(playlist_id)
        )

    def transcript_html_lines_from_playlist(self, playlist_id):
        transcripts = self.transcript_dict_from_playlist(playlist_id)
        lines = []
        for id, title, transcript in zip(*transcripts):
            lines.append(f'<h1>{title}</h1>')
            lines.extend([
                self.srt_line_to_link(
                    video_id=id,
                    text=_srt['text'],
                    start=_srt['start']
                ) for _srt in transcript
            ])
        return lines


        html = '\n'.join(lines)
        # with open(output_html, "w") as file1:
        #     file1.writelines(all_lines)
        x = 2

    def transcript_dict_from_playlist(self, playlist_id):
        ids = []
        titles = []
        transcripts = []
        playlist_items = self.playlist_items_from_playlist_id(playlist_id)
        for i, video in enumerate(playlist_items):
            print(f"Scraping video {i + 1}/{len(playlist_items)}...", end='\r')
            this_video_id = video.snippet.resourceId.videoId
            ids.append(this_video_id)
            titles.append(video.snippet.title)

            # these_lines = [f'<h1>{video.snippet.title}</h1>\n']
            srt = self.get_transcript(this_video_id)
            transcripts.append(srt)
            # srt_lines_formatted = [
            #     self.srt_line_to_link(
            #         video_id=this_video_id,
            #         text=_srt['text'],
            #         start=_srt['start']
            #     ) for _srt in srt
            # ]
        return ids, titles, transcripts

    def srt_line_to_link(self, video_id, text, start):
        return f'<a href="https://youtu.be/{video_id}?t={int(start)}">{text}</a><br>'

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
