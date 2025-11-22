"""
LLM 검증 모듈 - 취약점 검증 및 패치 생성
OpenAI compatible API 사용 (Ollama 포함)
"""
from typing import Optional, Dict, Any
from pathlib import Path
from loguru import logger
from pydantic import BaseModel
import os

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from sarif_cli.analyzer import VulnerabilityResult
from sarif_cli.config.settings import config
from sarif_cli.core.aux_analyser import AuxAnalyser


class PatchResult(BaseModel):
    """패치 생성 결과"""
    is_valid: bool
    confidence: float
    patch_code: Optional[str] = None
    explanation: str


def verify_and_generate_patch(
    vulnerability: VulnerabilityResult,
    project_dir: Path,
    language: str,
    llm_url: str = "http://localhost:11434",
    api_key: str = "not-needed"
) -> Dict[str, Any]:
    """
    LLM을 사용하여 취약점 검증 및 패치 생성
    
    Args:
        vulnerability: 취약점 정보
        project_dir: 프로젝트 디렉토리
        language: 언어
        llm_url: LLM API URL
        api_key: API 키
        
    Returns:
        검증 결과 및 패치 (JSON)
    """
    try:
        # 소스 코드 읽기
        source_code = read_source_file(vulnerability.file_path, project_dir, vulnerability.line)
        if not source_code:
            logger.warning(f"소스 코드를 읽을 수 없음: {vulnerability.file_path}")
            return {"is_valid": False, "explanation": "Source code not found"}
        
        # Aux 분석 실행
        aux_analyser = AuxAnalyser(project_dir, language)
        aux_result = aux_analyser.analyze_reachability(vulnerability.file_path, vulnerability.line)
        
        # 프롬프트 선택 및 로드
        if config.ENABLE_AUX:
            prompt_file = config.AUX_ENHANCED_PROMPT_FILE
            logger.info(f"Aux Enhanced Prompt 사용: {prompt_file}")
        else:
            prompt_file = config.BASIC_PROMPT_FILE
            logger.info(f"Basic Prompt 사용: {prompt_file}")
            
        try:
            prompt_content = prompt_file.read_text(encoding="utf-8")
            # Split system and human prompts (assuming separated by ---)
            parts = prompt_content.split("---")
            if len(parts) >= 2:
                system_prompt = parts[0].strip()
                human_prompt_template = parts[1].strip()
            else:
                # Fallback if format is wrong
                system_prompt = "You are a security expert."
                human_prompt_template = prompt_content
        except Exception as e:
            logger.error(f"프롬프트 파일 로드 실패: {e}")
            return {"is_valid": False, "explanation": "Prompt load failed"}

        # LLM 초기화
        logger.info(f"LLM 검증 시작: {vulnerability.rule_id} at {vulnerability.file_path}:{vulnerability.line}")
        
        # 로컬 LLM (Ollama 등 OpenAI compatible API)
        model_name = config.OLLAMA_MODEL
        
        # Ollama는 /v1을 base_url에 포함해야 함
        base_url = config.LLM_URL
        if not base_url.endswith("/v1"):
            base_url = f"{base_url}/v1"
        
        logger.info(f"로컬 LLM 사용: {base_url}, 모델: {model_name}")
        llm = ChatOpenAI(
            base_url=base_url,
            api_key="not-needed",  # 로컬 LLM은 API 키 불필요
            model=model_name,
            temperature=0.3
        )
        
        # 프롬프트 템플릿 작성
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt_template)
        ])
        
        # 체인 생성
        chain = prompt_template | llm | JsonOutputParser()
        
        # 실행
        input_vars = {
            "rule_id": vulnerability.rule_id,
            "message": vulnerability.message,
            "file_path": str(vulnerability.file_path),
            "line": vulnerability.line,
            "severity": vulnerability.severity,
            "source_code": source_code
        }
        
        # Aux 정보가 필요한 경우 추가
        if config.ENABLE_AUX:
            input_vars["aux_reachable"] = "Yes" if aux_result.reachable else "No"
            input_vars["aux_call_stack"] = "\n".join(aux_result.call_stack)
            input_vars["aux_data_flow"] = "\n".join(aux_result.data_flow)
            
        result = chain.invoke(input_vars)
        
        logger.info(f"검증 완료: {result.get('is_valid')}, 신뢰도: {result.get('confidence')}")
        return result
        
    except Exception as e:
        logger.exception(f"LLM 검증 중 오류 발생: {e}")
        # 오류 발생 시 기본값 반환 (안전하게 False 처리)
        return {
            "is_valid": False, 
            "confidence": 0.0, 
            "explanation": f"Error during verification: {str(e)}",
            "patch_code": None
        }


