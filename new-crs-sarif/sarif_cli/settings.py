"""
설정 관리 - 환경 변수 및 설정 파일 지원
"""
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class SarifCliSettings(BaseSettings):
    """SARIF CLI 설정"""
    
    # LLM 관련 설정
    enable_llm: bool = Field(
        default=False,
        description="LLM 검증 활성화 여부"
    )
    
    llm_url: Optional[str] = Field(
        default=None,
        description="LLM 서비스 URL (예: http://localhost:8000)"
    )
    
    llm_api_key: Optional[str] = Field(
        default=None,
        description="LLM API 키"
    )
    
    llm_model: str = Field(
        default="gpt-4o",
        description="사용할 LLM 모델 이름"
    )
    
    llm_temperature: float = Field(
        default=0.0,
        description="LLM 온도 설정 (0.0-1.0)"
    )
    
    # SAST 도구 설정
    enable_joern: bool = Field(
        default=True,
        description="Joern 분석 활성화 (C/C++)"
    )
    
    enable_codeql: bool = Field(
        default=False,
        description="CodeQL 분석 활성화"
    )
    
    # 출력 설정
    sarif_include_fixes: bool = Field(
        default=True,
        description="SARIF에 fixes 섹션 포함 여부"
    )
    
    verbose: bool = Field(
        default=False,
        description="상세 로그 출력"
    )
    
    model_config = SettingsConfigDict(
        env_prefix="SARIF_CLI_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


def load_settings(
    enable_llm: Optional[bool] = None,
    llm_url: Optional[str] = None,
    llm_key: Optional[str] = None,
) -> SarifCliSettings:
    """
    설정 로드 (우선순위: CLI 인자 > 환경 변수 > .env 파일 > 기본값)
    
    Args:
        enable_llm: CLI에서 전달된 LLM 활성화 옵션
        llm_url: CLI에서 전달된 LLM URL
        llm_key: CLI에서 전달된 LLM API 키
    
    Returns:
        설정 객체
    """
    # 환경 변수 및 .env 파일에서 기본 설정 로드
    settings = SarifCliSettings()
    
    # CLI 인자가 제공되면 우선 적용
    if enable_llm is not None:
        settings.enable_llm = enable_llm
    
    if llm_url is not None:
        settings.llm_url = llm_url
    
    if llm_key is not None:
        settings.llm_api_key = llm_key
    
    # LLM URL이 설정되면 자동으로 LLM 활성화
    if settings.llm_url and not settings.enable_llm:
        settings.enable_llm = True
    
    return settings
