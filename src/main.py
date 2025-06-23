import datetime
import os
import yaml

from agents.transcript_to_article_agent import run_summary
from agents.translator_agent import run_translation
from dotenv import load_dotenv
from tools.email_utils import send_email
from tools.file_utils import save_to_file
from tools.ollama_tools import managed_ollama
from tools.text_utils import concatenate_text
from tools.youtube_utils import get_recent_video_ids, get_transcript
from pathlib import Path

# MARK: Loading

current_file = Path(__file__).resolve()
src_dir = current_file.parent
project_root = src_dir.parent
env_path = project_root / ".env"

if not os.path.exists(env_path):
    raise FileNotFoundError(f"Missing .env file at {env_path}. Copy from .env.template and fill in your values.")
else:
    load_dotenv(dotenv_path=env_path)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECEPIENT_EMAIL = os.getenv("RECEPIENT_EMAIL")

yaml_path = project_root / "config" / "config.yaml"
with open(yaml_path, "r") as f:
    APP_CONFIG = yaml.safe_load(f)

TRANSLATION_CFG = APP_CONFIG.get("translation", {})
TRANSLATE_LANG = TRANSLATION_CFG.get("language", "en-US")
SUMMARY_LANG = "en-US"

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

def summarize_videos(video_ids: list[str]) -> list[str]:
    articles = []
    for video_id in video_ids:
        print(f"📹 Processing video: {video_id}")
        transcript = get_transcript(video_id)

        if transcript.startswith("["):
            print(f"⚠️ Skipping video due to transcript issue: {transcript}")
            continue

        print("🧠 Summarizing transcript with CrewAI agent...")
        article = run_summary(transcript, SUMMARY_LANG)

        if TRANSLATE_LANG.lower() != SUMMARY_LANG.lower():
            print("🌐 Translating article...")
            article = run_translation(article, TRANSLATE_LANG)

        articles.append(article)

    return articles

def deliver_articles(articles: list[str]):
    markdown = concatenate_text(articles)
    save_to_file(markdown)
    send_email(markdown, RECEPIENT_EMAIL, SENDER_EMAIL, SENDER_PASSWORD)

# MARK: Entry point

if __name__ == "__main__":
    if not YOUTUBE_API_KEY:
        raise EnvironmentError("Please set the YOUTUBE_API_KEY environment variable.")
    
    channel_ids = APP_CONFIG.get("youtube_channel_ids", [])
    days_back = APP_CONFIG.get("video_retrieval", {}).get("published_after_days", 1)
    
    with managed_ollama():
        video_ids = get_video_ids(channel_ids, days_back)
        articles = summarize_videos(video_ids)
        deliver_articles(articles)
        
    print("✅ Done.")
    
