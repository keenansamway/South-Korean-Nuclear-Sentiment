import os
import datetime
import pandas as pd

import whisper as OpenAIWhisper
from pytube import YouTube as PyTube
from googleapiclient.discovery import build

from config import YOUTUBE_API_KEY



class YouTubeHelper:
    """YouTube Helper Class
    
    Attributes:
        youtube (object): The YouTube API object.
        whisper_model (object): The OpenAI Whisper model.
        
    Public Methods:
        search (YouTube API): Search for videos based on a query term and date range.
        TODO: video_details (YouTube API): Get the details of a video.
        download_audio (PyTube): Download the audio of a list of videos.
        transcribe_audio (OpenAI Whisper): Transcribe a list of audio files.
        comments (YouTube API): Get the comments of a video.
    """
    
    def __init__(self, api_key, api_service_name="youtube", api_version="v3"):
        
        assert api_key is not None, "api_key must be provided"
        
        self.youtube = build(
            serviceName=api_service_name,
            version=api_version,
            developerKey=api_key
        )
        
        self.whisper_model = None
        
    #
    # Search Functions
    #
    
    def _search(self, **kwargs):
        return self.youtube.search().list(**kwargs).execute()
    

    def search(self, query, start_date, end_date, order_by="relevance", results_to_get=50):
        """Search for videos based on a query term and date range.
        
        API Cost: 100 credits for 50 search results
        Documentation: https://developers.google.com/youtube/v3/docs/search/list
        
        Parameters:
            query (str): The search query term.
            start_date (str): The start date for the search query.
            end_date (str): The end date for the search query.
            max_results (int): The maximum number of results to return.
        
        Returns:
            A pandas DataFrame containing the search results.
        """
        
        assert isinstance(query, str), "query must be a string"
        assert datetime.date.fromisoformat(start_date), "start_date must be of format YYYY-MM-DD"
        assert datetime.date.fromisoformat(end_date), "end_date must be of format YYYY-MM-DD"
        assert order_by in ["date", "rating", "relevance", "title", "videoCount", "viewCount"], \
            "order_by must be one of: date, rating, relevance, title, videoCount, viewCount"
        assert 0 < results_to_get <= 50, "results_to_get must be between 1 and 50 (inclusive)"
        
        nextPageToken = None
        first_page = True    
        
        search_df = pd.DataFrame()
        while (nextPageToken is not None) or (first_page is True):
            first_page = False
            to_get = 0
            if results_to_get >= 50:
                to_get = 50
                results_to_get -= 50
            elif 0 < results_to_get < 50:
                to_get = results_to_get
                results_to_get = 0
            else: # results_to_get <= 0
                break
            
            try:
                response = self._search(
                    part="snippet",
                    q=query,
                    pageToken=None,
                    type="video",
                    order=order_by, # date, rating, relevance (default), title, videoCount, viewCount
                    publishedAfter=start_date + "T00:00:00Z",
                    publishedBefore=end_date + "T00:00:00Z",
                    maxResults=to_get,
                )
                
            except Exception as e:
                print(e)
                break
                
            nextPageToken = response.get("nextPageToken") if "nextPageToken" in response else None

            items = response.get("items")
            
            df = pd.DataFrame()
            df['video_id'] = [item["id"]["videoId"] for item in items]
            df['video_title'] = [item["snippet"]["title"] for item in items]
            df['channel_id'] = [item["snippet"]["channelId"] for item in items]
            df['channel_title'] = [item["snippet"]["channelTitle"] for item in items]
            df['published_time'] = [item["snippet"]["publishedAt"] for item in items]
        
            search_df = pd.concat([search_df, df], ignore_index=True)
        
        return search_df


    #
    # Video Functions
    #

    def _videos(self, **kwargs):
        return self.youtube.videos().list(**kwargs).execute()
        
    
    # TODO: Implement function to get video details
    def video_details(self, video_id):
        """Get the details of a video.
        
        API Cost: 1 Credit Per Request/Video
        Documentation: https://developers.google.com/youtube/v3/docs/videos/list
        
        Parameters:
            video_id (str): The ID of the video to get details for.
            
        Returns:
            A pandas DataFrame containing the video details.
        """
        
        return self._videos(
            part="snippet,contentDetails,statistics",
            video_id=video_id,
        )
    
    
    def _download_audio_from_id(self, video_id, save_path, filename):
        video_object = PyTube("https://www.youtube.com/watch?v=" + video_id)
            
        streams = video_object.streams.filter(only_audio=True, file_extension="mp4")
        
        if streams.get_by_itag(140).exists(): # itag 140 -> 128kbps
            stream = streams.get_by_itag(140)
        elif streams.get_by_itag(139).exists(): # itag 139 -> 48kbps
            stream = streams.get_by_itag(139)
        else:
            stream = None
            raise Exception("No audio stream found")
        
        return stream.download(
            output_path=save_path,
            filename=filename,
        )
        
    
    def download_audio(self, video_ids, save_path="/content/audio"):
        """Download the audio of a list of videos.
        
        API Cost: 0 Credits
        Documentation: https://python-pytube.readthedocs.io/en/latest/user/quickstart.html
        
        Parameters:
            video_ids (list): The list of video IDs to download.
            save_path (str): The path to save the audio file to.
            
        Returns:
            A list of the filenames of the downloaded audio files.
        """
        
        assert video_ids is not None, "video_ids must be provided"
        assert isinstance(video_ids, list), "video_ids must be a list"
        assert isinstance(video_ids[0], str), "video_ids must be a list of strings"
        assert save_path is not None, "save_path must be provided"
        assert isinstance(save_path, str), "save_path must be a string"
        
        filenames = []
        for video_id in video_ids:
            filename = self._download_audio_from_id(
                video_id=video_id,
                save_path=save_path,
                filename=video_id + ".mp4"
            )
            filenames.append(filename)
            
        return filenames
    
    
    def _initialize_whisper_model(self, model="base"):
        self.whisper_model = OpenAIWhisper(model)
    
    
    def transcribe_audio(self, filenames, path="content/audio", model=None):
        """Transcribe a list of audio files.
        
        Parameters:
            filenames (list): The list of filenames to transcribe.
            path (str): The path to the audio files.
            model (str): The model to use for transcription.
        
        Returns:
            A list of strings containing the transcriptions.
        """
        
        assert filenames is not None, "filenames must be provided"
        assert isinstance(filenames, list), "filenames must be a list"
        assert isinstance(filenames[0], str), "filenames must be a list of strings"
        assert isinstance(path, str), "path must be a string"
        assert model in ["tiny", "base", "small", "medium", "large", None], \
            "model must be one of: tiny (39M), base (74M), small (244M), medium (769M), large (1550M)"
        
        if model is not None:
            self._initialize_whisper_model(model=model)
        elif self.whisper_model is None:
            self._initialize_whisper_model(model="base")
            
        transcripts = []
        for filename in filenames:
            assert os.path.exists(os.path.join(path, filename)), "File does not exist: " + filename + " in " + path
            output = self.whisper_model.transcribe(os.path.join(path, filename))
            transcripts.append(output["text"])
        
        return transcripts
        

    #
    # Comment Functions
    #
    
    def _comment_threads(self, **kwargs):
        return self.youtube.commentThreads().list(**kwargs).execute()


    def _comment_threads_to_df(self, comments_list):
        flattened_comments = []
        for comment in comments_list:
            flattened_comments += [comment["snippet"]["topLevelComment"]]
            if "replies" in comment:
                flattened_comments += comment["replies"]["comments"]
        
        flattened_df = pd.json_normalize(flattened_comments, sep=".")

        flattened_df = flattened_df.rename(
            columns={
                "snippet.videoId" : "video_id",
                "snippet.textOriginal" : "text_original",
                "snippet.authorDisplayName" : "author_display_name",
                "snippet.authorChannelId.value" : "author_channel_id",
                "snippet.likeCount" : "like_count",
                "snippet.publishedAt" : "published_at",
                "snippet.updatedAt" : "updated_at",
                "snippet.parentId" : "parent_id",
            }
        )

        flattened_df = flattened_df[
            ["id",
            "video_id",
            "text_original",
            "author_display_name",
            "author_channel_id",
            "like_count",
            "published_at",
            "updated_at",
            "parent_id"]
        ]
        
        return flattened_df


    def comments(self, video_id, results_to_get="all"):
        """Gets the comments of a video.
        
        API Cost: 1 credit for 100 comment threads (top-level comments plus any replies).
        Documentation: https://developers.google.com/youtube/v3/docs/commentThreads/list
        
        Parameters:
            video_id (str): The ID of the video to get the comments of.
            results_to_get (str): The number of results to get. Must be one of "all", "top_100", or "top_500".
                        
        Returns:
            A pandas DataFrame containing the comments of the video.
        """
        
        assert video_id is not None, "video_id must be provided"
        assert isinstance(video_id, str), "video_id must be a string"
        assert results_to_get in ["all", "top_100", "top_500"], \
            "results_to_get must be one of 'all', 'top_100', or 'top_500'"

        next_page_token = None
        first_page = True
        
        comments_list = []
        while (next_page_token is not None) or (first_page is True):
            first_page = False
            
            try: 
                threads = self._comment_threads(
                    part="snippet, replies",
                    videoId=video_id,
                    pageToken=next_page_token,
                    order="time", # time, relevance (sorting by relevance uses an algorithm which can filter out some comments)
                    maxResults=100,
                )

            except Exception as e:
                print(e)
                break
            
            next_page_token = threads.get("nextPageToken") if "nextPageToken" in threads else None
            comments_list += threads['items']
            
        comments_df = self._comment_threads_to_df(comments_list)
        
        return comments_df


if __name__ == "__main__":
    print("Youtube API Helper")