def _generate_rule_based_patch(
    vulnerability: VulnerabilityResult,
    source_code: str
) -> PatchResult:
    """
    규칙 기반 패치 생성 (LLM 없이)
    
    Args:
        vulnerability: 취약점 정보
        source_code: 소스 코드
    
    Returns:
        패치 결과
    """
    patch_code = generate_simple_patch(vulnerability, source_code)
    
    return PatchResult(
        is_valid=True,
        confidence=0.5,  # 규칙 기반이므로 낮은 신뢰도
        patch_code=patch_code,
        explanation=f"Rule-based patch for {vulnerability.rule_id}"
    )


def _get_code_context(source_code: str, line_num: int, context_lines: int = 5) -> str:
    """
    특정 라인 주변의 코드 context 추출
    
    Args:
        source_code: 전체 소스 코드
        line_num: 대상 라인 번호 (1-indexed)
        context_lines: context로 포함할 앞뒤 라인 수
    
    Returns:
        context 코드
    """
    lines = source_code.split("\n")
    start = max(0, line_num - context_lines - 1)
    end = min(len(lines), line_num + context_lines)
    
    context_lines_list = []
    for i in range(start, end):
        prefix = ">>> " if i == line_num - 1 else "    "
        context_lines_list.append(f"{prefix}{i+1:4d} | {lines[i]}")
    
    return "\n".join(context_lines_list)


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
    if "CWE-119" in vulnerability.rule_id or "buffer" in vulnerability.rule_id.lower():  # Buffer Overflow
        if "strcpy" in original_line:
            patched_line = original_line.replace("strcpy", "strncpy")
            patched_line += f"  // TODO: Add size parameter for strncpy"
            return patched_line
        elif "gets" in original_line:
            patched_line = original_line.replace("gets", "fgets")
            patched_line += f"  // TODO: Add size and stream parameters for fgets"
            return patched_line
    
    elif "CWE-89" in vulnerability.rule_id or "SQL" in vulnerability.rule_id:  # SQL Injection
        return "// Use PreparedStatement instead of string concatenation"
    
    elif "NP_ALWAYS_NULL" in vulnerability.rule_id or "null" in vulnerability.rule_id.lower():
        return "// Add null check before dereferencing"
    
    return f"// TODO: Manual review required for {vulnerability.rule_id}"


def read_source_file(file_path: Path, project_dir: Path = None, line: int = 0) -> Optional[str]:
    """
    소스 파일 읽기
    
    Args:
        file_path: 파일 경로
        project_dir: 프로젝트 디렉토리 (옵션)
        line: 라인 번호 (옵션, 컨텍스트 추출용)
    
    Returns:
        파일 내용 또는 컨텍스트
    """
    try:
        # 절대 경로 변환
        abs_path = file_path
        if not abs_path.is_absolute():
            if project_dir:
                abs_path = project_dir / file_path
            else:
                # 프로젝트 디렉토리가 없으면 현재 작업 디렉토리 기준
                abs_path = Path.cwd() / file_path
                
        if not abs_path.exists():
            logger.error(f"파일을 찾을 수 없음: {abs_path}")
            return None
            
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        if line > 0:
            return _get_code_context(content, line)
        return content
            
    except Exception as e:
        logger.error(f"파일 읽기 실패 {file_path}: {e}")
        return None
