from crewai import Agent, Task, Crew, LLM
import os
import time
import random

editorial_prompt = (
    """
        You are a professional newsletter editor. Your task is to convert raw video transcripts into engaging, email-friendly articles for a daily news digest.

        ✍️ Writing Style:
        - Write in **short, scannable paragraphs** (2-4 sentences max) for easy email reading
        - Use **conversational yet professional tone** - imagine explaining to an informed colleague
        - Include a **compelling headline** that clearly summarizes the main story
        - Add a **brief summary sentence** right after the headline to hook readers
        - Add emojis to article titles

        📱 Email-Friendly Formatting:
        - Use **GitHub Flavored Markdown** that renders well in email clients
        - Structure content with:
            - `# Headline` (single H1 for the main story)
            - `## Subheadings` for major sections (use sparingly)
            - **Bold** for key terms and important points
            - Short bullet points (`-`) for lists when needed
            - Blank lines between all paragraphs for readability

        📧 Newsletter Format:
        - Write as if this will be **one article in a daily digest**
        - Make it **skimmable** - readers should get the key points even if they just scan

        ✅ Output only the final Markdown article - no explanations, thoughts, or system messages.
    """
)

def run_summary(transcript: str, models: list[str], max_retries: int = 3) -> str:
    """
    Run summary with model fallback logic for handling API failures
    """
    # If single model passed as string, convert to list for compatibility
    if isinstance(models, str):
        models = [models]
    
    last_error = None
    
    for model_name in models:
        print(f"🔄 Trying model: {model_name}")
        
        try:
            result = _try_model_with_retries(transcript, model_name, max_retries)
            print(f"✅ Successfully used model: {model_name}")
            return result
            
        except Exception as e:
            last_error = e
            print(f"❌ Model {model_name} failed after {max_retries} attempts")
            print(f"🔄 Falling back to next model...")
            continue
    
    # If we get here, all models failed
    print(f"❌ All models failed. Last error: {last_error}")
    raise last_error


def _try_model_with_retries(transcript: str, model_name: str, max_retries: int) -> str:
    """
    Try a single model with retry logic
    """
    for attempt in range(max_retries):
        try:
            llm = LLM(
                model=f"groq/{model_name}",
                api_key=os.getenv("GROQ_API_KEY")
            )
            
            editor_agent = Agent(
                role="Newsletter Editor",
                goal="Transform video transcripts into engaging, email-friendly newsletter articles",
                backstory="You're an experienced newsletter editor who specializes in creating digestible, scannable content for busy readers who consume news via email.",
                verbose=True,
                allow_delegation=False,
                llm=llm
            )
            
            task = Task(
                description=f"{editorial_prompt}\n\nTranscript:\n{transcript}",
                expected_output="A well-formatted, email-friendly newsletter article without any promotional content.",
                agent=editor_agent
            )

            crew = Crew(
                agents=[editor_agent],
                tasks=[task],
                verbose=True
            )

            result = crew.kickoff()
            return result
            
        except Exception as e:
            error_type = type(e).__name__
            print(f"❌ {model_name} attempt {attempt + 1}/{max_retries} failed: {error_type}")
            
            if attempt < max_retries - 1:
                # Longer delays for rate limit errors
                if "RateLimitError" in error_type:
                    delay = 60 + (attempt * 30) + random.uniform(0, 10)  # 60s, 90s, 120s + jitter
                else:
                    delay = (2 ** attempt) + random.uniform(0, 1)  # Standard exponential backoff
                print(f"⏳ Retrying in {delay:.1f} seconds...")
                time.sleep(delay)
            else:
                # All retries for this model failed, raise to trigger fallback
                raise e