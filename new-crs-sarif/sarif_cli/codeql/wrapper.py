
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any, Literal

from loguru import logger

from .database import Database
from .analyze import run_codeql_analysis
from .common import temporary_dir, codeql_path


class CodeQLWrapper:
    """CodeQL 분석을 위한 고수준 래퍼"""

    def __init__(self):
        import os
        # codeql_path가 절대 경로인지 확인
        if not os.path.exists(codeql_path):
            raise FileNotFoundError(
                f"CodeQL 실행 파일을 찾을 수 없습니다: {codeql_path}\\n"
                "설치하려면 install_codeql.sh를 실행하거나 PATH에 추가하세요."
            )
        logger.info(f"CodeQL 실행 파일 확인 완료: {codeql_path}")

    def analyze(
        self,
        project_dir: Path,
        language: Literal["c", "cpp", "java"],
        build_command: str | List[str] | None = None,
    ) -> List[Dict[str, Any]]:
        """
        주어진 프로젝트에 대해 CodeQL 분석을 실행하고 결과를 반환합니다.

        Args:
            project_dir: 분석할 소스 코드가 있는 프로젝트 디렉토리.
            language: 분석할 언어 ("c", "cpp", "java").
            build_command: 프로젝트 빌드 명령어 (선택 사항).

        Returns:
            발견된 취약점 목록.
        """
        logger.info(f"{language} 프로젝트 분석 시작: {project_dir}")

        db_dir = temporary_dir(prefix="codeql_db_")
        results_dir = temporary_dir(prefix="codeql_results_")
        db_path = db_dir / f"{project_dir.name}-db"
        sarif_output_path = results_dir / f"{project_dir.name}-results.sarif"

        try:
            # 1. CodeQL 데이터베이스 생성
            logger.info("CodeQL 데이터베이스 생성 중...")
            
            db = Database.create(
                language=language,
                db_path=db_path,
                src_path=project_dir,
                command=build_command,
            )
            logger.success(f"데이터베이스 생성 완료: {db.path}")

            # 2. CodeQL 분석 실행 및 SARIF 파일 생성
            logger.info("CodeQL 분석 실행 중...")
            run_name = f"{project_dir.name}-{language}-run"
            
            # C와 C++를 동일하게 처리
            analysis_lang = "c" if language == "cpp" else language
            
            run_codeql_analysis(
                db=db,
                run_name=run_name,
                language=analysis_lang,
                output=sarif_output_path,
                extended=True,  # 확장된 쿼리 셋 사용
            )
            logger.success(f"분석 완료. SARIF 파일 생성: {sarif_output_path}")

            # 3. SARIF 파일 파싱
            if sarif_output_path.exists():
                return self._parse_sarif_report(sarif_output_path)
            else:
                logger.warning("SARIF 출력 파일이 생성되지 않았습니다.")
                return []

        except Exception as e:
            logger.error(f"CodeQL 분석 중 오류 발생: {e}", exc_info=True)
            return []
        finally:
            # 4. 임시 데이터베이스 및 결과 파일 정리
            logger.info("임시 파일 정리...")
            shutil.rmtree(db_dir, ignore_errors=True)
            shutil.rmtree(results_dir, ignore_errors=True)


    def _parse_sarif_report(self, report_path: Path) -> List[Dict[str, Any]]:
        """
        SARIF 파일을 파싱하여 취약점 정보를 추출합니다.
        """
        logger.info(f"SARIF 파일 파싱: {report_path}")
        results = []
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                sarif_data = json.load(f)

            for run in sarif_data.get("runs", []):
                rules = {
                    rule['id']: rule for rule in run.get("tool", {}).get("driver", {}).get("rules", [])
                }
                
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
                            "severity": level,
                        })
            logger.info(f"{len(results)}개의 결과를 파싱했습니다.")
        except json.JSONDecodeError:
            logger.error(f"SARIF 파일이 올바른 JSON 형식이 아닙니다: {report_path}")
        except Exception as e:
            logger.exception(f"SARIF 보고서 처리 중 예외 발생: {e}")
            
        return results
