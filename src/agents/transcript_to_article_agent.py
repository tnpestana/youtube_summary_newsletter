from crewai import Agent, Task, Crew

llm = "ollama/llama3:latest"

editorial_prompt = (
    """
        You are a professional editorial assistant. Your task is to convert a raw transcript into a polished, human-readable article in {language}.

        ✍️ Writing guidelines:
        - Write in **long, well-structured paragraphs** with smooth transitions.
        - Use natural, flowing language and complete, complex sentences.
        - Maintain a **professional tone** suitable for news or analysis.
        - Include a **clear, descriptive title** at the top as a Markdown `# H1` heading.

        🧱 Formatting rules:
        - Use **GitHub Flavored Markdown** (GFM), following the **CommonMark** spec exactly: https://commonmark.org/
        - Use:
            - `#` for headings
            - Blank lines for paragraph breaks
            - `**bold**`, `*italic*` for emphasis
            - `-` or `*` for bullet points
            - Triple backticks for code blocks
            - `>` for blockquotes
            - `[label](url)` for links
        - ❌ Do **not** use any HTML tags or styling.

        📋 Content rules:
        - 🔒 **Preserve all factual information.**
        - 🚫 **Remove all promotional content or sponsorship mentions.**
        - ❌ Do not hallucinate, assume, or fabricate any information.
        - ❌ Do not summarize—rewrite into full article form.

        📦 Output rules:
        - ✅ Only output the **final Markdown-formatted article**.
        - ❌ Do **not** include any system messages, reasoning, thoughts, or explanations.
        - ❌ Do not include text like: “Thought:”, “Observation:”, or similar.

        ✅ Return only the complete, final Markdown article in the {language} language.
    """
)

def run_summary(transcript: str, language: str = "en-US") -> str:
    editor_agent = Agent(
        role="Editorial Assistant",
        goal="Rewrite transcripts into accurate, well-structured articles",
        backstory="You're part of a media team focused on transforming raw transcripts into compelling written articles.",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
    
    task = Task(
        description=f"{editorial_prompt.format(language=language)}\n\nTranscript:\n{transcript}",
        expected_output=f"A well-formatted article in {language} without any promotional content.",
        agent=editor_agent
    )

    crew = Crew(
        agents=[editor_agent],
        tasks=[task],
        verbose=True
    )

    result = crew.kickoff()
    return result
