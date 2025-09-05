"""
Report generation for link check results.
"""

import json
import csv
from enum import Enum
from pathlib import Path
from dataclasses import asdict
from typing import List, Dict, Optional, Any
from datetime import datetime
from io import StringIO

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from .checker import LinkResult, LinkStatus


class ReportFormat(Enum):
    MARKDOWN = "markdown"
    JSON = "json"
    HTML = "html"
    CSV = "csv"
    TERMINAL = "terminal"


class Reporter:
    """Generates reports in multiple formats."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
    
    def generate(
        self,
        results: List[LinkResult],
        format: ReportFormat,
        output_path: Optional[str] = None,
        include_ignored: bool = False
    ) -> str:
        if not include_ignored:
            results = [r for r in results if r.status != LinkStatus.IGNORED]
        
        generators = {
            ReportFormat.MARKDOWN: self._generate_markdown,
            ReportFormat.JSON: self._generate_json,
            ReportFormat.HTML: self._generate_html,
            ReportFormat.CSV: self._generate_csv,
            ReportFormat.TERMINAL: self._generate_terminal,
        }
        
        content = generators[format](results)
        
        if output_path:
            Path(output_path).write_text(content, encoding='utf-8')
        
        return content
    
    def _get_stats(self, results: List[LinkResult]) -> Dict[str, Any]:
        total = len(results)
        ok = sum(1 for r in results if r.status == LinkStatus.OK)
        broken = sum(1 for r in results if r.status == LinkStatus.BROKEN)
        warnings = sum(1 for r in results if r.status == LinkStatus.WARNING)
        ignored = sum(1 for r in results if r.status == LinkStatus.IGNORED)
        
        return {
            'total': total,
            'ok': ok,
            'broken': broken,
            'warnings': warnings,
            'ignored': ignored,
            'health_score': round((ok / total * 100) if total else 0, 1)
        }
    
    def _generate_markdown(self, results: List[LinkResult]) -> str:
        stats = self._get_stats(results)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        lines = [
            "# 🔗 DocLink Doctor Report\n",
            f"**Generated:** {now}",
            f"**Total Links:** {stats['total']}\n",
            "## 📊 Summary\n",
            "| Status | Count | Percentage |",
            "|--------|-------|------------|",
            f"| ✅ Healthy | {stats['ok']} | {stats['health_score']}% |",
            f"| ❌ Broken | {stats['broken']} | {round(stats['broken']/max(stats['total'],1)*100,1)}% |",
            f"| ⚠️ Warnings | {stats['warnings']} | {round(stats['warnings']/max(stats['total'],1)*100,1)}% |",
            "",
        ]
        
        broken = [r for r in results if r.status == LinkStatus.BROKEN]
        if broken:
            lines.append("## ❌ Broken Links\n")
            for r in broken:
                lines.append(f"### {r.link.file_path}:{r.link.line_number}")
                lines.append(f"- **URL:** `{r.link.url}`")
                lines.append(f"- **Error:** {r.error_message or f'HTTP {r.status_code}'}")
                if r.suggestion:
                    lines.append(f"- **Suggestion:** `{r.suggestion}`")
                lines.append("")
        
        return '\n'.join(lines)
    
    def _generate_json(self, results: List[LinkResult]) -> str:
        stats = self._get_stats(results)
        
        data = {
            'metadata': {
                'tool': 'DocLink Doctor',
                'version': '1.0.0',
                'scan_date': datetime.now().isoformat(),
            },
            'summary': stats,
            'issues': [
                {
                    'file': r.link.file_path,
                    'line': r.link.line_number,
                    'url': r.link.url,
                    'status': r.status.value,
                    'status_code': r.status_code,
                    'error': r.error_message,
                    'suggestion': r.suggestion,
                }
                for r in results if r.status != LinkStatus.OK
            ]
        }
        
        return json.dumps(data, indent=2)
    
    def _generate_html(self, results: List[LinkResult]) -> str:
        stats = self._get_stats(results)
        broken = [r for r in results if r.status == LinkStatus.BROKEN]
        
        rows = '\n'.join([
            f'<tr><td>{r.link.file_path}</td><td>{r.link.line_number}</td>'
            f'<td>{r.link.url}</td><td>{r.error_message or r.status_code}</td></tr>'
            for r in broken
        ])
        
        return f"""<!DOCTYPE html>
<html><head><title>DocLink Doctor Report</title>
<style>body{{font-family:sans-serif;margin:2em}}table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ddd;padding:8px;text-align:left}}th{{background:#f4f4f4}}</style></head>
<body><h1>🔗 DocLink Doctor Report</h1>
<p>Health Score: <strong>{stats['health_score']}%</strong></p>
<p>Total: {stats['total']} | Healthy: {stats['ok']} | Broken: {stats['broken']}</p>
<h2>Broken Links</h2>
<table><tr><th>File</th><th>Line</th><th>URL</th><th>Error</th></tr>{rows}</table>
</body></html>"""
    
    def _generate_csv(self, results: List[LinkResult]) -> str:
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['File', 'Line', 'URL', 'Status', 'Error', 'Suggestion'])
        
        for r in results:
            writer.writerow([
                r.link.file_path, r.link.line_number, r.link.url,
                r.status.value, r.error_message or '', r.suggestion or ''
            ])
        
        return output.getvalue()
    
    def _generate_terminal(self, results: List[LinkResult]) -> str:
        stats = self._get_stats(results)
        
        table = Table(title="📊 Link Check Results")
        table.add_column("File", style="cyan")
        table.add_column("Total", justify="right")
        table.add_column("✅ OK", justify="right", style="green")
        table.add_column("❌ Broken", justify="right", style="red")
        
        by_file: Dict[str, Dict] = {}
        for r in results:
            fp = r.link.file_path
            if fp not in by_file:
                by_file[fp] = {'total': 0, 'ok': 0, 'broken': 0}
            by_file[fp]['total'] += 1
            if r.status == LinkStatus.OK:
                by_file[fp]['ok'] += 1
            elif r.status == LinkStatus.BROKEN:
                by_file[fp]['broken'] += 1
        
        for fp, s in by_file.items():
            table.add_row(Path(fp).name, str(s['total']), str(s['ok']), str(s['broken']))
        
        self.console.print(table)
        self.console.print(f"\n📈 Health Score: [bold]{stats['health_score']}%[/bold]")
        
        return f"Health Score: {stats['health_score']}%"
    
    def print_progress(self, current: int, total: int, message: str = ""):
        self.console.print(f"[{current}/{total}] {message}")
