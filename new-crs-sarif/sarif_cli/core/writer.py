"""
SARIF 출력 모듈 - 분석 결과를 SARIF 2.1.0 형식으로 저장
"""
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from loguru import logger

from sarif_cli.analyzer import VulnerabilityResult


def create_sarif_run(
    tool_name: str,
    tool_metadata: Dict[str, Any],
    vulnerabilities: List[VulnerabilityResult],
    vuln_to_patch: Dict[Any, Any] = None
) -> dict:
    """
    단일 도구에 대한 SARIF run 객체 생성
    """
    results = []
    vuln_to_patch = vuln_to_patch or {}
    
    # tool_metadata가 비어있으면 기본값 설정
    driver = tool_metadata.get("driver", {})
    if not driver:
        driver = {
            "name": tool_name,
            "version": "0.1.0",
            "informationUri": "https://github.com/your-org/sarif-cli"
        }
    
    # tool 객체 구성
    tool = tool_metadata if tool_metadata else {"driver": driver}
    
    for vuln in vulnerabilities:
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
        
        # 패치 정보 추가
        if vuln in vuln_to_patch:
            patch_info = vuln_to_patch[vuln]
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
        
        # Aux 분석 결과 추가
        if vuln.aux_result:
            result["properties"] = result.get("properties", {})
            result["properties"]["aux_analysis"] = vuln.aux_result

        results.append(result)
    
    run = {
        "tool": tool,
        "results": results,
        "invocations": [
            {
                "executionSuccessful": True,
                "endTimeUtc": datetime.utcnow().isoformat() + "Z"
            }
        ]
    }
    
    return run


def write_sarif_results(
    vulnerabilities: List[VulnerabilityResult],
    output_dir: Path
) -> List[Path]:
    """
    취약점 결과를 SARIF 파일로 저장
    """
    return write_sarif_results_with_patches(vulnerabilities, output_dir, {})


def write_sarif_results_with_patches(
    vulnerabilities: List[VulnerabilityResult],
    output_dir: Path,
    patches_map: Dict[int, Any]
) -> List[Path]:
    """
    취약점 결과와 패치를 SARIF 파일로 저장
    - 도구별 개별 SARIF 파일 생성 ({tool}.sarif)
    - 통합 SARIF 파일 생성 (output.sarif)
    """
    sarif_files = []
    
    # 1. 취약점 객체와 패치 매핑
    vuln_to_patch = {}
    for idx, patch in patches_map.items():
        if idx < len(vulnerabilities):
            vuln_to_patch[vulnerabilities[idx]] = patch
            
    # 2. 도구별 그룹화
    tool_groups = {}
    for vuln in vulnerabilities:
        tool = vuln.tool_name
        if tool not in tool_groups:
            tool_groups[tool] = []
        tool_groups[tool].append(vuln)
        
    runs = []
    
    # 3. 각 도구별 SARIF 생성 및 runs 추가
    for tool_name, vulns in tool_groups.items():
        # 메타데이터는 첫 번째 취약점에서 가져옴
        tool_metadata = vulns[0].tool_metadata
        
        run = create_sarif_run(tool_name, tool_metadata, vulns, vuln_to_patch)
        runs.append(run)
        
        # 개별 파일 저장 ({tool-name}.sarif)
        tool_sarif = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [run]
        }
        
        safe_tool_name = tool_name.lower().replace(" ", "_")
        tool_filename = f"{safe_tool_name}.sarif"
        tool_path = output_dir / tool_filename
        
        with open(tool_path, "w", encoding="utf-8") as f:
            json.dump(tool_sarif, f, indent=2, ensure_ascii=False)
            
        logger.info(f"개별 도구 SARIF 생성: {tool_path}")
        sarif_files.append(tool_path)
        
    # 4. 통합 파일 저장 (output.sarif)
    merged_sarif = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": runs
    }
    
    merged_path = output_dir / "output.sarif"
    with open(merged_path, "w", encoding="utf-8") as f:
        json.dump(merged_sarif, f, indent=2, ensure_ascii=False)
    
    logger.info(f"통합 SARIF 생성: {merged_path}")
    sarif_files.append(merged_path)
    
    return sarif_files
