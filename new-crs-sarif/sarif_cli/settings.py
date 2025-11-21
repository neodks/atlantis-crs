"""
SARIF CLI 설정 모듈
"""
import os
from pathlib import Path

# 기본 경로 설정
BASE_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = BASE_DIR / "prompts"

# Aux 분석 설정
# 환경 변수 'ENABLE_AUX_ANALYSIS'가 'true'일 경우 활성화 (대소문자 구분 없음)
ENABLE_AUX_ANALYSIS = os.getenv("ENABLE_AUX_ANALYSIS", "false").lower() == "true"

# Aux 분석 타임아웃 (초)
AUX_ANALYSIS_TIMEOUT = int(os.getenv("AUX_ANALYSIS_TIMEOUT", "300"))

# LLM 설정
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
LLM_URL = os.getenv("LLM_URL", "http://localhost:11434")

# 프롬프트 파일 경로
BASIC_PROMPT_FILE = PROMPTS_DIR / "basic.txt"
AUX_ENHANCED_PROMPT_FILE = PROMPTS_DIR / "aux_enhanced.txt"
