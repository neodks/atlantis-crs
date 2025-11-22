import docker
from docker.errors import ImageNotFound
from loguru import logger
from pathlib import Path
from typing import Optional, Tuple

class DockerManager:
    """
    Simplified Docker Manager for running Aux tools
    """
    def __init__(self, image_name: str, work_dir: Path):
        self.client = docker.from_env()
        self.image_name = image_name
        self.work_dir = work_dir.resolve()
        self.container = None

    def ensure_image(self):
        try:
            self.client.images.get(self.image_name)
            logger.debug(f"Image {self.image_name} exists")
        except ImageNotFound:
            logger.warning(f"Image {self.image_name} not found. Attempting to pull...")
            try:
                self.client.images.pull(self.image_name)
            except Exception as e:
                logger.error(f"Failed to pull image {self.image_name}: {e}")
                raise

    def start_container(self, env: Optional[dict] = None):
        self.ensure_image()
        
        # Mount work_dir to /src
        volumes = {
            str(self.work_dir): {'bind': '/src', 'mode': 'rw'}
        }
        
        try:
            self.container = self.client.containers.run(
                self.image_name,
                command="/bin/bash",
                detach=True,
                tty=True,
                volumes=volumes,
                environment=env or {},
                working_dir="/src"
            )
            logger.debug(f"Container started: {self.container.id}")
        except Exception as e:
            logger.error(f"Failed to start container: {e}")
            raise

    def exec_command(self, cmd: str) -> Tuple[int, str]:
        if not self.container:
            raise RuntimeError("Container not started")
            
        logger.debug(f"Exec: {cmd}")
        try:
            exit_code, output = self.container.exec_run(f"bash -c '{cmd}'")
            return exit_code, output.decode('utf-8', errors='replace')
        except Exception as e:
            logger.error(f"Exec failed: {e}")
            return -1, str(e)

    def cleanup(self):
        if self.container:
            try:
                self.container.stop()
                self.container.remove()
                logger.debug("Container removed")
            except Exception as e:
                logger.warning(f"Failed to remove container: {e}")
            finally:
                self.container = None
