
import subprocess
import json
from pathlib import Path
import os
import shutil
from typing import List, Dict, Any
from loguru import logger

class SpotBugsWrapper:
    """SpotBugs 실행 및 SARIF 결과 파싱을 위한 래퍼"""

    def __init__(self, spotbugs_home: str = ""):
        self.spotbugs_home = self._find_spotbugs_home(spotbugs_home)
        self.spotbugs_cmd = self._get_spotbugs_cmd()

    def _find_spotbugs_home(self, provided_home: str) -> Path:
        if provided_home and Path(provided_home).exists():
            return Path(provided_home)
        
        env_home = os.environ.get("SPOTBUGS_HOME")
        if env_home and Path(env_home).exists():
            return Path(env_home)

        home_dir = Path.home()
        spotbugs_dirs = sorted(list(home_dir.glob("spotbugs-*")), reverse=True)
        if spotbugs_dirs:
            logger.info(f"자동 감지된 SpotBugs 설치 경로: {spotbugs_dirs[0]}")
            return spotbugs_dirs[0]

        return None

    def _get_spotbugs_cmd(self) -> str:
        if self.spotbugs_home:
            cmd = self.spotbugs_home / "bin" / "spotbugs"
            return str(cmd) if cmd.exists() else None
        
        cmd = shutil.which("spotbugs")
        if cmd:
            return cmd
        
        return None

    def ensure_spotbugs_installed(self) -> bool:
        if self.spotbugs_cmd:
            logger.info(f"SpotBugs 실행 파일: {self.spotbugs_cmd}")
            return True
        
        logger.error("SpotBugs를 찾을 수 없습니다. SPOTBUGS_HOME 환경 변수를 설정하거나 PATH에 추가해주세요.")
        logger.error("또는 ./install_spotbugs.sh 스크립트를 실행하여 설치할 수 있습니다.")
        return False

    def _compile_java_files(self, project_dir: Path) -> Path:
        java_files = list(project_dir.rglob("*.java"))
        if not java_files:
            logger.warning("컴파일할 Java 소스 파일이 없습니다.")
            return None

        compile_dir = project_dir / "target" / "classes"
        compile_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Java 파일 컴파일 시작... ({len(java_files)}개)")
        
        cmd = ["javac", "-d", str(compile_dir), "-sourcepath", str(project_dir)] + [str(f) for f in java_files]
        
        try:
            process = subprocess.run(cmd, capture_output=True, text=True, check=True, encoding='utf-8')
            logger.info("Java 파일 컴파일 성공.")
            logger.debug(f"javac stdout: {process.stdout}")
            return compile_dir
        except FileNotFoundError:
            logger.error("`javac` 명령을 찾을 수 없습니다. JDK가 설치되어 있고 PATH에 등록되어 있는지 확인하세요.")
            return None
        except subprocess.CalledProcessError as e:
            logger.error(f"Java 컴파일 실패. 반환 코드: {e.returncode}")
            logger.error(f"javac stderr: {e.stderr}")
            return None

    def analyze(self, project_dir: Path) -> List[Dict[str, Any]]:
        classes_dir = self._compile_java_files(project_dir)
        if not classes_dir:
            return []

        output_sarif = project_dir / "spotbugs_report.sarif"
        
        spotbugs_command = [
            self.spotbugs_cmd,
            "-sarif",
            f"-output",
            str(output_sarif),
            "-sourcepath",
            str(project_dir),
            str(classes_dir)
        ]

        logger.info("SpotBugs 분석 실행 중 (SARIF 모드)...")
        try:
            process = subprocess.run(spotbugs_command, capture_output=True, text=True, check=False, encoding='utf-8')
            if process.returncode != 0:
                 logger.warning(f"SpotBugs 실행 중 오류 발생 (Exit code: {process.returncode})")
                 logger.warning(f"SpotBugs stdout: {process.stdout}")
                 logger.warning(f"SpotBugs stderr: {process.stderr}")

        except FileNotFoundError:
            logger.error("SpotBugs 실행 파일을 찾을 수 없습니다.")
            return []
        
        if not output_sarif.exists():
            logger.error("SpotBugs가 SARIF 보고서 파일을 생성하지 않았습니다.")
            return []

        logger.info(f"SpotBugs SARIF 보고서 파싱: {output_sarif}")
        return self._parse_sarif_report(output_sarif, project_dir)

    def _parse_sarif_report(self, report_path: Path, project_dir: Path) -> List[Dict[str, Any]]:
        results = []
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                sarif_data = json.load(f)

            for run in sarif_data.get("runs", []):
                rules = {rule['id']: rule for rule in run.get("tool", {}).get("driver", {}).get("rules", [])}
                
                for result in run.get("results", []):
                    rule_id = result.get("ruleId")
                    message = result.get("message", {}).get("text", "")
                    level = result.get("level", "warning")

                    if not rule_id or not message:
                        continue

                    for location in result.get("locations", []):
                        phys_loc = location.get("physicalLocation", {})
                        artifact_loc = phys_loc.get("artifactLocation", {})
                        uri = artifact_loc.get("uri")
                        
                        if not uri:
                            continue
                            
                        region = phys_loc.get("region", {})
                        line = region.get("startLine", 1)

                        rule_info = rules.get(rule_id, {})
                        rule_name = rule_info.get("shortDescription", {}).get("text", rule_id)
                        
                        results.append({
                            "file": uri,
                            "line": line,
                            "rule_id": rule_id,
                            "rule_name": rule_name,
                            "message": message,
                            "severity": self._map_severity(level),
                        })

        except FileNotFoundError:
            logger.error(f"SARIF 파일을 찾을 수 없습니다: {report_path}")
        except json.JSONDecodeError:
            logger.error(f"SARIF 파일이 올바른 JSON 형식이 아닙니다: {report_path}")
        except Exception as e:
            logger.exception(f"SARIF 보고서 처리 중 예외 발생: {e}")
            
        return results

    def _map_severity(self, level: str) -> str:
        if level == "error":
            return "error"
        if level == "warning":
            return "warning"
        return "note"

