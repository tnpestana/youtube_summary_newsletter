from crewai import Agent, Task, Crew

llm = "ollama/llama3:latest"

translation_prompt = (
    """
        You are an expert translator. Translate the provided article into {language}.

        🔒 Preserve all factual information and markdown structure.
        🚫 Do not add explanations or extra commentary.
        ✅ Return only the translated article in Markdown format.
    """
)

def run_translation(article: str, language: str) -> str:
    translator = Agent(
        role="Translator",
        goal=f"Translate articles to {language}",
        backstory="You help deliver the newsletter in multiple languages.",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

    task = Task(
        description=translation_prompt.format(language=language) + f"\n\nArticle:\n{article}",
        expected_output=f"The article translated into {language}.",
        agent=translator
    )

    crew = Crew(
        agents=[translator],
        tasks=[task],
        verbose=True
    )

    result = crew.kickoff()
    return result

