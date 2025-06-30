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
        - Start with the most important information first (inverted pyramid style)
        - Include a **compelling headline** that clearly summarizes the main story
        - Add a **brief summary sentence** right after the headline to hook readers

        📱 Email-Friendly Formatting:
        - Use **GitHub Flavored Markdown** that renders well in email clients
        - Structure content with:
            - `# Headline` (single H1 for the main story)
            - `## Subheadings` for major sections (use sparingly)
            - **Bold** for key terms and important points
            - Short bullet points (`-`) for lists when needed
            - Blank lines between all paragraphs for readability
        - ❌ Avoid: Long paragraphs, excessive formatting, code blocks, blockquotes

        📰 Content Guidelines:
        - **Lead with the key story** in the first 1-2 paragraphs
        - **Remove all promotional content**, sponsor mentions, and channel plugs
        - **Preserve factual accuracy** - don't add information not in the transcript
        - **Focus on newsworthy content** - what would interest newsletter readers?
        - **Provide context** when acronyms or specialized terms are mentioned
        - **End with implications** - why does this matter to readers?

        📧 Newsletter Format:
        - Keep articles **concise but complete** (aim for 200-400 words per story)
        - Write as if this will be **one article in a daily digest**
        - Make it **skimmable** - readers should get the key points even if they just scan

        ✅ Output only the final Markdown article - no explanations, thoughts, or system messages.
    """
)

def run_summary(transcript: str, model_name: str, max_retries: int = 3) -> str:
    """
    Run summary with retry logic for handling API failures
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
            print(f"❌ Attempt {attempt + 1}/{max_retries} failed: {error_type}")
            
            if attempt < max_retries - 1:
                # Exponential backoff with jitter
                delay = (2 ** attempt) + random.uniform(0, 1)
                print(f"⏳ Retrying in {delay:.1f} seconds...")
                time.sleep(delay)
            else:
                print(f"❌ All retry attempts failed. Last error: {e}")
                raise e