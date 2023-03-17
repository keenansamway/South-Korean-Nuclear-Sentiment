import pandas as pd
from pytube import YouTube as PyTube
from googleapiclient.discovery import build
from config import YOUTUBE_API_KEY


class YouTubeHelper:
    def __init__(self, api_key, api_service_name="youtube", api_version="v3"):
        
        assert api_key is not None, "api_key must be provided"
        
        self.youtube = build(
            serviceName=api_service_name,
            version=api_version,
            developerKey=self.api_key
        )
        
        
    #
    # Search Functions
    #
    
    def _search(self, **kwargs):
        return self.youtube.search().list(**kwargs).execute()
    

    def get_search_results(self, query, start_date, end_date, results_to_get=50):
        """
        Search for videos based on a query term.
        API Cost: 100 credits for 50 search results
        Documentation: https://developers.google.com/youtube/v3/docs/search/list
        
        Parameters:
            youtube (object): The YouTube API object.
            query (str): The search query term.
            start_date (str): The start date for the search query.
            end_date (str): The end date for the search query.
            max_results (int): The maximum number of results to return.
        
        Returns:
            A pandas DataFrame containing the search results.
        """
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
                    order="viewCount", # date, rating, relevance (default), title, videoCount, viewCount
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
            df['video_ids'] = [item["id"]["videoId"] for item in items]
            df['video_titles'] = [item["snippet"]["title"] for item in items]
            df['channel_ids'] = [item["snippet"]["channelId"] for item in items]
            df['channel_titles'] = [item["snippet"]["channelTitle"] for item in items]
            df['published_time'] = [item["snippet"]["publishedAt"] for item in items]
        
            search_df = pd.concat([search_df, df], ignore_index=True)
        
        return search_df

    #
    # Video Functions
    #

    def _videos(self, **kwargs):
        """
        Get the details of a video.
        API Cost: 1 Credit Per Request/Video
        Documentation: https://developers.google.com/youtube/v3/docs/videos/list
        
        Parameters:
            youtube (object): The YouTube API object.
            **kwargs: The keyword arguments to pass to the videos method.
            
        Returns:
            A list of videos matching the search query.
        """
        return self.youtube.videos().list(
            part="snippet,contentDetails,statistics",
            **kwargs,
        ).execute()
    
    
    def _download_audio_from_id(self, video_id, save_path=None, filename=None):
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
        
    
    def download_audio(self, video_ids, save_path=None):
        """
        Download the audio of a video or list of videos.
        API Cost: 0 Credits
        Documentation: https://python-pytube.readthedocs.io/en/latest/user/quickstart.html
        
        Parameters:
            video_ids (str or list): The video ID or list of video IDs to download.
            save_path (str): The path to save the audio file to.
            
        Returns:
            None
        """
        assert video_ids is not None, "video_ids must be provided"
        assert isinstance(video_ids, str) or isinstance(video_ids, list), "video_ids must be a string or list"
        
        if isinstance(video_ids, list):
            filenames = []
            for video_id in video_ids:
                filenames.append(self._download_audio_from_id(video_id, save_path, video_id+".mp4"))
            return filenames
        else:
            filename = self._download_audio_from_id(video_id, save_path, video_id+".mp4")
            return filename
    

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
                "snippet.videoId" : "videoId",
                "snippet.textOriginal" : "textOriginal",
                "snippet.authorDisplayName" : "authorDisplayName",
                "snippet.authorChannelId.value" : "authorChannelId",
                "snippet.likeCount" : "likeCount",
                "snippet.publishedAt" : "publishedAt",
                "snippet.updatedAt" : "updatedAt",
                "snippet.parentId" : "parentId",
            }
        )

        flattened_df = flattened_df[
            ["id",
            "videoId",
            "textOriginal",
            "authorDisplayName",
            "authorChannelId",
            "likeCount",
            "publishedAt",
            "updatedAt",
            "parentId"]
        ]
        
        return flattened_df


    def get_video_comments(self, youtube, videoId, top_level_only=False, max_results=100):
        """
        Gets the comments of a video.
        API Cost: 1 credit for 100 comment threads (top-level comments plus any replies).
        
        Parameters:
            youtube (object): The YouTube API object.
            videoId (str): The ID of the video to get the comments of.
            top_level_only (bool): Whether to get the replies of the comment threads or just the top-level comments.
            max_results (int): The maximum number of comments to return (1-100).
            
        Returns:
            A pandas DataFrame containing the comments of the video.
        """
        assert max_results <= 100, "max_results must be less than or equal to 100"
        
        next_page_token = None
        first_page = True
        
        comments_list = []
        while (next_page_token is not None) or (first_page is True):
            first_page = False

            part = "snippet"
            part += ",replies" if not top_level_only else ""
            
            try: 
                threads = self._comment_threads(
                    part=part,
                    videoId=videoId,
                    top_level_only=top_level_only,
                    pageToken=next_page_token,
                    order="time", # time, relevance (sorting by relevance uses an algorithm which can filter out some comments)
                    maxResults=max_results,
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
    
    API_SERVICE_NAME = "youtube"
    API_VERSION = "v3"
