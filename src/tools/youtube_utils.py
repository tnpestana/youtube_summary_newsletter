import requests

from datetime import datetime, timedelta
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from youtube_transcript_api.formatters import TextFormatter

def get_recent_video_ids(channel_id, api_key, published_after=None) -> list[str]:
    if published_after is None:
        published_after = (datetime.now() - timedelta(days=1)).isoformat("T") + "Z"

    base_url = "https://www.googleapis.com/youtube/v3/search"
    video_ids = []
    next_page_token = None

    while True:
        params = {
            "part": "id",
            "channelId": channel_id,
            "publishedAfter": published_after,
            "type": "video",
            "order": "date",
            "maxResults": 50,
            "pageToken": next_page_token,
            "key": api_key
        }

        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        for item in data.get("items", []):
            video_ids.append(item["id"]["videoId"])

        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break

    return video_ids

def get_transcript(video_id, lang='en', proxies=None):
    try:
        # Use proxies if provided to work around IP blocking
        if proxies:
            transcript = YouTubeTranscriptApi.get_transcript(
                video_id, 
                languages=[lang],
                proxies=proxies
            )
        else:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
            
        return " ".join([t["text"] for t in transcript])
    except TranscriptsDisabled:
        return "[Transcript disabled]"
    except NoTranscriptFound:
        return "[Transcript not available]"
    except Exception as e:
        return f"[Error fetching transcript: {str(e)}]"