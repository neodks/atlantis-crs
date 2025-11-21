"""
Joern 래퍼 - 기존 crs-sarif의 JoernServer 재사용 (직접 joern-parse 사용)
"""
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger
import tempfile
import shutil
import subprocess

def ensure_joern_installed() -> bool:
    """joern-parse와 joern 실행 파일이 PATH에 있는지 확인"""
    for cmd in ("joern-parse", "joern"):
        if shutil.which(cmd):
            return True
    logger.error(
        "Joern이 설치되지 않았습니다. https://joern.io/ 에서 설치 후 PATH에 추가하세요."
    )
    return False


class JoernAnalyzer:
    """Joern을 사용한 C/C++ 취약점 분석"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.cpg_path = None
        self.server = None
    
    def build_cpg(self) -> Path:
        """
        Code Property Graph (CPG) 생성
        
        Returns:
            CPG 파일 경로
        """
        logger.info(f"Building CPG for {self.project_dir}")
        
        try:
            # Joern이 설치돼 있는지 확인
            if not ensure_joern_installed():
                return None
            
            # 임시 작업 디렉토리 생성
            work_dir = Path(tempfile.mkdtemp(prefix="joern_"))
            cpg_file = work_dir / "cpg.bin"
            
            # joern-parse 실행
            cmd = [
                "joern-parse",
                str(self.project_dir),
                "--output",
                str(cpg_file),
            ]
            # joern-parse 실행 및 CPG 생성
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode != 0:
                logger.error(f"joern-parse 실패: {result.stderr.strip()}")
                return None
            if not cpg_file.exists():
                logger.error("CPG 파일이 생성되지 않았습니다.")
                return None
            logger.info(f"CPG 생성 완료: {cpg_file}")
            self.cpg_path = cpg_file
            return self.cpg_path
                
        except ImportError as e:
            logger.warning(f"sarif.static.joern을 import할 수 없습니다: {e}")
            return None
        except Exception as e:
            logger.error(f"CPG 생성 중 오류: {e}")
            return None
    
    def start_server(self) -> bool:
        """
        Joern 서버 시작
        
        Returns:
            서버 시작 성공 여부
        """
        if not self.cpg_path:
            logger.warning("CPG가 없어 서버를 시작할 수 없습니다.")
            return False
        
        # JoernServer 사용을 포기하고 직접 joern CLI를 사용합니다.
        # CPG가 이미 생성되어 있으면 바로 True 반환
        if self.cpg_path:
            logger.info("Joern 서버 대신 직접 joern CLI를 사용합니다.")
            return True
        logger.warning("CPG가 없어서 Joern을 사용할 수 없습니다.")
        return False
    
    def query_vulnerabilities(self) -> List[Dict[str, Any]]:
        """
        Joern 쿼리를 사용하여 취약점 탐지
        
        Returns:
            취약점 정보 리스트
        """
        # 직접 joern CLI를 사용해 쿼리를 실행합니다.
        if not self.cpg_path:
            logger.warning("CPG가 없어서 쿼리를 실행할 수 없습니다.")
            return []

        import json, tempfile
        vulnerabilities = []

        # 쿼리 정의 (same as before)
        buffer_overflow_query = """
        cpg.call.name("(strcpy|memcpy|sprintf|gets).*\\").l.map { c =>
          Map(
            "function" -> c.name,
            "file" -> c.file.name.headOption.getOrElse("unknown"),
            "line" -> c.lineNumber.headOption.getOrElse(0),
            "code" -> c.code
          )
        }.toJson
        """
        uaf_query = """
        cpg.call.name("free").l.map { c =>
          Map(
            "function" -> "free",
            "file" -> c.file.name.headOption.getOrElse("unknown"),
            "line" -> c.lineNumber.headOption.getOrElse(0),
            "code" -> c.code
          )
        }.toJson
        """
        null_deref_query = """
        cpg.call.name(".*").where(_.argument.code("NULL")).l.map { c =>
          Map(
            "function" -> c.name,
            "file" -> c.file.name.headOption.getOrElse("unknown"),
            "line" -> c.lineNumber.headOption.getOrElse(0),
            "code" -> c.code
          )
        }.toJson
        """
        queries = [
            ("CWE-119", "Buffer Overflow", buffer_overflow_query),
            ("CWE-416", "Use After Free", uaf_query),
            ("CWE-476", "NULL Pointer Dereference", null_deref_query),
        ]

        # Execute each query via joern CLI with quiet flag
        for rule_id, rule_name, query in queries:
            try:
                # Write query to temporary file
                with tempfile.NamedTemporaryFile('w', delete=False, suffix='.sc') as f:
                    f.write(query)
                    query_file = f.name
                # Run joern CLI
                cmd = [
                    "joern",
                    "--script", query_file,
                    "--cpg", str(self.cpg_path)
                ]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                # Clean up temp file
                try:
                    Path(query_file).unlink()
                except Exception:
                    pass
                if result.returncode != 0:
                    logger.warning(f"{rule_name} 쿼리 실행 실패: {result.stderr.strip()}")
                    continue
                stdout = result.stdout.strip()
                if not stdout:
                    logger.warning(f"{rule_name} 쿼리 결과가 비어 있습니다.")
                    continue
                # Parse possible multiple JSON objects
                responses = []
                for line in stdout.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    # Skip lines that are not JSON (e.g., Joern log messages)
                    if not (line.startswith('{') or line.startswith('[')):
                        logger.debug(f"Skipping non-JSON line: {line}")
                        continue
                    try:
                        data = json.loads(line)
                        responses.append(data)
                    except json.JSONDecodeError:
                        logger.debug(f"JSON 파싱 실패 (무시): {line}")
                aggregated = []
                for data in responses:
                    if isinstance(data, dict) and "response" in data:
                        aggregated.extend(data["response"])
                logger.info(f"{rule_name}: {len(aggregated)}개 발견")
                for item in aggregated:
                    if isinstance(item, dict):
                        vulnerabilities.append({
                            "rule_id": rule_id,
                            "rule_name": rule_name,
                            "file": item.get("file", "unknown"),
                            "line": item.get("line", 0),
                            "function": item.get("function", "unknown"),
                            "code": item.get("code", ""),
                        })
            except Exception as e:
                logger.warning(f"{rule_name} 쿼리 실행 중 오류: {e}")
                continue
        return vulnerabilities
    
    def stop_server(self):
        """현재 구현에서는 별도 서버가 없으므로 아무 작업도 하지 않음"""
    
    def __del__(self):
        """소멸자 - 현재는 noop"""
        self.stop_server()
