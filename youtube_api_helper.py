import pandas as pd
from googleapiclient.discovery import build
from config import YOUTUBE_API_KEY

API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

youtube = build(
    serviceName=API_SERVICE_NAME,
    version=API_VERSION,
    developerKey=YOUTUBE_API_KEY
)

#
# Search Functions
#

def get_search_results(youtube, query, start_date, end_date, results_to_get=50):
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
            response = youtube.search().list(
                part="snippet",
                q=query,
                pageToken=None,
                type="video",
                order="viewCount", # date, rating, relevance (default), title, videoCount, viewCount
                publishedAfter=start_date + "T00:00:00Z",
                publishedBefore=end_date + "T00:00:00Z",
                maxResults=to_get,
            ).execute()
            
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

def _get_video_details(youtube, **kwargs):
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
    return youtube.videos().list(
        part="snippet,contentDetails,statistics",
        **kwargs,
    ).execute()


#
# Comment Functions
#

def _flatten_comments_to_df(comments_list):
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


def get_video_comments(youtube, videoId, top_level_only=False, max_results=100):
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
            threads = youtube.commentThreads().list(
                part=part,
                videoId=videoId,
                top_level_only=top_level_only,
                pageToken=next_page_token,
                order="time", # time, relevance (sorting by relevance uses an algorithm which can filter out some comments)
                maxResults=max_results,
            ).execute()

        except Exception as e:
            print(e)
            break
        
        next_page_token = threads.get("nextPageToken") if "nextPageToken" in threads else None
        comments_list += threads['items']
    
    comments_df = _flatten_comments_to_df(comments_list)
    
    return comments_df



if __name__ == "__main__":
    print("Youtube API Helper")