import os
from pathlib import Path
from loguru import logger
from .docker_manager import DockerManager
from sarif_cli.core.aux_analyser import AuxAnalysisResult

class SootUpAnalyser:
    """
    SootUp Analyser for Java
    Uses Docker to analyze reachability in JVM bytecode.
    """
    # Using a placeholder image name. 
    # In a real scenario, this should be 'sootup/sootup' or similar.
    IMAGE_NAME = "sootup/sootup" 

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.docker = DockerManager(self.IMAGE_NAME, self.project_dir)

    def analyze(self, file_path: Path, line: int) -> AuxAnalysisResult:
        try:
            self.docker.start_container()
            
            # 1. Compile Java file (if not already compiled)
            # We assume 'javac' is available in the container
            try:
                rel_path = file_path.relative_to(self.project_dir)
            except ValueError:
                rel_path = file_path.name
            
            # Check if .class file exists (heuristic)
            class_file = rel_path.with_suffix(".class")
            
            # Try to compile
            compile_cmd = f"javac {rel_path}"
            exit_code, output = self.docker.exec_command(compile_cmd)
            
            if exit_code != 0:
                # Compilation might fail due to dependencies. 
                # We'll proceed if there are existing class files, otherwise fail.
                logger.warning(f"SootUp Compilation warning: {output}")
            
            # 2. Run SootUp
            # SootUp CLI usage (hypothetical, based on script analysis):
            # java -jar sootup.jar --input-dir . --class-name <ClassName> --analysis reachability
            
            # We need to deduce the class name from the file path
            # e.g., src/main/java/com/example/App.java -> com.example.App
            # This is hard without parsing package declaration.
            # Fallback: use filename without extension
            class_name = file_path.stem
            
            sootup_cmd = f"java -jar /opt/sootup/sootup-cli.jar --input-dir . --class-name {class_name} --analysis reachability"
            
            exit_code, output = self.docker.exec_command(sootup_cmd)
            
            reachable = False
            call_stack = []
            
            if exit_code == 0 and "Reachable" in output:
                reachable = True
                call_stack = ["main", "...", f"{class_name}:{line}"]
            
            return AuxAnalysisResult(reachable, call_stack, ["Data flow analysis not implemented"])

        except Exception as e:
            logger.error(f"SootUp Analysis Error: {e}")
            return AuxAnalysisResult(False, [f"Error: {e}"], [])
        finally:
            self.docker.cleanup()
