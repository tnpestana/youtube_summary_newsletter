import requests

from datetime import datetime, timedelta
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

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

def get_transcript(video_id, lang='en'):
    try:
        # Try the standard static method call first (newer versions)
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
        return " ".join([t["text"] for t in transcript_list])
    except AttributeError:
        # If static method doesn't exist, use the older API with fetch/list methods
        try:
            # Try the fetch method (older API)
            transcript_list = YouTubeTranscriptApi.fetch(video_id, lang)
            return " ".join([t["text"] for t in transcript_list])
        except Exception as fetch_error:
            try:
                # Try the list method as fallback
                transcript_data = YouTubeTranscriptApi.list(video_id)
                # Extract text from whatever format this returns
                if isinstance(transcript_data, list):
                    return " ".join([str(item.get("text", item)) for item in transcript_data])
                else:
                    return f"[Unexpected list format: {type(transcript_data)}]"
            except Exception as list_error:
                return f"[Error: Both fetch ({fetch_error}) and list ({list_error}) methods failed]"
    except TranscriptsDisabled:
        return "[Transcript disabled]"
    except NoTranscriptFound:
        return "[Transcript not available]"
    except Exception as e:
        return f"[Error fetching transcript: {str(e)}]"