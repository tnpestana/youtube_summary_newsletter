from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

def get_transcript(video_id, lang='en'):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
        return " ".join([t["text"] for t in transcript])
    except TranscriptsDisabled:
        return "[Transcript disabled]"
    except NoTranscriptFound:
        return "[Transcript not available]"
    except Exception as e:
        return f"[Error fetching transcript: {str(e)}]"