import os
from contextlib import contextmanager
from groq import Groq

@contextmanager
def managed_groq():
    """
    Context manager for Groq API - no server management needed.
    Just validates the API key is available.
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise EnvironmentError("GROQ_API_KEY environment variable is required.")
    
    print("🚀 Using Groq API...")
    try:
        yield
    finally:
        print("✅ Groq API session completed.")

def get_groq_llm(model_name: str):
    """
    Returns a Groq LLM instance for use with CrewAI.
    model_name: The Groq model to use (required).
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise EnvironmentError("GROQ_API_KEY environment variable is required.")
    
    from langchain_groq import ChatGroq
    
    return ChatGroq(
        groq_api_key=groq_api_key,
        model=model_name,
        temperature=0.1,
        max_tokens=4096
    )