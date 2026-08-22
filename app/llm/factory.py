"""
LLM Factory — Model abstraction layer

Kyun abstraction?
- Aaj OpenAI, kal Anthropic, parso local Ollama
- Code change nahi karna padta — sirf .env change karo
- Testing mein mock LLM use kar sakte hain
- Cost optimization: chhote tasks ke liye smaller models
"""

from langchain_core.language_models import BaseChatModel
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger("llm_factory")


def get_llm(
    temperature: float = 0.1,
    model_override: str | None = None,
) -> BaseChatModel:
    """
    Settings ke hisaab se correct LLM return karo.

    Args:
        temperature: 0.0 = deterministic, 1.0 = creative
                    Security analysis ke liye 0.1 best hai
        model_override: Default model override karo

    Returns:
        LangChain compatible LLM object
    """
    provider = settings.llm_provider.lower()
    model = model_override or settings.llm_model_name

    logger.info("Initializing LLM", provider=provider, model=model)

    if provider == "openai":
        return _get_openai_llm(temperature, model)
    elif provider == "anthropic":
        return _get_anthropic_llm(temperature, model)
    elif provider == "groq":
        return _get_groq_llm(temperature, model)
    elif provider == "ollama":
        return _get_ollama_llm(temperature, model)
    else:
        logger.warning(f"Unknown provider {provider}, defaulting to OpenAI")
        return _get_openai_llm(temperature, model)


def _get_openai_llm(temperature: float, model: str) -> BaseChatModel:
    """OpenAI LLM — GPT-4o-mini default."""
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=settings.llm_api_key,
        max_tokens=2000,
    )


def _get_anthropic_llm(temperature: float, model: str) -> BaseChatModel:
    """Anthropic Claude LLM."""
    from langchain_anthropic import ChatAnthropic
    return ChatAnthropic(
        model=model,
        temperature=temperature,
        api_key=settings.llm_api_key,
        max_tokens=2000,
    )


# def _get_groq_llm(temperature: float, model: str) -> BaseChatModel:
#     """Groq LLM — very fast inference."""
#     from langchain_groq import ChatGroq
#     return ChatGroq(
#         model=model,
#         temperature=temperature,
#         groq_api_key=settings.llm_api_key,
#         max_tokens=2000,
#     )


def _get_ollama_llm(temperature: float, model: str) -> BaseChatModel:
    """Ollama — local LLM, no API key needed."""
    from langchain_ollama import ChatOllama
    return ChatOllama(
        model=model,
        temperature=temperature,
    )


# def get_llm(temperature: float = 0.1, strong: bool = False) -> BaseChatModel:
#     """
#     strong=True = 70b model (vulnerability reasoning, patch gen)
#     strong=False = 8b model (simple tasks, fast)
#     """
#     model = settings.llm_strong_model if strong else settings.llm_model_name
#     # ... rest same



def _get_groq_llm(temperature: float, model: str) -> BaseChatModel:
    """Groq LLM — very fast inference."""
    from langchain_groq import ChatGroq
    return ChatGroq(
        model=model,
        temperature=temperature,
        groq_api_key=settings.llm_api_key,
        max_tokens=2000,
    )