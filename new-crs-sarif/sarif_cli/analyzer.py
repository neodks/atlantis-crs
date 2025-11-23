"""
SAST 분석 실행 모듈 - 다양한 SAST 도구 통합
"""
from pathlib import Path
from typing import Set, List, Dict, Any
from loguru import logger

from sarif_cli.core.detector import get_files_by_language
from sarif_cli.models.vulnerability import VulnerabilityResult


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
        from sarif_cli.wrappers.codeql.wrapper import CodeQLWrapper
        
        codeql_wrapper = CodeQLWrapper()
        
        # TODO: This is a temporary solution for simple projects.
        # A more robust solution should detect the build system (e.g., make, maven, gradle).
        build_command = None
        if language == "java":
            java_files = list(project_dir.rglob("*.java"))
            if java_files:
                # Use find command to compile all Java files
                build_command = 'find . -name "*.java" -exec javac {} +'
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
                tool_name=r.get("tool_name", "CodeQL"),
                tool_metadata=r.get("tool_metadata", {}),
            ))
            
        logger.info(f"CodeQL 분석 완료 ({language}): {len(results)}개 발견")
        return results

    except Exception as e:
        logger.exception(f"CodeQL 분석 중 오류 발생 ({language}): {e}")
        return []


def analyze_with_joern(project_dir: Path, language: str) -> List[VulnerabilityResult]:
    """
    Joern을 사용하여 C/C++ 코드 분석
    
    Args:
        project_dir: 프로젝트 디렉토리
        language: 분석할 언어 ("c" 또는 "cpp")
    
    Returns:
        취약점 결과 리스트
    """
    logger.info(f"Joern 분석 시작 ({language})")
    
    try:
        from sarif_cli.wrappers.joern_wrapper import JoernAnalyzer
        
        analyzer = JoernAnalyzer(project_dir)
        
        # CPG 빌드
        cpg_path = analyzer.build_cpg()
        if not cpg_path:
            logger.warning("CPG 생성 실패. Joern 분석을 건너뜁니다.")
            return []
        
        # 서버 시작 (실제로는 CPG 존재 확인)
        if not analyzer.start_server():
            logger.warning("Joern 서버 시작 실패. Joern 분석을 건너뜁니다.")
            return []
        
        # 취약점 쿼리 실행
        raw_results = analyzer.query_vulnerabilities()
        
        # VulnerabilityResult로 변환
        results = []
        for r in raw_results:
            try:
                file_path = Path(r["file"]).relative_to(project_dir.parent)
            except ValueError:
                file_path = Path(r["file"])
            
            results.append(VulnerabilityResult(
                file_path=file_path,
                line=r["line"],
                column=1,
                rule_id=r["rule_id"],
                message=f"{r['rule_name']}: {r.get('code', '')}",
                severity="warning",
                tool_name=r.get("tool_name", "Joern"),
                tool_metadata=r.get("tool_metadata", {}),
            ))
        
        logger.info(f"Joern 분석 완료 ({language}): {len(results)}개 발견")
        return results
        
    except ImportError:
        logger.warning("Joern wrapper를 찾을 수 없습니다. Joern 분석을 건너뜁니다.")
        return []
    except Exception as e:
        logger.exception(f"Joern 분석 중 오류 발생 ({language}): {e}")
        return []


def analyze_with_spotbugs(project_dir: Path) -> List[VulnerabilityResult]:
    """
    SpotBugs를 사용하여 Java 코드 분석
    
    Args:
        project_dir: 프로젝트 디렉토리
    
    Returns:
        취약점 결과 리스트
    """
    logger.info("SpotBugs 분석 시작")
    
    try:
        from sarif_cli.wrappers.spotbugs_wrapper import SpotBugsWrapper
        
        spotbugs = SpotBugsWrapper()
        
        # SpotBugs 설치 확인
        if not spotbugs.ensure_spotbugs_installed():
            logger.warning("SpotBugs가 설치되지 않았습니다. SpotBugs 분석을 건너뜁니다.")
            return []
        
        # 분석 실행
        raw_results = spotbugs.analyze(project_dir)
        
        # VulnerabilityResult로 변환
        results = []
        for r in raw_results:
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
                tool_name=r.get("tool_name", "SpotBugs"),
                tool_metadata=r.get("tool_metadata", {}),
            ))
        
        logger.info(f"SpotBugs 분석 완료: {len(results)}개 발견")
        return results
        
    except ImportError:
        logger.warning("SpotBugs wrapper를 찾을 수 없습니다. SpotBugs 분석을 건너뜁니다.")
        return []
    except Exception as e:
        logger.exception(f"SpotBugs 분석 중 오류 발생: {e}")
        return []


