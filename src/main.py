import datetime
import os
import yaml

from agents.transcript_to_article_agent import run_summary
from dotenv import load_dotenv
from tools.email_utils import send_email
from tools.file_utils import save_to_file
from tools.text_utils import concatenate_text
from tools.youtube_utils import get_recent_video_ids, get_transcript
from pathlib import Path

# MARK: Loading

current_file = Path(__file__).resolve()
src_dir = current_file.parent
project_root = src_dir.parent

env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECEPIENT_EMAIL = os.getenv("RECEPIENT_EMAIL")

yaml_path = project_root / "config" / "config.yaml"
with open(yaml_path, "r") as f:
    APP_CONFIG = yaml.safe_load(f)

# MARK: Main pipeline

def get_published_after_date(days: int) -> str:
    now = datetime.datetime.now()
    published_after = (now - datetime.timedelta(days)).isoformat("T") + "Z"
    return published_after

def process_channels(channel_ids):
    all_articles = []

    for channel_id in channel_ids:
        print(f"\n⏳ Fetching videos for channel: {channel_id}")
        video_ids = get_recent_video_ids(channel_id, YOUTUBE_API_KEY, published_after)

        for video_id in video_ids:
            print(f"📹 Processing video: {video_id}")
            transcript = get_transcript(video_id)

            if transcript.startswith("["):
                print(f"⚠️ Skipping video due to transcript issue: {transcript}")
                continue

            print("🧠 Summarizing transcript with CrewAI agent...")
            article = run_summary(transcript)

            all_articles.append({
                "channel_id": channel_id,
                "video_id": video_id,
                "article": article
            })

    return all_articles

# MARK: Entry point

if __name__ == "__main__":
    if not YOUTUBE_API_KEY:
        raise EnvironmentError("Please set the YOUTUBE_API_KEY environment variable.")

    channel_ids = APP_CONFIG.get("youtube_channel_ids", [])
    days_back = APP_CONFIG.get("video_retrieval", {}).get("published_after_days", 1)
    published_after = get_published_after_date(days_back)

    results = process_channels(channel_ids)
    articles = [item["article"] for item in results]
    markdown = concatenate_text(articles)
    
    save_to_file(markdown)
    send_email(
        markdown_text=markdown, 
        recipient_email=RECEPIENT_EMAIL,
        sender_email=SENDER_EMAIL,
        sender_password=SENDER_PASSWORD
    )

    print("\n✅ Done. Summarized Articles:\n")
    for result in results:
        print(f"--- Channel: {result['channel_id']} | Video: {result['video_id']} ---")
        print(result['article'])
        print("\n" + "="*80 + "\n")