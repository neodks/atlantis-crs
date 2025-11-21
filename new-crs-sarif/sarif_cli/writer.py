"""
SARIF 출력 모듈 - 분석 결과를 SARIF 2.1.0 형식으로 저장
"""
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from loguru import logger

from sarif_cli.analyzer import VulnerabilityResult


def create_sarif_report(
    vulnerabilities: List[VulnerabilityResult],
    file_path: Path,
    patches: Dict[int, Any] = None
) -> dict:
    """
    단일 파일에 대한 SARIF 리포트 생성
    
    Args:
        vulnerabilities: 해당 파일의 취약점 리스트
        file_path: 대상 파일 경로
        patches: 취약점 ID별 패치 정보 (선택)
    
    Returns:
        SARIF 2.1.0 형식 딕셔너리
    """
    results = []
    patches = patches or {}
    
    for idx, vuln in enumerate(vulnerabilities):
        result = {
            "ruleId": vuln.rule_id,
            "level": vuln.severity,
            "message": {
                "text": vuln.message
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": str(vuln.file_path)
                        },
                        "region": {
                            "startLine": vuln.line,
                            "startColumn": vuln.column
                        }
                    }
                }
            ]
        }
        
        # LLM 패치가 있으면 fixes 추가
        if idx in patches and patches[idx]:
            patch_info = patches[idx]
            if patch_info.patch_code:
                result["fixes"] = [
                    {
                        "description": {
                            "text": f"{patch_info.explanation} (confidence: {patch_info.confidence:.2f})"
                        },
                        "artifactChanges": [
                            {
                                "artifactLocation": {
                                    "uri": str(vuln.file_path)
                                },
                                "replacements": [
                                    {
                                        "deletedRegion": {
                                            "startLine": vuln.line,
                                            "startColumn": 1
                                        },
                                        "insertedContent": {
                                            "text": patch_info.patch_code
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
        
        results.append(result)
    
    sarif = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "SARIF-CLI",
                        "version": "0.1.0",
                        "informationUri": "https://github.com/your-org/sarif-cli"
                    }
                },
                "results": results,
                "invocations": [
                    {
                        "executionSuccessful": True,
                        "endTimeUtc": datetime.utcnow().isoformat() + "Z"
                    }
                ]
            }
        ]
    }
    
    return sarif


def write_sarif_results(
    vulnerabilities: List[VulnerabilityResult],
    output_dir: Path
) -> List[Path]:
    """
    취약점 결과를 파일별로 SARIF 파일로 저장
    
    Args:
        vulnerabilities: 모든 취약점 결과
        output_dir: 출력 디렉토리
    
    Returns:
        생성된 SARIF 파일 경로 리스트
    """
    return write_sarif_results_with_patches(vulnerabilities, output_dir, {})


def write_sarif_results_with_patches(
    vulnerabilities: List[VulnerabilityResult],
    output_dir: Path,
    patches_map: Dict[int, Any]
) -> List[Path]:
    """
    취약점 결과와 패치를 파일별로 SARIF 파일로 저장
    
    Args:
        vulnerabilities: 모든 취약점 결과
        output_dir: 출력 디렉토리
        patches_map: 취약점 인덱스별 패치 정보
    
    Returns:
        생성된 SARIF 파일 경로 리스트
    """
    # 파일별로 취약점 그룹화
    file_groups = {}
    vuln_indices = {}  # 파일별 취약점의 원래 인덱스 추적
    
    for idx, vuln in enumerate(vulnerabilities):
        file_key = vuln.file_path
        if file_key not in file_groups:
            file_groups[file_key] = []
            vuln_indices[file_key] = []
        file_groups[file_key].append(vuln)
        vuln_indices[file_key].append(idx)
    
    sarif_files = []
    
    # 파일별 SARIF 생성
    for file_path, vulns in file_groups.items():
        sarif_filename = f"{file_path.name}.sarif"
        sarif_path = output_dir / sarif_filename
        
        # 해당 파일의 취약점에 대한 패치만 추출
        file_patches = {}
        for local_idx, global_idx in enumerate(vuln_indices[file_path]):
            if global_idx in patches_map:
                file_patches[local_idx] = patches_map[global_idx]
        
        sarif_report = create_sarif_report(vulns, file_path, file_patches)
        
        with open(sarif_path, "w", encoding="utf-8") as f:
            json.dump(sarif_report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"SARIF 파일 생성: {sarif_path}")
        sarif_files.append(sarif_path)
    
    return sarif_files
