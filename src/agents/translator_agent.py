from crewai import Agent, Task, Crew

llm = "ollama/llama3:latest"

translation_prompt = (
    """
        You are a language expert tasked with translating articles into {language}.
        Preserve all Markdown formatting exactly as provided.

        ✅ Return only the translated Markdown text in {language} without additional explanations.
    """
)


def run_translation(article: str, language: str) -> str:
    translator_agent = Agent(
        role="Translator",
        goal="Translate articles while keeping formatting intact",
        backstory="Skilled linguist who produces accurate translations for publication.",
        verbose=True,
        allow_delegation=False,
        llm=llm,
    )

    task = Task(
        description=f"{translation_prompt.format(language=language)}\n\nArticle:\n{article}",
        expected_output=f"The article translated to {language} preserving Markdown formatting.",
        agent=translator_agent,
    )

    crew = Crew(agents=[translator_agent], tasks=[task], verbose=True)
    result = crew.kickoff()
    return result
