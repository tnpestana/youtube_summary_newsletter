# YouTube Summary Newsletter 📧

An automated newsletter system that transforms YouTube video transcripts into concise, email-friendly articles using AI. Perfect for staying updated with your favorite channels without watching every video.

## 🚀 Features

- **Automated Daily Newsletters**: Runs on GitHub Actions at 6:00 AM UTC daily
- **AI-Powered Summarization**: Uses CrewAI + Groq for intelligent content transformation
- **Multiple Channel Support**: Monitor several YouTube channels simultaneously
- **Email-Friendly Format**: Short, scannable paragraphs optimized for email reading
- **Robust Error Handling**: Retry logic and graceful failure handling
- **No Promotional Content**: Automatically removes sponsor mentions and channel plugs

## 📋 How It Works

1. **Fetch Videos**: Retrieves recent videos from configured YouTube channels
2. **Extract Transcripts**: Downloads video transcripts using YouTube's API
3. **AI Processing**: CrewAI agents transform transcripts into newsletter-style articles
4. **Email Delivery**: Sends formatted articles via email to your inbox

## 🛠️ Setup Instructions

### Prerequisites

- Python 3.11+
- YouTube Data API v3 key
- Groq API key (for AI processing)
- Email account with SMTP access

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd youtube_summary_newsletter
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.template .env
   # Edit .env with your API keys and email credentials
   ```

4. **Update configuration**
   Edit `config/config.yaml` to add your YouTube channel IDs and preferences.

5. **Run locally**
   ```bash
   python src/main.py
   ```

### Configuration

#### YouTube Channels (`config/config.yaml`)
```yaml
youtube_channel_ids:
  - UC-uhvujip5deVcEtLxnW8qg # TLDR News Global
  - UC-eegKVWEgBCa4OzjnK_PtA # TLDR News EU
  - UCz_3xlMTVUYYTQqCfh9lD7w # TLDR Daily
```

#### LLM Settings
```yaml
llm:
  provider: "groq"
  model: "llama-3.1-8b-instant"
```

#### Video Retrieval Settings
```yaml
video_retrieval:
  published_after_days: 1 # Look for videos from the last N days
```

## ⚙️ GitHub Actions Automation

### Setting Up Automated Daily Newsletters

1. **Fork/Clone this repository to your GitHub account**

2. **Configure GitHub Secrets**
   
   Go to your repository → Settings → Secrets and variables → Actions
   
   Add these secrets:
   
   | Secret Name | Description | Example |
   |-------------|-------------|---------|
   | `YOUTUBE_API_KEY` | YouTube Data API v3 key | `AIzaSyA...` |
   | `GROQ_API_KEY` | Groq API key | `gsk_...` |
   | `SENDER_EMAIL` | Sender email address | `your-email@gmail.com` |
   | `SENDER_PASSWORD` | Email password/app password | `your-app-password` |
   | `RECIPIENT_EMAIL` | Newsletter recipient email | `recipient@example.com` |

3. **Email Setup for Gmail**
   - Enable 2-factor authentication
   - Generate an App Password:
     - Google Account → Security → 2-Step Verification → App passwords
     - Select "Mail" and generate password
     - Use this app password as `SENDER_PASSWORD`

4. **Test the Setup**
   - Go to Actions tab → "Daily YouTube Summary Newsletter"
   - Click "Run workflow" to test manually
   - Check your email for the newsletter

### Customizing the Schedule

The default schedule runs at 6:00 AM UTC. To change this, edit `.github/workflows/daily-newsletter.yml`:

```yaml
schedule:
  # Examples for different timezones:
  - cron: '0 6 * * *'   # 6:00 AM UTC
  - cron: '0 11 * * *'  # 6:00 AM EST (UTC-5)
  - cron: '0 14 * * *'  # 6:00 AM PST (UTC-8)
  - cron: '0 5 * * *'   # 6:00 AM CET (UTC+1)
```

## 🔧 API Keys Setup

### YouTube Data API v3
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable YouTube Data API v3
4. Create credentials (API Key)
5. Restrict the key to YouTube Data API v3

### Groq API
1. Sign up at [Groq Console](https://console.groq.com/)
2. Generate an API key
3. Note: Groq offers free tier with rate limits

## 📁 Project Structure

```
src/
├── main.py                          # Main application entry point
├── agents/
│   └── transcript_to_article_agent.py  # CrewAI agent for content transformation
└── tools/                           # Utility modules
    ├── youtube_utils.py             # YouTube API interactions
    ├── groq_tools.py                # Groq API integration
    ├── email_utils.py               # Email delivery
    └── text_utils.py                # Text processing utilities

.github/workflows/
└── daily-newsletter.yml            # GitHub Actions workflow

config/
└── config.yaml                     # Application configuration
```

## 🎛️ Customization

### Adding New Channels
1. Find the YouTube channel ID (from channel URL or browser inspector)
2. Add to `config/config.yaml` under `youtube_channel_ids`

### Changing AI Model
Edit `config/config.yaml`:
```yaml
llm:
  provider: "groq"
  model: "llama-3.1-70b-versatile"  # or other Groq models
```

### Adjusting Content Length
The AI prompt targets 200-400 words per article. To modify, edit the prompt in `src/agents/transcript_to_article_agent.py`.

## 🐛 Troubleshooting

### Common Issues

**No emails received:**
- Check spam folder
- Verify email credentials and app password
- Test SMTP settings locally

**API rate limits:**
- Groq has free tier limits
- YouTube API has daily quotas
- The system includes retry logic with exponential backoff

**No videos found:**
- Check if channels published videos in the configured time window
- Verify channel IDs are correct
- Increase `published_after_days` in config

**Transcript errors:**
- Some videos may not have transcripts available
- The system skips videos without transcripts automatically

### Debug Locally

```bash
# Test with environment variables
export YOUTUBE_API_KEY="your_key"
export GROQ_API_KEY="your_key"
# ... other vars
python src/main.py
```

### GitHub Actions Debugging

- Check the Actions tab for detailed logs
- Download artifacts to see generated articles
- Use "Run workflow" to test manually

## 📝 License

This project is open source. Feel free to fork, modify, and use for your own newsletter needs!

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional AI providers (OpenAI, Anthropic, etc.)
- More email providers
- Web interface for configuration
- Better error handling and monitoring
- Support for more content sources