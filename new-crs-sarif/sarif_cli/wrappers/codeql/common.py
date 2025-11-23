import os
import subprocess
import tempfile
import uuid
from pathlib import Path

from loguru import logger

from sarif_cli.core.cmd import BaseCommander

# Configuration
def _find_codeql_path():
    """CodeQL 실행 파일 경로를 찾습니다."""
    import shutil
    from pathlib import Path
    
    # 1. PATH에서 찾기
    codeql_in_path = shutil.which("codeql")
    if codeql_in_path:
        return codeql_in_path
    
    # 2. 일반적인 설치 위치에서 찾기
    possible_locations = [
        Path.home() / "codeql-cli" / "codeql" / "codeql",
        Path.home() / "bin" / "codeql" / "codeql",
        Path("/usr/local/bin/codeql"),
        Path("/opt/codeql/codeql"),
    ]
    
    for location in possible_locations:
        if location.exists() and location.is_file():
            return str(location)
    
    # 찾지 못한 경우 기본값 반환 (에러는 나중에 발생)
    return "codeql"

codeql_path = _find_codeql_path()
library_path = None


def temporary_root(tmp_root: Path | None = None) -> Path:
    if tmp_root is None:
        tmp_root = tempfile.TemporaryDirectory(prefix="codeql_")

    tmp_root = Path(tmp_root.name)

    if not tmp_root.exists():
        tmp_root.mkdir(parents=True, exist_ok=True)

    return tmp_root


def temporary_path(prefix, suffix) -> Path:
    name = ""

    if prefix:
        name += prefix

    name += uuid.uuid4().hex

    if suffix:
        name += suffix

    return temporary_root() / name


def temporary_dir(create=True, prefix=None, suffix=None) -> Path:
    path = temporary_path(prefix, suffix)

    if create:
        path.mkdir(parents=True, exist_ok=True)

    return path


def temporary_file(create=True, prefix=None, suffix=None) -> Path:
    path = temporary_path(prefix, suffix)

    if create:
        # Create the file using touch like command in pathlib
        path.touch()

    return path


def run(args, *, container_id: str | None = None, timeout: int | None = None):
    command = [codeql_path] + list(map(str, args))

    if container_id:
        logger.warning("Docker execution is not supported in this version. Running locally.")
        
    runner = BaseCommander()
    # 기본적으로 출력을 억제 (quiet=True)
    res = runner.run(command, timeout=timeout, quiet=True)

    if res.returncode != 0:
        if res.returncode == -1:
            raise subprocess.TimeoutExpired(
                f"Command {' '.join(command)} timed out after {timeout} seconds"
            )
        else:
            raise RuntimeError(
                f"Command {' '.join(command)} failed with return code {res.returncode}"
            )

    return res


