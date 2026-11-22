import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Settings(BaseModel):
    app_name: str = "7-Agent Multi-Agent AI Research System"
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    tavily_api_key: str = os.getenv("TAVILY_API_KEY", "")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/research_system.db")
    max_research_retries: int = int(os.getenv("MAX_RESEARCH_RETRIES", "2"))
    default_llm_model: str = os.getenv("DEFAULT_LLM_MODEL", "openai/gpt-oss-120b")
    vector_store_dir: str = os.getenv("VECTOR_STORE_DIR", "data/vector_store")
    reports_dir: str = os.getenv("REPORTS_DIR", "reports")

    def validate_keys(self) -> dict[str, bool]:
        return {
            "groq_configured": bool(self.groq_api_key),
            "gemini_configured": bool(self.gemini_api_key),
            "tavily_configured": bool(self.tavily_api_key),
        }


settings = Settings()
