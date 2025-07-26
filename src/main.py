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
    print(f"\n🚀 STEP 1: Fetching video IDs from {len(channel_ids)} channels")
    print(f"📅 Looking for videos published in the last {days_back} day(s)")
    
    if not channel_ids:
        print("❌ No YouTube channel IDs provided in configuration")
        raise ValueError("No YouTube channel IDs provided.")

    all_video_ids = []
    published_after = get_published_after_date(days_back)
    
    for i, channel_id in enumerate(channel_ids, 1):
        print(f"\n📺 Processing channel {i}/{len(channel_ids)}: {channel_id}")

        video_ids = get_recent_video_ids(channel_id, YOUTUBE_API_KEY, published_after)
        all_video_ids.extend(video_ids)
        print(f"📊 Channel {channel_id} contributed {len(video_ids)} videos")
    
    print(f"\n✅ STEP 1 COMPLETE: Found {len(all_video_ids)} total videos across all channels")
    if len(all_video_ids) == 0:
        print("⚠️ WARNING: No videos found - this might indicate API issues or no recent uploads")
    
    return all_video_ids

def summarize_videos(video_ids: list[str], llm_models: list[str]) -> list[str]:
    print(f"\n🚀 STEP 2 & 3: Processing {len(video_ids)} videos (transcript + AI summarization)")
    
    articles = []
    transcript_failures = []
    ai_failures = []
    
    for i, video_id in enumerate(video_ids, 1):
        print(f"\n📹 Processing video {i}/{len(video_ids)}: {video_id}")
        
        # STEP 2: Transcript fetching
        try:
            print("🌐 STEP 2a: Fetching transcript...")
            transcript = get_transcript(video_id)
            
            if transcript.startswith("["):
                print(f"⚠️ Transcript fetch failed: {transcript}")
                transcript_failures.append((video_id, transcript))
                print(f"❌ Skipping video {video_id} due to transcript failure")
                continue
            
            print(f"✅ STEP 2a SUCCESS: Fetched transcript ({len(transcript)} chars)")
        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            print(f"❌ STEP 2a FAILED: {error_msg}")
            transcript_failures.append((video_id, error_msg))
            continue

        # STEP 3: AI processing  
        try:
            print("🧠 STEP 3: Summarizing transcript with CrewAI agent...")
            article = run_summary(transcript, llm_models)
            articles.append(article)
            print(f"✅ STEP 3 SUCCESS: Generated article for {video_id}")
            
            # Add delay between video processing to avoid rate limits
            if i < len(video_ids):  # Don't delay after last video
                rate_limited_processing_delay(i-1, len(video_ids), 10.0, "Waiting 10 seconds before next video...")
            
        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            print(f"❌ STEP 3 FAILED: {error_msg}")
            ai_failures.append((video_id, error_msg))
            print(f"⏩ Continuing with next video...")
            continue
    
    # Summary of results
    print(f"\n📊 STEP 2 & 3 SUMMARY:")
    print(f"✅ Successfully processed: {len(articles)}/{len(video_ids)} videos")
    print(f"❌ Transcript failures: {len(transcript_failures)}/{len(video_ids)} videos")
    print(f"❌ AI processing failures: {len(ai_failures)}/{len(video_ids)} videos")
    
    if transcript_failures:
        print(f"\n🔍 TRANSCRIPT FAILURE DETAILS:")
        for video_id, error in transcript_failures:
            print(f"  • {video_id}: {error}")
            
    if ai_failures:
        print(f"\n🔍 AI PROCESSING FAILURE DETAILS:")
        for video_id, error in ai_failures:
            print(f"  • {video_id}: {error}")

    return articles

def deliver_articles(articles: list[str]):
    print(f"\n🚀 STEP 4: Email delivery")
    print(f"📊 Articles to deliver: {len(articles)}")
    
    # Check email configuration
    missing_config = []
    if not RECIPIENT_EMAIL: missing_config.append("RECIPIENT_EMAIL")
    if not SENDER_EMAIL: missing_config.append("SENDER_EMAIL")
    if not SENDER_PASSWORD: missing_config.append("SENDER_PASSWORD")
    
    if missing_config:
        print(f"❌ STEP 4 FAILED: Missing email configuration: {', '.join(missing_config)}")
        return
    
    if not articles:
        # Send a notification email about the failure
        failure_message = f"""# YouTube Newsletter - Processing Failed

Unfortunately, no articles could be processed today due to processing issues.

**Issue Details:**
- YouTube transcript fetching encountered errors
- This could be due to IP blocking, rate limiting, or API changes
- The system attempted fallback methods but they also failed

**Next Steps:**
- The system will retry automatically on the next scheduled run
- Consider checking the GitHub Actions logs for detailed error information
- YouTube's anti-bot measures are becoming more aggressive

**Date:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
        print("⚠️ No articles to send - sending failure notification email")
        try:
            send_email(failure_message, RECIPIENT_EMAIL, SENDER_EMAIL, SENDER_PASSWORD)
            print("✅ STEP 4 SUCCESS: Failure notification email sent successfully")
        except Exception as e:
            print(f"❌ STEP 4 FAILED: Could not send notification email - {type(e).__name__}: {e}")
        return
    
    # Generate final content
    markdown = concatenate_text(articles)
    print(f"📝 Generated newsletter content: {len(markdown)} characters")
    
    # Send newsletter
    try:
        print(f"📧 Sending newsletter to {RECIPIENT_EMAIL}...")
        send_email(markdown, RECIPIENT_EMAIL, SENDER_EMAIL, SENDER_PASSWORD)
        print(f"✅ STEP 4 SUCCESS: Newsletter delivered successfully")
    except Exception as e:
        print(f"❌ STEP 4 FAILED: Email delivery error - {type(e).__name__}: {e}")
        raise

# MARK: Entry point

if __name__ == "__main__":
    print("🚀 Starting YouTube Summary Newsletter Pipeline")
    print("=" * 60)
    
    # Validate environment
    if not YOUTUBE_API_KEY:
        print("❌ SETUP FAILED: Missing YOUTUBE_API_KEY environment variable")
        raise EnvironmentError("Please set the YOUTUBE_API_KEY environment variable.")
    
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        print("❌ SETUP FAILED: Missing GROQ_API_KEY environment variable") 
        raise EnvironmentError("Please set the GROQ_API_KEY environment variable.")
    
    # Load configuration
    channel_ids = APP_CONFIG.get("youtube_channel_ids", [])
    days_back = APP_CONFIG.get("video_retrieval", {}).get("published_after_days", 1)
    llm_models = APP_CONFIG.get("llm", {}).get("models", ["llama-3.1-8b-instant"])
    
    print(f"✅ SETUP COMPLETE: Configured for {len(channel_ids)} channels, {days_back} days back")
    
    try:
        with managed_groq():
            # Execute pipeline
            video_ids = get_video_ids(channel_ids, days_back)
            articles = summarize_videos(video_ids, llm_models)
            deliver_articles(articles)
        
        print("\n" + "=" * 60)
        print("✅ PIPELINE COMPLETE: YouTube Newsletter successfully processed")
        
    except Exception as e:
        print(f"\n❌ PIPELINE FAILED: {type(e).__name__}: {e}")
        raise
    