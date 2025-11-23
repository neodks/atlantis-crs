"""
Auxiliary Analyser Module
Provides additional static analysis (Reachability, Data Flow) to enhance LLM verification.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict
from loguru import logger

from sarif_cli.config.settings import config

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
        self.enabled = config.ENABLE_AUX
        
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
        
        logger.info(f"Running Aux Analysis for {file_path}:{line} ({self.language})")
        
        try:
            if self.language in ["c", "cpp"]:
                from sarif_cli.core.aux_tools.svf_analyser import SVFAnalyser
                analyser = SVFAnalyser(self.project_dir)
                return analyser.analyze(file_path, line)
            elif self.language == "java":
                from sarif_cli.core.aux_tools.sootup_analyser import SootUpAnalyser
                analyser = SootUpAnalyser(self.project_dir)
                return analyser.analyze(file_path, line)
            else:
                logger.warning(f"Aux analysis not supported for language: {self.language}")
                return AuxAnalysisResult(False, ["Not supported"], [])
                
        except Exception as e:
            logger.error(f"Aux analysis failed: {e}")
            return AuxAnalysisResult(
                reachable=False,
                call_stack=[f"Error: {e}"],
                data_flow=[]
            )
