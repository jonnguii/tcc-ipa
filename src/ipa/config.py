from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    supabase_url: str
    supabase_service_key: str
    gemini_api_key: str = ""
    gemini_model: str = ""
    ai_mode: str = "record"
    executor: str = "stub"
    erp_base_url: str = "http://localhost:8000"
    erp_sabotage: str = "none"
    rpa_headless: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
