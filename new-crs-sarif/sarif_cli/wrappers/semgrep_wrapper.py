"""
Semgrep 래퍼 - JavaScript/TypeScript 보안 취약점 분석
"""
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger
import shutil


def ensure_semgrep_installed() -> bool:
    """Semgrep이 설치되어 있는지 확인"""
    if shutil.which("semgrep"):
        return True
    logger.error("Semgrep이 설치되지 않았습니다. 'pip install semgrep' 또는 'brew install semgrep'로 설치하세요.")
    return False


class SemgrepAnalyzer:
    """Semgrep을 사용한 다중 언어 취약점 분석"""
    
    def __init__(self):
        self.semgrep_cmd = shutil.which("semgrep")
    
    def analyze(self, project_dir: Path, language: str = "auto") -> List[Dict[str, Any]]:
        """
        Semgrep을 사용하여 코드 분석
        
        Args:
            project_dir: 프로젝트 디렉토리
            language: 분석할 언어 ("javascript", "python", "java", "auto")
        
        Returns:
            취약점 정보 리스트 (경량화된 형식)
        """
        if not ensure_semgrep_installed():
            return []
        
        logger.info(f"Semgrep 분석 시작: {project_dir} (언어: {language})")
        
        # Semgrep 실행 (SARIF 출력)
        cmd = [
            "semgrep",
            "--config=auto",  # 자동 규칙 선택
            "--sarif",        # SARIF 형식 출력
            "--quiet",        # 불필요한 출력 제거
            str(project_dir),
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,
            )
            
            # Semgrep은 취약점을 발견하면 exit code 1을 반환
            if result.returncode not in [0, 1]:
                logger.warning(f"Semgrep 실행 중 오류 발생 (Exit code: {result.returncode})")
                logger.warning(f"stderr: {result.stderr}")
                return []
            
            # SARIF 파싱 (경량화)
            try:
                sarif_data = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                logger.error(f"Semgrep SARIF 출력 파싱 실패: {e}")
                logger.debug(f"stdout: {result.stdout[:500]}")
                return []
            
            # 경량화된 결과 추출
            vulnerabilities = self._parse_sarif_lightweight(sarif_data, project_dir)
            
            logger.info(f"Semgrep 분석 완료: {len(vulnerabilities)}개 발견")
            return vulnerabilities
            
        except subprocess.TimeoutExpired:
            logger.error("Semgrep 실행 시간 초과 (180초)")
            return []
        except Exception as e:
            logger.exception(f"Semgrep 실행 중 오류: {e}")
            return []
    
    def _parse_sarif_lightweight(self, sarif_data: Dict[str, Any], project_dir: Path) -> List[Dict[str, Any]]:
        """
        Semgrep SARIF에서 필요한 정보만 추출 (경량화)
        
        LLM에 전달할 때 불필요한 메타데이터를 제거하고 핵심 정보만 추출
        """
        vulnerabilities = []
        
        for run in sarif_data.get("runs", []):
            # 규칙 정보 추출 (간소화)
            rules = {}
            for rule in run.get("tool", {}).get("driver", {}).get("rules", []):
                rule_id = rule.get("id")
                rules[rule_id] = {
                    "name": rule.get("shortDescription", {}).get("text", rule_id),
                    "severity": rule.get("properties", {}).get("security-severity", "5.0"),
                    # 긴 설명은 제외 (LLM에 불필요)
                }
            
            # 결과 추출 (핵심 정보만)
            for result in run.get("results", []):
                rule_id = result.get("ruleId")
                message = result.get("message", {}).get("text", "")
                
                # 위치 정보
                for location in result.get("locations", []):
                    phys_loc = location.get("physicalLocation", {})
                    artifact_loc = phys_loc.get("artifactLocation", {})
                    uri = artifact_loc.get("uri", "")
                    
                    if not uri:
                        continue
                    
                    region = phys_loc.get("region", {})
                    line = region.get("startLine", 1)
                    
                    # 코드 스니펫 (짧게)
                    snippet = region.get("snippet", {}).get("text", "")
                    if len(snippet) > 200:
                        snippet = snippet[:200] + "..."
                    
                    rule_info = rules.get(rule_id, {})
                    
                    vulnerabilities.append({
                        "file": uri,
                        "line": line,
                        "rule_id": rule_id,
                        "rule_name": rule_info.get("name", rule_id),
                        "message": message,
                        "severity": self._map_severity(rule_info.get("severity", "5.0")),
                        "code": snippet,  # 짧은 스니펫만
                        "tool_name": "Semgrep",
                        "tool_metadata": run.get("tool", {}),
                    })
        
        return vulnerabilities
    
    def _map_severity(self, semgrep_severity: str) -> str:
        """Semgrep severity (0-10)를 표준 severity로 매핑"""
        try:
            score = float(semgrep_severity)
            if score >= 7.0:
                return "error"
            elif score >= 4.0:
                return "warning"
            else:
                return "note"
        except (ValueError, TypeError):
            return "warning"
