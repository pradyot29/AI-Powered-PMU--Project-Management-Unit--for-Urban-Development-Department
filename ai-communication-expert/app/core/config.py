from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "AI Communication Expert - PMU"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # API Keys - Made both optional, at least one required
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    
    # Database
    DATABASE_URL: str = "sqlite:///./pmu_communications.db"
    
    # AI Configuration
    PRIMARY_LLM: str = "anthropic"
    MODEL_NAME: str = "claude-sonnet-4-20250514"
    FALLBACK_MODEL: str = "gpt-4o"
    MAX_TOKENS: int = 4000
    TEMPERATURE: float = 0.3
    
    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE: int = 10
    MAX_TOKENS_PER_DAY: int = 1000000
    
    # File Storage
    OUTPUT_DIR: str = "./outputs"
    MAX_FILE_SIZE_MB: int = 10
    
    # Government Configuration
    DEPARTMENT_NAME: str = "Urban Development Department"
    STATE_NAME: str = "Maharashtra"
    OFFICE_ADDRESS: str = "Mantralaya, Mumbai - 400032"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()