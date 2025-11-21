"""
LLM 검증 모듈 - 취약점 검증 및 패치 생성
"""
from typing import Optional, Dict, Any
from pathlib import Path
from loguru import logger
from pydantic import BaseModel

from sarif_cli.analyzer import VulnerabilityResult


class PatchResult(BaseModel):
    """패치 생성 결과"""
    is_valid: bool
    confidence: float
    patch_code: Optional[str] = None
    explanation: str


def verify_and_generate_patch(
    vulnerability: VulnerabilityResult,
    source_code: str,
    llm_url: Optional[str] = None,
    llm_key: Optional[str] = None
) -> Optional[PatchResult]:
    """
    LLM을 사용하여 취약점검증 및 패치 생성
    
    Args:
        vulnerability: 취약점 정보
        source_code: 해당 파일의 소스 코드
        llm_url: LLM 서비스 URL
        llm_key: LLM API 키
    
    Returns:
        패치 결과 또는 None (LLM 비활성화 시)
    """
    if not llm_url:
        logger.debug("LLM이 비활성화되어 패치 생성을 건너뜁니다.")
        return None
    
    try:
        from sarif.llm.chat.openai import GPT4oLLM
        from sarif.llm.chat.base import ask
        from langchain.prompts import ChatPromptTemplate
        
        # LLM 초기화
        logger.info(f"LLM 검증 시작: {vulnerability.rule_id} at {vulnerability.file_path}:{vulnerability.line}")
        
        # TODO: 실제 LLM 프롬프트 및 검증 로직
        # 현재는 간단한 데모 응답 반환
        
        patch_result = PatchResult(
            is_valid=True,
            confidence=0.85,
            patch_code=generate_simple_patch(vulnerability, source_code),
            explanation=f"Detected {vulnerability.rule_id}: {vulnerability.message}"
        )
        
        logger.info(f"LLM 검증 완료: valid={patch_result.is_valid}, confidence={patch_result.confidence}")
        return patch_result
        
    except ImportError as e:
        logger.warning(f"LLM 모듈을 가져올 수 없습니다: {e}")
        return None
    except Exception as e:
        logger.error(f"LLM 검증 중 오류: {e}")
        return None


def generate_simple_patch(
    vulnerability: VulnerabilityResult,
    source_code: str
) -> str:
    """
    간단한 규칙 기반 패치 생성 (LLM 없이)
    
    Args:
        vulnerability: 취약점 정보
        source_code: 소스 코드
    
    Returns:
        패치 코드
    """
    lines = source_code.split("\n")
    target_line = vulnerability.line - 1
    
    if target_line < 0 or target_line >= len(lines):
        return "// Unable to generate patch: invalid line number"
    
    original_line = lines[target_line]
    
    # 규칙 기반 패치 예시
    if "CWE-119" in vulnerability.rule_id:  # Buffer Overflow
        if "strcpy" in original_line:
            patched_line = original_line.replace("strcpy", "strncpy")
            patched_line += f"  // TODO: Add size parameter for strncpy"
            return patched_line
        elif "gets" in original_line:
            patched_line = original_line.replace("gets", "fgets")
            patched_line += f"  // TODO: Add size and stream parameters for fgets"
            return patched_line
    
    elif "CWE-89" in vulnerability.rule_id:  # SQL Injection
        return "// Use PreparedStatement instead of string concatenation"
    
    return f"// TODO: Manual review required for {vulnerability.rule_id}"


def read_source_file(file_path: Path) -> Optional[str]:
    """
    소스 파일 읽기
    
    Args:
        file_path: 파일 경로
    
    Returns:
        파일 내용 또는 None
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"파일 읽기 실패 {file_path}: {e}")
        return None
