"""
CLI 진입점 - Typer 기반 커맨드라인 인터페이스
"""
import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from loguru import logger

from sarif_cli.detector import detect_languages
from sarif_cli.analyzer import analyze_project
from sarif_cli.settings import load_settings

app = typer.Typer()
console = Console()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    input_dir: Optional[Path] = typer.Option(
        None,
        "--input-dir",
        "-i",
        help="분석할 프로젝트 소스 코드 디렉토리",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="SARIF 결과 파일 저장 디렉토리",
    ),
    llm_url: Optional[str] = typer.Option(
        None,
        "--llm-url",
        help="LLM 서비스 URL (예: http://localhost:8000)",
    ),
    llm_key: Optional[str] = typer.Option(
        None,
        "--llm-key",
        help="LLM API 키 (선택)",
    ),
    enable_llm: bool = typer.Option(
        False,
        "--enable-llm",
        help="LLM 검증 활성화",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help=".env 설정 파일 경로 (기본: .env)",
    ),
):
    """
    SAST 분석 + LLM 검증 + 패치 생성
    
    예시:
        sarif-cli -i ./my-project -o ./results
        sarif-cli -i ./my-project -o ./results --enable-llm --llm-url http://localhost:8000
        
    환경 변수로 설정:
        export SARIF_CLI_ENABLE_LLM=true
        export SARIF_CLI_LLM_URL=http://localhost:8000
        sarif-cli -i ./my-project -o ./results
    """
    # 서브커맨드가 호출되면 여기서 멈춤
    if ctx.invoked_subcommand is not None:
        return
    
    # input_dir과 output_dir이 없으면 도움말 표시
    if input_dir is None or output_dir is None:
        console.print("[red]Error: --input-dir and --output-dir are required[/red]")
        raise typer.Exit(1)
    
    # 설정 로드 (CLI 인자 > 환경 변수 > .env 파일)
    settings = load_settings(
        enable_llm=enable_llm,
        llm_url=llm_url,
        llm_key=llm_key,
    )
    
    console.print(f"[bold green]🔍 SAST 분석 시작[/bold green]")
    console.print(f"입력: {input_dir}")
    console.print(f"출력: {output_dir}")
    if settings.enable_llm:
        console.print(f"[cyan]LLM: 활성화 (URL: {settings.llm_url or 'Not configured'})[/cyan]")
    else:
        console.print(f"[dim]LLM: 비활성화[/dim]")
    
    # 1. 출력 디렉토리 생성
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. 언어 감지
    console.print("\n[yellow]📝 언어 감지 중...[/yellow]")
    languages = detect_languages(input_dir)
    console.print(f"감지된 언어: {', '.join(languages)}")
    
    # 3. SAST 분석 실행
    console.print("\n[yellow]🔬 SAST 분석 실행 중...[/yellow]")
    results = analyze_project(input_dir, languages)
    console.print(f"발견된 취약점 후보: {len(results)}개")
    
    # 4. LLM 검증 (설정에 따라)
    patches_map = {}
    if settings.enable_llm:
        console.print("\n[yellow]🤖 LLM 검증 및 패치 생성 중...[/yellow]")
        from sarif_cli.llm_verifier import verify_and_generate_patch, read_source_file
        
        for idx, vuln in enumerate(results):
            # 소스 파일 읽기
            source_code = read_source_file(vuln.file_path)
            if source_code:
                # LLM 검증 및 패치 생성
                patch_result = verify_and_generate_patch(
                    vuln, 
                    source_code, 
                    settings.llm_url, 
                    settings.llm_api_key
                )
                if patch_result:
                    patches_map[idx] = patch_result
                    console.print(f"  ✓ {vuln.file_path.name}:{vuln.line} - {patch_result.explanation[:50]}...")
        
        console.print(f"패치 생성 완료: {len(patches_map)}개")
    
    # 5. SARIF 파일 작성
    console.print("\n[yellow]💾 SARIF 파일 작성 중...[/yellow]")
    
    # 파일별로 취약점과 패치를 그룹화
    from sarif_cli.writer import write_sarif_results_with_patches
    sarif_files = write_sarif_results_with_patches(results, output_dir, patches_map)
    
    console.print(f"\n[bold green]✅ 완료! {len(sarif_files)}개 SARIF 파일 생성[/bold green]")
    for sarif_file in sarif_files:
        console.print(f"  - {sarif_file}")


if __name__ == "__main__":
    app()
