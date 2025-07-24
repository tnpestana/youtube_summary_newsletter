import os
import requests
from scraperapi_sdk import ScraperAPIClient

from datetime import datetime, timedelta
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

def get_recent_video_ids(channel_id, api_key, published_after=None) -> list[str]:
    if published_after is None:
        published_after = (datetime.now() - timedelta(days=1)).isoformat("T") + "Z"

    base_url = "https://www.googleapis.com/youtube/v3/search"
    video_ids = []
    next_page_token = None

    # Check if ScraperAPI key is available for GitHub Actions
    scraperapi_key = os.getenv("SCRAPERAPI_KEY")
    
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

        if scraperapi_key:
            # Use ScraperAPI to bypass IP blocks
            try:
                client = ScraperAPIClient(scraperapi_key)
                response = client.get(base_url, params=params)
                data = response.json()
            except Exception as e:
                print(f"⚠️ ScraperAPI failed: {e}")
                print("🔄 Falling back to direct requests...")
                # Fallback to direct requests if ScraperAPI fails
                response = requests.get(base_url, params=params)
                response.raise_for_status()
                data = response.json()
        else:
            # Fallback to direct requests for local development
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
        scraperapi_key = os.getenv("SCRAPERAPI_KEY")
        
        if scraperapi_key:
            # Use ScraperAPI as proxy for transcript fetching
            proxies = {
                'http': f'http://scraperapi:{scraperapi_key}@proxy-server.scraperapi.com:8001',
                'https': f'http://scraperapi:{scraperapi_key}@proxy-server.scraperapi.com:8001'
            }
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang], proxies=proxies)
        else:
            # Fallback to direct requests for local development
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
            
        return " ".join([t["text"] for t in transcript])
    except TranscriptsDisabled:
        return "[Transcript disabled]"
    except NoTranscriptFound:
        return "[Transcript not available]"
    except Exception as e:
        return f"[Error fetching transcript: {str(e)}]"