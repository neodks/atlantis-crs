"""
Auxiliary Analyser Module
Provides additional static analysis (Reachability, Data Flow) to enhance LLM verification.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict
from loguru import logger

from sarif_cli import settings

@dataclass
class AuxAnalysisResult:
    reachable: bool
    call_stack: List[str]
    data_flow: List[str]
    
    def __str__(self):
        return f"Reachable: {self.reachable}, Stack: {len(self.call_stack)} frames"

class AuxAnalyser:
    """
    Auxiliary Analyser that wraps heavy static analysis tools (SVF, SootUp).
    Currently implements a lightweight/mock version for demonstration.
    """
    
    def __init__(self, project_dir: Path, language: str):
        self.project_dir = project_dir
        self.language = language
        self.enabled = settings.ENABLE_AUX_ANALYSIS
        
    def analyze_reachability(self, file_path: Path, line: int) -> AuxAnalysisResult:
        """
        Analyze reachability of a specific line in a file.
        """
        if not self.enabled:
            return AuxAnalysisResult(
                reachable=False, 
                call_stack=["Aux analysis disabled"], 
                data_flow=["No data"]
            )
            
        logger.info(f"Running Aux Analysis for {file_path}:{line} ({self.language})")
        
        # TODO: Implement actual integration with SVF/SootUp
        # For now, we perform a simple heuristic check or return a placeholder
        
        # Placeholder logic:
        # If the file contains "main" or "handler", we assume it's reachable.
        try:
            content = file_path.read_text(errors='ignore')
            lines = content.splitlines()
            
            if 0 <= line - 1 < len(lines):
                target_line = lines[line - 1]
            else:
                target_line = "unknown"
                
            reachable = False
            call_stack = []
            data_flow = []
            
            # Simple heuristic for demonstration
            if "main" in content or "def " in content or "public " in content:
                reachable = True
                call_stack = ["main()", "process_request()", target_line.strip()]
                data_flow = ["user_input -> request_body -> target_var"]
            else:
                reachable = False
                call_stack = ["No path found"]
                data_flow = ["No data flow"]
                
            return AuxAnalysisResult(
                reachable=reachable,
                call_stack=call_stack,
                data_flow=data_flow
            )
            
        except Exception as e:
            logger.error(f"Aux analysis failed: {e}")
            return AuxAnalysisResult(
                reachable=False,
                call_stack=[f"Error: {e}"],
                data_flow=[]
            )
