"""
언어 감지 모듈 - 파일 확장자 기반 언어 자동 감지
"""
from pathlib import Path
from typing import Set
from loguru import logger


# 언어별 파일 확장자 매핑
LANGUAGE_EXTENSIONS = {
    "c": {".c", ".h"},
    "cpp": {".cpp", ".cc", ".cxx", ".hpp", ".hxx", ".h++"},
    "java": {".java"},
    "python": {".py"},
    "javascript": {".js", ".jsx", ".ts", ".tsx"},
}


def detect_languages(project_dir: Path) -> Set[str]:
    """
    프로젝트 디렉토리에서 사용된 프로그래밍 언어를 감지합니다.
    
    Args:
        project_dir: 분석할 프로젝트 디렉토리
    
    Returns:
        감지된 언어 집합 (예: {"c", "java"})
    """
    detected_languages = set()
    
    # 모든 파일 순회
    for file_path in project_dir.rglob("*"):
        if not file_path.is_file():
            continue
        
        ext = file_path.suffix.lower()
        
        # 언어별 확장자 매칭
        for language, extensions in LANGUAGE_EXTENSIONS.items():
            if ext in extensions:
                detected_languages.add(language)
                logger.info(f"감지: {file_path.name} → {language}")
    
    if not detected_languages:
        logger.warning("지원되는 언어를 찾을 수 없습니다.")
    
    return detected_languages


def get_files_by_language(project_dir: Path, language: str) -> list[Path]:
    """
    특정 언어의 소스 파일만 반환합니다.
    
    Args:
        project_dir: 프로젝트 디렉토리
        language: 언어 (예: "c", "java")
    
    Returns:
        해당 언어의 파일 경로 리스트
    """
    extensions = LANGUAGE_EXTENSIONS.get(language, set())
    files = []
    
    for file_path in project_dir.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in extensions:
            files.append(file_path)
    
    return files
