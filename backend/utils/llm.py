import json
import re
from langchain_ollama import ChatOllama
from backend.config import settings

def get_llm(temperature=None, force_json=True):
    """
    Get the configured LLM (Gemini if API key provided, otherwise Ollama).
    """
    temp = temperature if temperature is not None else settings.ollama_temperature

    if settings.gemini_api_key:
        from langchain_google_genai import ChatGoogleGenerativeAI
        kwargs = {
            "model": settings.gemini_model,
            "google_api_key": settings.gemini_api_key,
            "temperature": temp,
        }
        # Gemini handles JSON mode via model_kwargs or explicit instruction.
        if force_json:
             # We rely on the system prompt for JSON format with Gemini, 
             # but we can also set the mime type.
             kwargs["model_kwargs"] = {"response_mime_type": "application/json"}
        return ChatGoogleGenerativeAI(**kwargs)
    else:
        kwargs = {
            "model": settings.ollama_model,
            "base_url": settings.ollama_base_url,
            "temperature": temp,
        }
        if force_json:
            kwargs["format"] = "json"
        return ChatOllama(**kwargs)

def clean_json_response(content: str) -> dict:
    """
    Clean the LLM output to ensure it's valid JSON.
    Removes markdown code blocks if the LLM includes them.
    """
    try:
        # First try to parse it directly
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Extract JSON from markdown block if present
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', content, re.DOTALL | re.IGNORECASE)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
            
    # Try finding the first '{' and last '}'
    start = content.find('{')
    end = content.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(content[start:end+1])
        except json.JSONDecodeError:
            pass

    raise ValueError("Could not parse valid JSON from LLM response")
