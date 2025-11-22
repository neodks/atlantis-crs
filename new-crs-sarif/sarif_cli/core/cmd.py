import subprocess
import sys
from abc import ABC
from typing import NamedTuple
from loguru import logger


class ProcessRunRet(NamedTuple):
    returncode: int
    stdout: str
    stderr: str


class BaseCommander(ABC):
    def __init__(self, quiet=False):
        self.quiet = quiet

    def run(
        self,
        cmd: str | list[str],
        input: str | None = None,
        cwd: str | None = None,
        pipe: bool = False,
        quiet: bool = False,
        timeout: int | None = None,
        stdout_file: str | None = None,
        stderr_file: str | None = None,
    ) -> ProcessRunRet:
        if isinstance(cmd, list):
            cmd = " ".join(cmd)

        if not quiet:
            logger.debug(f"Running command: {cmd}")

        try:
            if quiet:
                result = subprocess.run(
                    cmd,
                    input=input,
                    shell=True,
                    cwd=cwd,
                    check=True,
                    text=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=timeout,
                )
            elif not pipe:
                result = subprocess.run(
                    cmd,
                    input=input,
                    shell=True,
                    cwd=cwd,
                    check=True,
                    text=True,
                    stdout=sys.stdout,
                    stderr=sys.stderr,
                    timeout=timeout,
                )
            else:
                result = subprocess.run(
                    cmd,
                    input=input,
                    shell=True,
                    cwd=cwd,
                    check=True,
                    text=True,
                    capture_output=True,
                    timeout=timeout,
                )

            return ProcessRunRet(result.returncode, result.stdout, result.stderr)

        except subprocess.CalledProcessError as e:
            logger.error(
                f"Error occurred while running CMD: {cmd} at {cwd}. Error: {e}"
            )

            return ProcessRunRet(e.returncode, e.stdout, e.stderr)

        except subprocess.TimeoutExpired as e:
            logger.error(f"Timeout occurred while running CMD: {cmd} at {cwd}")
            logger.error(e)

            return ProcessRunRet(-1, e.stdout, e.stderr)

        finally:
            if stdout_file and result.stdout:
                with open(stdout_file, "a") as f:
                    f.write(result.stdout)
            if stderr_file and result.stderr:
                with open(stderr_file, "a") as f:
                    f.write(result.stderr)
