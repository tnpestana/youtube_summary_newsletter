import datetime
import os
import yaml
from dotenv import load_dotenv
from tools.youtube.fetch_video_ids import get_recent_video_ids
from tools.youtube.fetch_transcripts import get_transcript
from tools.concatenate_articles import concatenate_text
from tools.save_articles import save_to_file
from tools.send_email import send_email
from agents.transcript_to_article_agent import run_summary

# -- ENV --------------------------------------------------
load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECEPIENT_EMAIL = os.getenv("RECEPIENT_EMAIL")

# -- MAIN PIPELINE ----------------------------------------------
def load_config(filepath="config/config.yaml"):
    with open(filepath, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config

def get_published_after_date(days: int) -> str:
    now = datetime.datetime.utcnow()
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

# -- ENTRY POINT ------------------------------------------------
if __name__ == "__main__":
    if not YOUTUBE_API_KEY:
        raise EnvironmentError("Please set the YOUTUBE_API_KEY environment variable.")

    config = load_config()

    channel_ids = config.get("youtube_channel_ids", [])
    days_back = config.get("video_retrieval", {}).get("published_after_days", 1)
    published_after = get_published_after_date(days_back)

    results = process_channels(channel_ids, after=published_after)
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