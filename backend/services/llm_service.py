from langchain_groq import ChatGroq
from backend.core.config import settings


class LLMService:
    def __init__(self, model_name: str | None = None, temperature: float = 0.1):
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables.")

        self.model_name = model_name or settings.default_llm_model
        self.llm = ChatGroq(
            model_name=self.model_name,
            groq_api_key=settings.groq_api_key,
            temperature=temperature,
        )

    def get_llm(self) -> ChatGroq:
        return self.llm

    def invoke(self, prompt: str) -> str:
        response = self.llm.invoke(prompt)
        return response.content if hasattr(response, "content") else str(response)


def get_llm(model_name: str | None = None, temperature: float = 0.1) -> ChatGroq:
    return LLMService(model_name=model_name, temperature=temperature).get_llm()
