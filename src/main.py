import datetime
import os
import yaml

from agents.transcript_to_article_agent import run_summary
from dotenv import load_dotenv
from tools.email_utils import send_email
from tools.groq_tools import managed_groq
from tools.rate_limiting import rate_limited_processing_delay
from tools.text_utils import concatenate_text
from tools.youtube_utils import get_recent_video_ids, get_transcript
from pathlib import Path

# MARK: Loading

current_file = Path(__file__).resolve()
src_dir = current_file.parent
project_root = src_dir.parent
env_path = project_root / ".env"

if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

yaml_path = project_root / "config" / "config.yaml"
with open(yaml_path, "r") as f:
    APP_CONFIG = yaml.safe_load(f)

# MARK: Main pipeline

def get_published_after_date(days: int, now: datetime.datetime | None = None) -> str:
    now = now or datetime.datetime.now()
    return (now - datetime.timedelta(days=days)).isoformat("T") + "Z"

def get_video_ids(channel_ids: list[str], days_back: int) -> list[str]:
    if not channel_ids:
        raise ValueError("No YouTube channel IDs provided.")

    all_video_ids = []
    published_after = get_published_after_date(days_back)
    for channel_id in channel_ids:
        print(f"⏳ Fetching videos for channel: {channel_id}")

        video_ids = get_recent_video_ids(channel_id, YOUTUBE_API_KEY, published_after)
        all_video_ids.extend(video_ids)
    
    return all_video_ids

def summarize_videos(video_ids: list[str], llm_models: list[str]) -> list[str]:
    articles = []
    for i, video_id in enumerate(video_ids):
        print(f"📹 Processing video: {video_id}")
        try:
            transcript = get_transcript(video_id)

            if transcript.startswith("["):
                print(f"⚠️ Skipping video due to transcript issue: {transcript}")
                continue

            print("🧠 Summarizing transcript with CrewAI agent...")
            article = run_summary(transcript, llm_models)
            articles.append(article)
            print(f"✅ Successfully processed video: {video_id}")
            
            # Add delay between video processing to avoid rate limits
            rate_limited_processing_delay(i, len(video_ids), 10.0, "Waiting 10 seconds before next video...")
            
        except Exception as e:
            print(f"❌ Failed to process video {video_id}: {type(e).__name__}: {e}")
            print(f"⏩ Continuing with next video...")
            continue

    return articles

def deliver_articles(articles: list[str]):
    print(f"📊 Total articles to deliver: {len(articles)}")
    if not articles:
        print("⚠️ No articles to send - email will be empty")
        return
    
    markdown = concatenate_text(articles)
    print(f"📝 Generated markdown content length: {len(markdown)} characters")
    send_email(markdown, RECIPIENT_EMAIL, SENDER_EMAIL, SENDER_PASSWORD)

# MARK: Entry point

if __name__ == "__main__":
    if not YOUTUBE_API_KEY:
        raise EnvironmentError("Please set the YOUTUBE_API_KEY environment variable.")
    
    # Validate Groq API key
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise EnvironmentError("Please set the GROQ_API_KEY environment variable.")
    
    channel_ids = APP_CONFIG.get("youtube_channel_ids", [])
    days_back = APP_CONFIG.get("video_retrieval", {}).get("published_after_days", 1)
    llm_models = APP_CONFIG.get("llm", {}).get("models", ["llama-3.1-8b-instant"])
    
    with managed_groq():
        video_ids = get_video_ids(channel_ids, days_back)
        print(f"🎬 Found {len(video_ids)} videos to process")
        articles = summarize_videos(video_ids, llm_models)
        print(f"📝 Successfully processed {len(articles)} articles")
        deliver_articles(articles)
        
    print("✅ Done.")
    