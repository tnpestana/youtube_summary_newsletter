# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a YouTube Summary Newsletter application that automatically fetches transcripts from YouTube channels, processes them using AI (CrewAI + Ollama), and delivers summaries via email. The application is designed to run as a daily newsletter system.

## Architecture

### Core Components

- **Main Pipeline** (`src/main.py`): Orchestrates the entire workflow from video fetching to email delivery
- **AI Agent** (`src/agents/transcript_to_article_agent.py`): Uses CrewAI to transform raw transcripts into polished articles
- **Utilities** (`src/tools/`): Modular tools for YouTube API, email, file operations, and Ollama management
- **Configuration** (`config/config.yaml`): Centralized configuration for channels, LLM settings, and output preferences

### Key Dependencies

- **CrewAI**: Multi-agent AI orchestration framework
- **Groq**: Cloud-based LLM inference API
- **YouTube Transcript API**: For fetching video transcripts
- **Python-dotenv**: Environment variable management

## Development Commands

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template and configure
cp .env.template .env
# Edit .env with your YouTube API key and email credentials
```

### Running the Application
```bash
# Run the main pipeline manually
python src/main.py

# Run via scheduler (checks if execution is needed)
python src/scheduler.py

# Run via shell script (includes logging)
./run_newsletter.sh
```

### Configuration

The application uses two configuration files:

1. **`.env`**: Contains sensitive credentials (YouTube API key, Groq API key, email credentials)
2. **`config/config.yaml`**: Contains application settings including:
   - YouTube channel IDs to monitor
   - Video retrieval settings (days back to search)
   - LLM provider and model configuration
   - Output folder and filename preferences

## Development Notes

### LLM Configuration

The application supports different LLM providers through the `llm` section in `config.yaml`. Currently configured for Groq with the llama3-70b-8192 model.

### Groq Integration

The application uses Groq's cloud API for LLM inference (`src/tools/groq_tools.py`) which eliminates the need for local model installation and management.

### Error Handling

- Missing `.env` file will raise a clear error with instructions
- Transcript fetching errors are logged and videos are skipped
- Email delivery failures should be handled gracefully

### Output Structure

Processed articles are saved to the `summarized_articles/` directory with timestamps. The filename format includes the LLM model used for tracking different model outputs.

## Scheduled Execution

### Setting Up Your Own Schedule

Follow these steps to set up automated daily execution on your Mac:

#### 1. Grant Permissions (macOS Security Requirement)

On macOS Ventura and later, you need to give Terminal "Full Disk Access" permissions:

1. Open **System Settings** > **Privacy & Security** > **Full Disk Access**
2. Click the **+** button and add your Terminal application
3. Restart Terminal after granting permissions

#### 2. Install the Cron Job

Choose your preferred time and install the cron job. The format is: `minute hour * * *`

**Examples:**
```bash
# Run at 8:00 PM daily (recommended - computer usually awake)
echo "0 20 * * * $(pwd)/run_newsletter.sh" | crontab -

# Run at 8:00 AM daily
echo "0 8 * * * $(pwd)/run_newsletter.sh" | crontab -

# Run at 2:00 PM daily
echo "0 14 * * * $(pwd)/run_newsletter.sh" | crontab -

# Run at 11:30 PM daily
echo "30 23 * * * $(pwd)/run_newsletter.sh" | crontab -
```

#### 3. Set Up Startup Execution (For Missed Runs)

Create a LaunchAgent that runs when your Mac starts up:

```bash
# Create the LaunchAgent directory if it doesn't exist
mkdir -p ~/Library/LaunchAgents

# Create the LaunchAgent file (replace USERNAME with your actual username)
cat > ~/Library/LaunchAgents/com.newsletter.scheduler.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.newsletter.scheduler</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$(pwd)/src/scheduler.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$(pwd)</string>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$(pwd)/logs/launcher.log</string>
    <key>StandardErrorPath</key>
    <string>$(pwd)/logs/launcher.log</string>
</dict>
</plist>
EOF

# Load the LaunchAgent
launchctl load ~/Library/LaunchAgents/com.newsletter.scheduler.plist
```

#### 4. Verify Setup

```bash
# Check your cron job is installed
crontab -l

# Check LaunchAgent is loaded
launchctl list | grep newsletter

# Test the scheduler manually
python3 src/scheduler.py
```

### How the Smart Scheduling Works

The system uses two mechanisms to ensure your newsletter runs daily:

1. **Cron Job**: Runs at your scheduled time (e.g., 8 PM) if your Mac is awake
2. **LaunchAgent**: Runs the scheduler when your Mac starts up

The scheduler (`src/scheduler.py`) intelligently:
- Tracks the last successful run in `logs/last_run.json`
- Only runs the newsletter if more than 23 hours have passed since the last execution
- Prevents duplicate runs if both the cron job and startup trigger fire

### Troubleshooting

**Cron job not running?**
- Ensure Terminal has "Full Disk Access" permissions
- Check the cron job exists: `crontab -l`
- Verify the script is executable: `ls -la run_newsletter.sh`

**Newsletter not running on startup?**
- Check LaunchAgent is loaded: `launchctl list | grep newsletter`
- View startup logs: `cat logs/launcher.log`

**Still having issues?**
- Test manually: `./run_newsletter.sh`
- Check main logs: `cat logs/newsletter_cron.log`

### Customizing the Schedule

You can modify the cron time format to run at different intervals:

```bash
# Every 6 hours at minute 0
0 */6 * * *

# Every weekday at 9 AM
0 9 * * 1-5

# Every Sunday at 10 AM
0 10 * * 0

# Twice daily: 8 AM and 8 PM
0 8,20 * * *
```

## File Structure

```
src/
├── main.py                          # Main application entry point
├── scheduler.py                     # Smart scheduler for missed executions
├── agents/
│   └── transcript_to_article_agent.py  # CrewAI agent for transcript processing
└── tools/                           # Utility modules
    ├── youtube_utils.py             # YouTube API interactions
    ├── groq_tools.py                # Groq API integration
    ├── email_utils.py               # Email delivery
    ├── file_utils.py                # File operations
    └── text_utils.py                # Text processing utilities

run_newsletter.sh                    # Shell script wrapper with logging
logs/                               # Log files and execution tracking
└── last_run.json                   # Tracks last successful execution
```

## Important Implementation Details

- The application fetches videos published within the last N days (configurable)
- Transcripts are processed through a CrewAI agent with specific editorial guidelines
- The agent is instructed to remove promotional content and maintain factual accuracy
- Output is formatted as GitHub Flavored Markdown following CommonMark specifications
- All articles are concatenated and delivered as a single email newsletter