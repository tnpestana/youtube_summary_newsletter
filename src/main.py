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
    load_dotenv(dotenv_path=env_path, override=True)

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
    
    # List of free public proxies to try (these change frequently)
    proxy_options = [
        None,  # Try direct connection first
        {"http": "http://198.49.68.80:80", "https": "http://198.49.68.80:80"},
        {"http": "http://47.74.152.29:8888", "https": "http://47.74.152.29:8888"},
        {"http": "http://20.111.54.16:80", "https": "http://20.111.54.16:80"},
    ]
    
    for i, video_id in enumerate(video_ids):
        print(f"📹 Processing video: {video_id}")
        transcript = None
        
        # Try each proxy option until one works
        for proxy_idx, proxies in enumerate(proxy_options):
            try:
                if proxies:
                    print(f"🌐 Attempting with proxy {proxy_idx}...")
                else:
                    print("🌐 Attempting direct connection...")
                    
                transcript = get_transcript(video_id, proxies=proxies)
                
                if not transcript.startswith("["):
                    print(f"✅ Successfully fetched transcript using {'direct connection' if not proxies else f'proxy {proxy_idx}'}")
                    break  # Success!
                else:
                    print(f"⚠️ {'Direct connection' if not proxies else f'Proxy {proxy_idx}'} failed: {transcript}")
                    
            except Exception as e:
                print(f"⚠️ {'Direct connection' if not proxies else f'Proxy {proxy_idx}'} error: {e}")
                continue
        
        if not transcript or transcript.startswith("["):
            print(f"❌ All connection attempts failed for video {video_id}")
            continue

        try:
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
    
    if not all([RECIPIENT_EMAIL, SENDER_EMAIL, SENDER_PASSWORD]):
        print("❌ Missing email configuration - check RECIPIENT_EMAIL, SENDER_EMAIL, SENDER_PASSWORD")
        return
    
    if not articles:
        # Send a notification email about the failure
        failure_message = f"""# YouTube Newsletter - Processing Failed

Unfortunately, no articles could be processed today due to transcript fetching issues.

**Issue Details:**
- YouTube is blocking transcript access with bot detection
- All proxy attempts failed with connection errors
- This is a temporary issue that should resolve itself

**Next Steps:**
- The system will retry automatically on the next scheduled run
- YouTube's anti-bot measures are becoming more aggressive
- Consider implementing cookie-based authentication for more reliable access

**Date:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
        print("⚠️ No articles to send - sending failure notification email")
        try:
            send_email(failure_message, RECIPIENT_EMAIL, SENDER_EMAIL, SENDER_PASSWORD)
            print("📧 Failure notification email sent successfully")
        except Exception as e:
            print(f"❌ Failed to send notification email: {type(e).__name__}: {e}")
        return
    
    markdown = concatenate_text(articles)
    print(f"📝 Generated markdown content length: {len(markdown)} characters")
    
    try:
        send_email(markdown, RECIPIENT_EMAIL, SENDER_EMAIL, SENDER_PASSWORD)
    except Exception as e:
        print(f"❌ Email delivery failed: {type(e).__name__}: {e}")
        raise

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
    