import os
import shutil
from pathlib import Path
from typing import List, Literal

from .common import run, temporary_dir
from .query import Query

CODEQL_QLPACK = """
name: aixcc-codeql
version: 0.0.0
libraryPathDependencies: {}
"""

from loguru import logger


class Database(object):
    def __init__(self, path: Path, temp: bool = False):
        self._check_codeql_db(path)

        self.path = path
        self.temp = temp

    def __del__(self):
        if getattr(self, 'temp', False):
            shutil.rmtree(self.path)

    def run_command(self, command: str, options: List = [], post: List = []):
        run(["database", command] + options + [self.path] + post)

    @staticmethod
    def from_cpp(code, command: List | None = None):
        compilers = ["cxx", "clang++", "g++", "cc", "clang", "gcc"]

        if command is None:
            for compiler in compilers:
                if shutil.which(compiler) is not None:
                    command = [compiler, "-c"]
                    break

        directory = temporary_dir()

        fpath = os.path.join(directory, "source.cpp")
        with open(fpath, "w") as f:
            f.write(code)

        command.append(fpath)

        return Database.create("c", directory, command)

    def query(self, ql: str, language: Literal["cpp", "java"] = "cpp"):
        if not hasattr(self, "qldir"):
            self.qldir = temporary_dir()

            qlpack_path = os.path.join(self.qldir, "qlpack.yml")
            with open(qlpack_path, "w") as f:
                qlpack_text = CODEQL_QLPACK.format(
                    "codeql-cpp" if language == "cpp" else "codeql-java"
                )
                f.write(qlpack_text)

        query_path = os.path.join(self.qldir, "query.ql")

        with open(query_path, "w") as f:
            f.write(ql)

        query = Query(query_path)
        bqrs = query.run(database=self)

        return bqrs.parse()

    @staticmethod
    def _check_codeql_db(path: Path):
        if not path.exists():
            raise FileNotFoundError(f"Database not found at {path}")

        if not path.is_dir():
            raise ValueError(f"Database is not a directory: {path}")

        if not any(
            path.joinpath(f"db-{lang}").exists()
            for lang in ["java", "cpp", "c", "python", "javascript"]
        ):
            raise ValueError(f"Database is not a CodeQL database: {path}")

        return True

    @staticmethod
    def create(
        language: Literal["cpp", "java", "c", "python", "javascript"],
        db_path: Path,
        src_path: Path,
        command: list | str | None = None,
    ) -> "Database":
        if language == "c":
            language = "cpp"

        if db_path.exists():
            logger.warning(f"Database already exists at {db_path}, using existing db")
            return Database(db_path)

        if not db_path.parent.exists():
            db_path.parent.mkdir(parents=True, exist_ok=True)

        args = [
            "database",
            "create",
            db_path.as_posix(),
            "-s",
            src_path.as_posix(),
            "--threads",
            os.getenv("CODEQL_THREADS", "4"),
            "--verbose",
        ]

        if isinstance(language, list):
            args += ["-l", ",".join(language), "--db-cluster"]
        else:
            args += ["-l", language]

        if command is not None:
            if isinstance(command, list):
                command = " ".join(command)
            args += ["-c", f'"{command}"']

        try:
            run(args)
        except Exception as e:
            logger.error(f"Error creating database: {e}")

            # Remove the database if it exists
            if db_path.exists():
                shutil.rmtree(db_path, ignore_errors=True)

            raise e

        return Database(db_path)

    def analyze(self, queries: list | str, format: str, output: str):
        if type(queries) is not list:
            queries = [queries]

        options = [f"--format={format}", "-o", output]
        # options += ["--search-path", search_path]

        self.run_command("analyze", options, post=queries)

    def upgrade(self):
        self.run_command("upgrade")

    def cleanup(self):
        self.run_command("cleanup")

    def bundle(self, output: str):
        options = ["-o", output]
        self.run_command("bundle", options)
