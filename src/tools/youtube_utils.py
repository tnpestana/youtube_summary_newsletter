import requests
import yt_dlp
import tempfile
import os

from datetime import datetime, timedelta

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
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Configure yt-dlp options
        ydl_opts = {
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': [lang],
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
            # Add user agent to avoid bot detection
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            # Try to extract from embedded player
            'extractor_args': {
                'youtube': {
                    'player_client': ['web'],
                }
            },
            # Additional options to bypass restrictions
            'cookiesfrombrowser': None,  # Don't use browser cookies in CI
            'no_check_certificate': True,
        }
        
        # Use temporary directory for subtitle files
        with tempfile.TemporaryDirectory() as temp_dir:
            ydl_opts['outtmpl'] = os.path.join(temp_dir, '%(title)s.%(ext)s')
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract video info to get subtitle files
                info = ydl.extract_info(video_url, download=False)
                
                # Download subtitles
                ydl.download([video_url])
                
                # Look for subtitle files in the temp directory
                subtitle_files = []
                for file in os.listdir(temp_dir):
                    if file.endswith(f'.{lang}.vtt') or file.endswith(f'.{lang}.srt'):
                        subtitle_files.append(os.path.join(temp_dir, file))
                
                if not subtitle_files:
                    return "[Transcript not available]"
                
                # Read the first available subtitle file
                subtitle_file = subtitle_files[0]
                with open(subtitle_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse VTT or SRT content to extract text
                transcript_text = parse_subtitle_content(content)
                return transcript_text
                
    except Exception as e:
        return f"[Error fetching transcript: {str(e)}]"

def parse_subtitle_content(content):
    """Parse VTT or SRT subtitle content to extract plain text"""
    lines = content.split('\n')
    transcript_lines = []
    
    for line in lines:
        line = line.strip()
        # Skip empty lines, timestamps, and VTT headers
        if (not line or 
            line.startswith('WEBVTT') or 
            '-->' in line or 
            line.isdigit() or
            line.startswith('NOTE') or
            line.startswith('STYLE') or
            line.startswith('::cue')):
            continue
        
        # Remove VTT formatting tags
        import re
        line = re.sub(r'<[^>]+>', '', line)
        
        if line:
            transcript_lines.append(line)
    
    return ' '.join(transcript_lines)