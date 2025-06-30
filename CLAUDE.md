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
# Run the main pipeline
python src/main.py
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

## File Structure

```
src/
├── main.py                          # Main application entry point
├── agents/
│   └── transcript_to_article_agent.py  # CrewAI agent for transcript processing
└── tools/                           # Utility modules
    ├── youtube_utils.py             # YouTube API interactions
    ├── groq_tools.py                # Groq API integration
    ├── email_utils.py               # Email delivery
    ├── file_utils.py                # File operations
    └── text_utils.py                # Text processing utilities
```

## Important Implementation Details

- The application fetches videos published within the last N days (configurable)
- Transcripts are processed through a CrewAI agent with specific editorial guidelines
- The agent is instructed to remove promotional content and maintain factual accuracy
- Output is formatted as GitHub Flavored Markdown following CommonMark specifications
- All articles are concatenated and delivered as a single email newsletter