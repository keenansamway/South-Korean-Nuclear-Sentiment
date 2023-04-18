"""

This class downloads an audio stream (.mp4 file) from a YouTube video.
It utilizes the pytube library to access the YouTube video streams.

PyTube Documentation: # https://pytube.io/en/latest/index.html

"""


import os
import pandas as pd
from pytube import YouTube

class YoutubeVideoDownloader():
    def __init__(self):
        pass
    
    def download_audio(self, video_url, output_path, prefix='audio_', filename=None):
        try:
            # Get the video object
            video = YouTube(video_url)
                                 
            # Download the audio stream (highest abr available)
            stream = video.streams.filter(only_audio=True, file_extension='mp4')
            
            stream = stream.order_by('abr').asc().first()
            #stream = stream.get_by_itag(140)
            
            filename = stream.download(
                output_path=output_path,
                filename=filename,
                filename_prefix=prefix)
            
            print(f"Downloaded audio file: {filename}")
                   
            return True
        
        except Exception as e:
            print(e)
            return False

if __name__ == '__main__':
    video_url = 'https://www.youtube.com/watch?v=9bZkp7q19f0'
    output_path = 'content/audio'
    
    yt = YoutubeVideoDownloader()
    yt.download_audio(video_url=video_url, output_path=output_path)