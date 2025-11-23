"""
Bandit 래퍼 - Python 보안 취약점 분석
"""
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger
import shutil


def ensure_bandit_installed() -> bool:
    """Bandit이 설치되어 있는지 확인"""
    if shutil.which("bandit"):
        return True
    logger.error("Bandit이 설치되지 않았습니다. 'pip install bandit' 또는 'uv pip install bandit'로 설치하세요.")
    return False


class BanditAnalyzer:
    """Bandit을 사용한 Python 취약점 분석"""
    
    def __init__(self):
        self.bandit_cmd = shutil.which("bandit")
    
    def analyze(self, project_dir: Path) -> List[Dict[str, Any]]:
        """
        Bandit을 사용하여 Python 코드 분석
        
        Args:
            project_dir: 프로젝트 디렉토리
        
        Returns:
            취약점 정보 리스트
        """
        if not ensure_bandit_installed():
            return []
        
        logger.info(f"Bandit 분석 시작: {project_dir}")
        
        # Python 파일 찾기
        python_files = list(project_dir.rglob("*.py"))
        if not python_files:
            logger.warning("분석할 Python 파일이 없습니다.")
            return []
        
        # Bandit 실행 (JSON 출력)
        cmd = [
            "bandit",
            "-r",  # recursive
            str(project_dir),
            "-f", "json",  # JSON format
            "-ll",  # Low confidence, Low severity 이상만
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            
            # Bandit은 취약점을 발견하면 exit code 1을 반환
            # 0: 취약점 없음, 1: 취약점 발견
            if result.returncode not in [0, 1]:
                logger.warning(f"Bandit 실행 중 오류 발생 (Exit code: {result.returncode})")
                logger.warning(f"stderr: {result.stderr}")
                return []
            
            # JSON 파싱
            try:
                data = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                logger.error(f"Bandit JSON 출력 파싱 실패: {e}")
                logger.debug(f"stdout: {result.stdout}")
                return []
            
            # 결과 변환
            vulnerabilities = []
            for issue in data.get("results", []):
                vulnerabilities.append({
                    "file": issue.get("filename", "unknown"),
                    "line": issue.get("line_number", 0),
                    "rule_id": issue.get("test_id", "unknown"),
                    "rule_name": issue.get("test_name", "unknown"),
                    "message": issue.get("issue_text", ""),
                    "severity": self._map_severity(issue.get("issue_severity", "LOW")),
                    "confidence": issue.get("issue_confidence", "LOW"),
                    "code": issue.get("code", ""),
                })
            
            logger.info(f"Bandit 분석 완료: {len(vulnerabilities)}개 발견")
            return vulnerabilities
            
        except subprocess.TimeoutExpired:
            logger.error("Bandit 실행 시간 초과 (120초)")
            return []
        except Exception as e:
            logger.exception(f"Bandit 실행 중 오류: {e}")
            return []
    
    def _map_severity(self, bandit_severity: str) -> str:
        """Bandit severity를 표준 severity로 매핑"""
        severity_map = {
            "HIGH": "error",
            "MEDIUM": "warning",
            "LOW": "note",
        }
        return severity_map.get(bandit_severity.upper(), "warning")
