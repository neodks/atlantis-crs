"""
SARIF CLI 설정 모듈
"""
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class _Settings(BaseSettings):
    """
    CLI 및 환경 변수 설정을 관리하는 Pydantic 모델
    우선순위: CLI 인자 > 환경 변수 > .env 파일 > 기본값
    """
    model_config = SettingsConfigDict(
        env_file='.env',
        env_prefix='SARIF_CLI_',  # e.g. SARIF_CLI_ENABLE_LLM
        env_file_encoding='utf-8',
        extra='ignore'  # Allow extra fields in kwargs
    )

    # LLM 설정
    ENABLE_LLM: bool = False
    LLM_URL: Optional[str] = "http://localhost:11434"
    LLM_API_KEY: Optional[str] = Field(None, alias='llm_key')
    OLLAMA_MODEL: str = "qwen2.5:7b"

    # Aux 분석 설정
    ENABLE_AUX: bool = False
    AUX_ANALYSIS_TIMEOUT: int = 300

    # 경로 설정
    BASE_DIR: Path = Path(__file__).resolve().parent
    PROMPTS_DIR: Path = BASE_DIR / "prompts"
    BASIC_PROMPT_FILE: Path = PROMPTS_DIR / "basic.txt"
    AUX_ENHANCED_PROMPT_FILE: Path = PROMPTS_DIR / "aux_enhanced.txt"


config = _Settings()


def load_settings(**kwargs) -> _Settings:
    """
    설정 객체를 로드하고 CLI 인자로 업데이트합니다.
    None이 아닌 CLI 인자만 사용하여 기존 설정을 덮어씁니다.
    """
    # None 값을 제거하여 명시적으로 제공된 인자만 사용
    cli_args = {k.upper(): v for k, v in kwargs.items() if v is not None}
    global config
    config = _Settings(**cli_args)
    return config
