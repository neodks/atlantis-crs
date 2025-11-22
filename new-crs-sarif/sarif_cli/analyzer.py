"""
SAST 분석 실행 모듈 - 다양한 SAST 도구 통합
"""
from pathlib import Path
from typing import Set, List, Dict, Any
from loguru import logger

from sarif_cli.detector import get_files_by_language


class VulnerabilityResult:
    """취약점 분석 결과"""
    def __init__(
        self,
        file_path: Path,
        line: int,
        column: int,
        rule_id: str,
        message: str,
        severity: str = "warning",
    ):
        self.file_path = file_path
        self.line = line
        self.column = column
        self.rule_id = rule_id
        self.message = message
        self.severity = severity


def analyze_with_codeql(project_dir: Path, language: str) -> List[VulnerabilityResult]:
    """
    CodeQL을 사용하여 코드 분석
    
    Args:
        project_dir: 프로젝트 디렉토리
        language: 분석할 언어
    
    Returns:
        취약점 결과 리스트
    """
    logger.info(f"CodeQL 분석 시작 ({language})")
    
    try:
        from sarif_cli.codeql.wrapper import CodeQLWrapper
        
        codeql_wrapper = CodeQLWrapper()
        
        # TODO: This is a temporary solution for simple projects.
        # A more robust solution should detect the build system (e.g., make, maven, gradle).
        build_command = None
        if language == "java":
            java_files = list(project_dir.rglob("*.java"))
            if java_files:
                build_command = "javac " + " ".join([str(f.relative_to(project_dir)) for f in java_files])
        elif language in ["c", "cpp"]:
            c_files = list(project_dir.rglob("*.c"))
            cpp_files = list(project_dir.rglob("*.cpp"))
            all_files = c_files + cpp_files
            if all_files:
                compiler = "g++" if cpp_files else "gcc"
                # Compile files individually to avoid object file collisions and ensure CodeQL traces all of them
                # Create a temporary build script to avoid quoting issues with sh -c
                build_script_path = project_dir / "build_codeql.sh"
                with open(build_script_path, "w") as f:
                    f.write("#!/bin/bash\n")
                    f.write("set -e\n") # Stop on error
                    for file in all_files:
                        rel_path = file.relative_to(project_dir)
                        obj_file = str(rel_path).replace("/", "_") + ".o"
                        f.write(f"{compiler} -c {str(rel_path)} -o {obj_file}\n")
                
                import os
                os.chmod(build_script_path, 0o755)
                
                build_command = f"./{build_script_path.name}"

        try:
            raw_results = codeql_wrapper.analyze(
                project_dir=project_dir,
                language=language,
                build_command=build_command,
            )
            import sys
            print(f"DEBUG: {language} raw_results: {len(raw_results)}", file=sys.stderr)
            for r in raw_results:
                print(f"DEBUG: {language} result file: {r.get('file')}", file=sys.stderr)
        finally:
            # Clean up build script if it exists
            if build_command and "build_codeql.sh" in str(build_command):
                build_script_path = project_dir / "build_codeql.sh"
                if build_script_path.exists():
                    try:
                        build_script_path.unlink()
                    except Exception:
                        pass
        
        results = []
        for r in raw_results:
            # Try to construct a relative path to the project
            try:
                file_path = Path(r["file"]).relative_to(project_dir.parent)
            except ValueError:
                file_path = Path(r["file"])

            results.append(VulnerabilityResult(
                file_path=file_path,
                line=r["line"],
                column=1,
                rule_id=r["rule_id"],
                message=f"{r['rule_name']}: {r['message']}",
                severity=r["severity"],
            ))
            
        logger.info(f"CodeQL 분석 완료 ({language}): {len(results)}개 발견")
        return results

    except Exception as e:
        logger.exception(f"CodeQL 분석 중 오류 발생 ({language}): {e}")
        return []


def analyze_project(project_dir: Path, languages: Set[str]) -> List[VulnerabilityResult]:
    """
    프로젝트 전체 분석 - 언어별 적절한 SAST 도구 실행
    
    Args:
        project_dir: 프로젝트 디렉토리
        languages: 감지된 언어 집합
    
    Returns:
        모든 취약점 결과 통합 리스트
    """
    all_results = []
    
    # Java는 SpotBugs, C/C++/Python/JS는 CodeQL 사용
    codeql_languages = {"c", "cpp", "python", "javascript"}
    
    for language in languages:
        if language in codeql_languages:
            logger.info(f"{language} 분석 실행 (CodeQL 사용)")
            results = analyze_with_codeql(project_dir, language)
            all_results.extend(results)
        elif language == "java":
            logger.info(f"Java 분석 실행 (SpotBugs 사용)")
            try:
                from sarif_cli.spotbugs_wrapper import SpotBugsWrapper
                
                spotbugs = SpotBugsWrapper()
                
                # SpotBugs는 프로젝트 디렉토리를 받아서 내부에서 컴파일과 분석을 수행
                raw_results = spotbugs.analyze(project_dir)
                
                for r in raw_results:
                    try:
                        file_path = Path(r["file"]).relative_to(project_dir.parent)
                    except ValueError:
                        file_path = Path(r["file"])
                    
                    all_results.append(VulnerabilityResult(
                        file_path=file_path,
                        line=r["line"],
                        column=1,
                        rule_id=r["rule_id"],
                        message=f"{r['rule_name']}: {r['message']}",
                        severity=r["severity"],
                    ))
                
                logger.info(f"SpotBugs 분석 완료: {len(raw_results)}개 발견")
                    
            except Exception as e:
                logger.exception(f"SpotBugs 분석 중 오류 발생: {e}")
        else:
            logger.warning(f"{language}는 현재 지원되지 않습니다.")
    
    return all_results
