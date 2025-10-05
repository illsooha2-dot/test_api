# backend/app/config.py
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # .env 값들
    MOCK_BASE_URL: str = "https://mockapi.kiwoom.com"
    APP_KEY: str = ""
    APP_SECRET: str = ""
    ACCOUNT_NO: str = ""
    ACNT_PRDT_CD: str = "01"
    DEBUG: int = 0

    # 내부에서 통일해서 쓰기 위한 별칭
    @property
    def base_url(self) -> str:
        return self.MOCK_BASE_URL

    # pydantic-settings v2 방식
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[1] / ".env"),
        extra="ignore",
    )

settings = Settings()
