import os
import requests
from datetime import datetime, timedelta
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from pytube import YouTube

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
    # Try youtube-transcript-api first (primary method)
    try:
        print(f"📥 Trying youtube-transcript-api for video: {video_id}")
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
        result = " ".join([t["text"] for t in transcript])
        print(f"✅ youtube-transcript-api successful ({len(result)} chars)")
        return result
            
    except TranscriptsDisabled:
        print("⚠️ youtube-transcript-api: Transcript disabled")
        return "[Transcript disabled]"
    except NoTranscriptFound:
        print("⚠️ youtube-transcript-api: Transcript not found, trying pytube fallback...")
    except Exception as e:
        print(f"⚠️ youtube-transcript-api failed: {e}, trying pytube fallback...")
    
    # Fallback to pytube if youtube-transcript-api fails
    try:
        print(f"🔄 Trying pytube fallback for video: {video_id}")
        url = f"https://www.youtube.com/watch?v={video_id}"
        yt = YouTube(url)
        
        # Try to get captions in the specified language
        captions = yt.captions.get_by_language_code(lang)
        if not captions:
            # If specified language not found, try English as fallback
            captions = yt.captions.get_by_language_code('en')
        if not captions:
            # If English not found, get the first available caption
            if yt.captions:
                captions = list(yt.captions.values())[0]
            else:
                print("❌ pytube: No captions available")
                return "[No captions available]"
        
        # Generate and return the transcript
        transcript_text = captions.generate_srt_captions()
        
        # Parse SRT format to extract just the text
        lines = transcript_text.split('\n')
        text_lines = []
        for i, line in enumerate(lines):
            # Skip sequence numbers and timestamps, keep only text
            if line.strip() and not line.strip().isdigit() and '-->' not in line:
                text_lines.append(line.strip())
        
        result = " ".join(text_lines)
        print(f"✅ pytube fallback successful ({len(result)} chars)")
        return result
            
    except Exception as e:
        print(f"❌ Both methods failed. Final error: {e}")
        return f"[Error fetching transcript: {str(e)}]"