def analyze_with_bandit(project_dir: Path) -> List[VulnerabilityResult]:
    """
    Bandit을 사용하여 Python 코드 분석
    
    Args:
        project_dir: 프로젝트 디렉토리
    
    Returns:
        취약점 결과 리스트
    """
    logger.info("Bandit 분석 시작")
    
    try:
        from sarif_cli.wrappers.bandit_wrapper import BanditAnalyzer
        
        analyzer = BanditAnalyzer()
        
        # 분석 실행
        raw_results = analyzer.analyze(project_dir)
        
        # VulnerabilityResult로 변환
        results = []
        for r in raw_results:
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
                tool_name=r.get("tool_name", "Bandit"),
                tool_metadata=r.get("tool_metadata", {}),
            ))
        
        logger.info(f"Bandit 분석 완료: {len(results)}개 발견")
        return results
        
    except ImportError:
        logger.warning("Bandit wrapper를 찾을 수 없습니다. Bandit 분석을 건너뜁니다.")
        return []
    except Exception as e:
        logger.exception(f"Bandit 분석 중 오류 발생: {e}")
        return []


def analyze_with_semgrep(project_dir: Path, language: str) -> List[VulnerabilityResult]:
    """
    Semgrep을 사용하여 코드 분석 (경량화된 SARIF 파싱)
    
    Args:
        project_dir: 프로젝트 디렉토리
        language: 분석할 언어
    
    Returns:
        취약점 결과 리스트
    """
    logger.info(f"Semgrep 분석 시작 ({language})")
    
    try:
        from sarif_cli.wrappers.semgrep_wrapper import SemgrepAnalyzer
        
        analyzer = SemgrepAnalyzer()
        
        # 분석 실행 (경량화된 결과 반환)
        raw_results = analyzer.analyze(project_dir, language)
        
        # VulnerabilityResult로 변환
        results = []
        for r in raw_results:
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
                tool_name=r.get("tool_name", "Semgrep"),
                tool_metadata=r.get("tool_metadata", {}),
            ))
        
        logger.info(f"Semgrep 분석 완료 ({language}): {len(results)}개 발견")
        return results
        
    except ImportError:
        logger.warning("Semgrep wrapper를 찾을 수 없습니다. Semgrep 분석을 건너뜁니다.")
        return []
    except Exception as e:
        logger.exception(f"Semgrep 분석 중 오류 발생 ({language}): {e}")
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
    
    # C/C++/Java/Python/JS는 CodeQL 사용
    codeql_languages = {"c", "cpp", "java", "python", "javascript"}
    
    for language in languages:
        if language in codeql_languages:
            logger.info(f"{language} 분석 실행 (CodeQL 사용)")
            results = analyze_with_codeql(project_dir, language)
            all_results.extend(results)
            
            # C/C++인 경우 Joern도 추가로 실행
            if language in ["c", "cpp"]:
                logger.info(f"{language} 분석 실행 (Joern 사용)")
                joern_results = analyze_with_joern(project_dir, language)
                all_results.extend(joern_results)
            
            # Java인 경우 SpotBugs도 추가로 실행
            if language == "java":
                logger.info(f"{language} 분석 실행 (SpotBugs 사용)")
                spotbugs_results = analyze_with_spotbugs(project_dir)
                all_results.extend(spotbugs_results)
            
            # Python인 경우 Bandit도 추가로 실행
            if language == "python":
                logger.info(f"{language} 분석 실행 (Bandit 사용)")
                bandit_results = analyze_with_bandit(project_dir)
                all_results.extend(bandit_results)
            
            # 모든 언어에 대해 Semgrep도 추가로 실행 (경량 파서 사용)
            logger.info(f"{language} 분석 실행 (Semgrep 사용)")
            semgrep_results = analyze_with_semgrep(project_dir, language)
            all_results.extend(semgrep_results)
        else:
            logger.warning(f"지원하지 않는 언어: {language}")
    
    logger.info(f"총 {len(all_results)}개의 취약점 발견")
    return all_results
