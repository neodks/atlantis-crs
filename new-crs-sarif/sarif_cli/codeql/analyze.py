import json
import os
from pathlib import Path
from typing import Literal

from loguru import logger

from .common import run, temporary_dir
from .database import Database


def run_codeql_analysis(
    db: Database,
    run_name: str,
    language: Literal["c", "java"],
    output: Path | None = None,
    split_results: bool = False,
    extended: bool = False,
) -> None:
    # Create temporary directory for analysis results
    if output is None:
        output = temporary_dir() / f"{run_name}.sarif"

    nproc = os.cpu_count()

    # Run CodeQL analysis based on language
    if language == "c":
        run(
            [
                "database",
                "analyze",
                str(db.path),
                "--format=sarif-latest",
                "--threads=" + str(int(nproc / 2)),
                "--output",
                str(output),
                "--sarif-category=cpp",
                # 다운로드된 쿼리 팩 사용
                "codeql/cpp-queries:codeql-suites/cpp-security-and-quality.qls",
            ],
        )
    elif language == "java":
        run(
            [
                "database",
                "analyze",
                str(db.path),
                "--format=sarif-latest",
                "--threads=" + str(int(nproc / 2)),
                "--output",
                str(output),
                "--sarif-category=java",
                # 다운로드된 쿼리 팩 사용
                "codeql/java-queries:codeql-suites/java-security-and-quality.qls",
            ],
        )
    elif language == "python":
        run(
            [
                "database",
                "analyze",
                str(db.path),
                "--format=sarif-latest",
                "--threads=" + str(int(nproc / 2)),
                "--output",
                str(output),
                "--sarif-category=python",
                "codeql/python-queries:codeql-suites/python-security-and-quality.qls",
            ],
        )
    elif language == "javascript":
        run(
            [
                "database",
                "analyze",
                str(db.path),
                "--format=sarif-latest",
                "--threads=" + str(int(nproc / 2)),
                "--output",
                str(output),
                "--sarif-category=javascript",
                "codeql/javascript-queries:codeql-suites/javascript-security-and-quality.qls",
            ],
        )
