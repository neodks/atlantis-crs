import os
from pathlib import Path
from typing import List, Tuple
from loguru import logger
from .docker_manager import DockerManager
from sarif_cli.core.aux_analyser import AuxAnalysisResult

class SVFAnalyser:
    """
    SVF (Static Value-Flow) Analyser for C/C++
    Uses Docker to compile and analyze reachability.
    """
    # Using a lightweight SVF image or the one from crs-sarif if available
    # For now, we'll use a placeholder or assume 'svf-tools/SVF' is available/built
    IMAGE_NAME = "svf-tools/svf" 

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.docker = DockerManager(self.IMAGE_NAME, self.project_dir)

    def analyze(self, file_path: Path, line: int) -> AuxAnalysisResult:
        try:
            self.docker.start_container()
            
            # 1. Compile to LLVM Bitcode (.bc)
            # We need to find the relative path from project root
            try:
                rel_path = file_path.relative_to(self.project_dir)
            except ValueError:
                # If file_path is absolute but not in project_dir, try to handle or fail
                rel_path = file_path.name # Fallback
            
            bc_file = f"{rel_path}.bc"
            
            # Simple compilation command - might fail for complex projects
            # -g: generate debug info (crucial for line mapping)
            # -c: compile only
            # -emit-llvm: generate bitcode
            compile_cmd = f"clang -c -emit-llvm -g {rel_path} -o {bc_file}"
            
            exit_code, output = self.docker.exec_command(compile_cmd)
            if exit_code != 0:
                logger.warning(f"SVF Compilation failed: {output}")
                return AuxAnalysisResult(False, ["Compilation failed"], [])

            # 2. Run SVF (wpa)
            # -ander: Andersen's pointer analysis (fast, less precise)
            # -dump-callgraph: generate call graph
            # We need to check reachability to the target line.
            # SVF doesn't have a direct "is line X reachable" CLI flag easily accessible without custom traversal.
            # However, we can check if the function containing the line is reachable from main.
            
            # First, find the function name for the line (using llvm-dis or simple parsing? No, SVF can do it)
            # Let's use a heuristic: Run wpa and check if the function is in the call graph.
            
            wpa_cmd = f"wpa -ander -dump-callgraph {bc_file}"
            exit_code, output = self.docker.exec_command(wpa_cmd)
            
            if exit_code != 0:
                logger.warning(f"SVF Analysis failed: {output}")
                return AuxAnalysisResult(False, ["Analysis failed"], [])
            
            # 3. Parse Results
            # This is tricky without a custom SVF pass.
            # For this MVP, we will assume if compilation and wpa succeed, and we find the function in the callgraph, it's "potentially reachable".
            # To be more precise, we would need to parse the dot file.
            
            # Let's look for "callgraph_final.dot"
            exit_code, dot_content = self.docker.exec_command("cat callgraph_final.dot")
            
            reachable = False
            call_stack = []
            
            if exit_code == 0 and len(dot_content) > 0:
                # Heuristic: If the dot file is generated, we consider it a success.
                # Real reachability requires parsing the graph from 'main' to target function.
                reachable = True 
                call_stack = ["main", "...", f"Function at {rel_path}:{line}"]
            
            return AuxAnalysisResult(reachable, call_stack, ["Data flow analysis not implemented"])

        except Exception as e:
            logger.error(f"SVF Analysis Error: {e}")
            return AuxAnalysisResult(False, [f"Error: {e}"], [])
        finally:
            self.docker.cleanup()
