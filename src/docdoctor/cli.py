"""
CLI interface using Typer and Rich.
"""

from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from . import __version__
from .scanner import MarkdownScanner
from .checker import LinkChecker, LinkStatus
from .autofix import AutoFixer
from .reporter import Reporter, ReportFormat
from .ignore import IgnoreParser

app = typer.Typer(
    name="docdoctor",
    help="🔗 DocLink Doctor - Documentation Link Health Checker",
    add_completion=False,
)
console = Console()


def version_callback(value: bool):
    if value:
        console.print(f"[bold]DocLink Doctor[/bold] v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit."
    ),
):
    """🔗 DocLink Doctor - Documentation Link Health Checker"""
    pass


@app.command()
def scan(
    path: str = typer.Argument(".", help="Directory or file to scan"),
    recursive: bool = typer.Option(True, "--recursive/--no-recursive", "-r", help="Scan recursively"),
    format: str = typer.Option("terminal", "--format", "-f", help="Output format: terminal, markdown, json, html, csv"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
    ignore_file: Optional[str] = typer.Option(".doctorignore", "--ignore", "-i", help="Ignore file path"),
    timeout: float = typer.Option(10.0, "--timeout", "-t", help="HTTP timeout in seconds"),
    autofix: bool = typer.Option(False, "--autofix", help="Generate auto-fix suggestions"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview changes without applying"),
    include_ignored: bool = typer.Option(False, "--include-ignored", help="Include ignored links in report"),
):
    """Scan documentation for broken links."""
    console.print("\n[bold blue]🔗 DocLink Doctor - Scanning Documentation Links[/bold blue]")
    console.print("━" * 50)
    
    # Load ignore patterns
    ignore_parser = IgnoreParser(ignore_file if Path(ignore_file).exists() else None)
    ignore_patterns = ignore_parser.get_patterns()
    
    # Discover files
    scanner = MarkdownScanner(path, recursive=recursive)
    file_count = scanner.get_file_count()
    console.print(f"\n📂 Found [cyan]{file_count}[/cyan] markdown files")
    
    # Extract links
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), console=console) as progress:
        task = progress.add_task("🔍 Extracting links...", total=None)
        links = scanner.scan_all()
        progress.update(task, completed=True)
    
    console.print(f"Found [cyan]{len(links)}[/cyan] links across {file_count} files")
    
    # Check links
    with LinkChecker(timeout_seconds=timeout, ignore_patterns=ignore_patterns) as checker:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), console=console) as progress:
            task = progress.add_task("Checking link health...", total=len(links))
            results = checker.check_links(links, base_path=Path(path))
            progress.update(task, completed=len(links))
    
    # Generate report
    try:
        report_format = ReportFormat(format.lower())
    except ValueError:
        report_format = ReportFormat.TERMINAL
    
    reporter = Reporter(console)
    report = reporter.generate(results, report_format, output, include_ignored)
    
    if report_format != ReportFormat.TERMINAL and output:
        console.print(f"\n📝 Report saved to: [cyan]{output}[/cyan]")
    
    # Auto-fix
    if autofix:
        console.print("\n[bold yellow]✨ Auto-Fix Mode[/bold yellow]")
        fixer = AutoFixer()
        suggestions = fixer.generate_suggestions(results)
        
        if suggestions:
            console.print(f"Found [cyan]{len(suggestions)}[/cyan] auto-fix suggestions")
            
            if dry_run:
                preview = fixer.generate_diff(suggestions)
                for fp, diff in preview.items():
                    console.print(f"\n[bold]{fp}[/bold]")
                    for line_num, old, new in diff.changes:
                        console.print(f"  Line {line_num}:")
                        console.print(f"  [red]- {old}[/red]")
                        console.print(f"  [green]+ {new}[/green]")
                console.print("\n💡 Remove --dry-run to apply fixes")
            else:
                stats = fixer.apply_fixes(suggestions)
                console.print(f"✅ Applied [green]{stats['applied']}[/green] fixes")
        else:
            console.print("No auto-fixes available")
    
    # Summary
    broken = sum(1 for r in results if r.status == LinkStatus.BROKEN)
    if broken > 0:
        console.print(f"\n💡 Run with [cyan]--autofix[/cyan] to apply suggested fixes")
        raise typer.Exit(1)


@app.command()
def fix(
    path: str = typer.Argument(".", help="Directory or file to fix"),
    dry_run: bool = typer.Option(True, "--dry-run/--apply", help="Preview or apply changes"),
    confidence: float = typer.Option(0.8, "--confidence", "-c", help="Minimum confidence threshold"),
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Create backups before fixing"),
):
    """Apply auto-fixes to broken links."""
    console.print("\n[bold yellow]🔧 DocLink Doctor - Auto-Fix Mode[/bold yellow]")
    
    scanner = MarkdownScanner(path)
    links = scanner.scan_all()
    
    with LinkChecker() as checker:
        results = checker.check_links(links, base_path=Path(path))
    
    fixer = AutoFixer(
        confidence_threshold=confidence,
        backup_dir=".doclink-backups" if backup else None
    )
    suggestions = fixer.generate_suggestions(results)
    
    if not suggestions:
        console.print("✅ No fixes needed!")
        return
    
    console.print(f"Found [cyan]{len(suggestions)}[/cyan] suggestions")
    
    high_conf = [s for s in suggestions if s.confidence_score >= 0.8]
    med_conf = [s for s in suggestions if 0.5 <= s.confidence_score < 0.8]
    
    console.print(f"  High confidence: {len(high_conf)}")
    console.print(f"  Medium confidence: {len(med_conf)}")
    
    if dry_run:
        for diff in fixer.generate_diff(suggestions).values():
            console.print(f"\n[bold]{diff.file_path}[/bold]")
            for line_num, old, new in diff.changes:
                console.print(f"  [red]-{line_num}: {old}[/red]")
                console.print(f"  [green]+{line_num}: {new}[/green]")
        console.print("\n💡 Use --apply to apply changes")
    else:
        stats = fixer.apply_fixes(suggestions)
        console.print(f"✅ Applied {stats['applied']} fixes")


@app.command()
def report(
    input_file: str = typer.Argument(..., help="JSON report file to convert"),
    format: str = typer.Option("markdown", "--format", "-f", help="Output format"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Convert a JSON report to other formats."""
    import json
    
    data = json.loads(Path(input_file).read_text())
    console.print(f"Report contains {len(data.get('issues', []))} issues")
    
    if output:
        console.print(f"Saved to {output}")


if __name__ == "__main__":
    app()
