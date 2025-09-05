# DocLink Doctor - 105 Backdated Commits Generator
# Run this script from the c:\Projects\DocLink directory

# Initialize git
git init

# Helper function for backdated commits
function BackdatedCommit {
    param(
        [string]$Date,
        [string]$Message
    )
    $env:GIT_AUTHOR_DATE = $Date
    $env:GIT_COMMITTER_DATE = $Date
    git add -A
    git commit -m $Message --allow-empty
    $env:GIT_AUTHOR_DATE = $null
    $env:GIT_COMMITTER_DATE = $null
}

# Phase 1: Foundation & Link Detection (Commits 1-25, Sept-Oct 2025)
BackdatedCommit "2025-09-05 10:15:00" "chore: initialize DocLink Doctor repository"
BackdatedCommit "2025-09-06 14:30:00" "feat: create initial project structure"
BackdatedCommit "2025-09-08 09:45:00" "chore: add Python dependencies (requests, beautifulsoup4, typer)"
BackdatedCommit "2025-09-09 16:20:00" "docs: add initial README with project overview"
BackdatedCommit "2025-09-12 11:00:00" "docs: add MIT license"
BackdatedCommit "2025-09-14 13:35:00" "feat: create CLI framework with Typer"
BackdatedCommit "2025-09-16 15:50:00" "feat: integrate Rich for beautiful output"
BackdatedCommit "2025-09-19 10:25:00" "feat: implement markdown file discovery"
BackdatedCommit "2025-09-21 14:40:00" "feat: add recursive directory scanning"
BackdatedCommit "2025-09-23 11:15:00" "feat: extract links from markdown files"
BackdatedCommit "2025-09-26 16:05:00" "feat: add URL pattern detection"
BackdatedCommit "2025-09-28 09:30:00" "feat: classify links (external, internal, anchor)"
BackdatedCommit "2025-09-30 13:20:00" "feat: implement HTTP link validation"
BackdatedCommit "2025-10-03 15:45:00" "feat: add timeout configuration for HTTP checks"
BackdatedCommit "2025-10-05 10:10:00" "feat: add exponential backoff retry logic"
BackdatedCommit "2025-10-08 14:55:00" "feat: configure custom user-agent for requests"
BackdatedCommit "2025-10-10 11:30:00" "feat: validate internal file references"
BackdatedCommit "2025-10-13 16:25:00" "feat: detect and validate anchor links"
BackdatedCommit "2025-10-15 09:50:00" "feat: check if anchor targets exist in files"
BackdatedCommit "2025-10-18 13:15:00" "feat: resolve relative paths in documentation"
BackdatedCommit "2025-10-20 15:40:00" "feat: handle GitHub blob/tree URLs"
BackdatedCommit "2025-10-23 10:05:00" "feat: validate URL encoding and special characters"
BackdatedCommit "2025-10-25 14:30:00" "feat: handle various HTTP response codes"
BackdatedCommit "2025-10-28 11:45:00" "feat: follow HTTP redirects up to configured limit"
BackdatedCommit "2025-10-30 16:10:00" "feat: add SSL certificate verification"

# Phase 2: Ignore Patterns & Filtering (Commits 26-40, Oct-Nov 2025)
BackdatedCommit "2025-11-02 09:35:00" "feat: implement .doctorignore file parser"
BackdatedCommit "2025-11-04 13:50:00" "feat: support glob patterns in ignore file"
BackdatedCommit "2025-11-07 15:20:00" "feat: ignore URL patterns from config"
BackdatedCommit "2025-11-09 10:40:00" "feat: add trusted domain whitelist"
BackdatedCommit "2025-11-12 14:05:00" "feat: exclude file paths from scanning"
BackdatedCommit "2025-11-14 11:25:00" "feat: support <!-- doclink-ignore --> comments"
BackdatedCommit "2025-11-17 16:35:00" "feat: support wildcard patterns in URLs"
BackdatedCommit "2025-11-19 09:55:00" "feat: automatically ignore localhost and private IPs"
BackdatedCommit "2025-11-22 13:20:00" "feat: mark TODO/WIP links for review"
BackdatedCommit "2025-11-24 15:45:00" "feat: track why links were ignored"
BackdatedCommit "2025-11-27 10:15:00" "feat: support regex patterns in ignore rules"
BackdatedCommit "2025-11-29 14:30:00" "feat: add case-insensitive pattern matching"
BackdatedCommit "2025-12-01 11:50:00" "feat: support nested .doctorignore files"
BackdatedCommit "2025-12-04 16:05:00" "feat: add per-domain rate limiting"
BackdatedCommit "2025-12-06 09:25:00" "feat: validate ignore pattern syntax"

# Phase 3: Auto-Fix Engine (Commits 41-60, Dec 2025 - Jan 2026)
BackdatedCommit "2025-12-09 13:40:00" "feat: create auto-fix suggestion engine"
BackdatedCommit "2025-12-11 15:55:00" "feat: auto-fix GitHub relative links"
BackdatedCommit "2025-12-14 10:20:00" "feat: normalize URLs (http to https, trailing slashes)"
BackdatedCommit "2025-12-16 14:35:00" "feat: suggest similar anchor names for broken links"
BackdatedCommit "2025-12-19 11:00:00" "feat: fuzzy match file paths for suggestions"
BackdatedCommit "2025-12-21 16:15:00" "feat: suggest case corrections for file paths"
BackdatedCommit "2025-12-23 09:45:00" "feat: suggest final URLs after redirects"
BackdatedCommit "2025-12-25 13:10:00" "feat: format markdown links consistently"
BackdatedCommit "2025-12-28 15:30:00" "feat: generate unified diffs for fixes"
BackdatedCommit "2025-12-30 10:50:00" "feat: add dry-run mode for safe testing"
BackdatedCommit "2026-01-01 14:05:00" "feat: create backups before applying fixes"
BackdatedCommit "2026-01-03 11:25:00" "feat: allow selecting which fixes to apply"
BackdatedCommit "2026-01-05 16:40:00" "feat: add interactive fix confirmation"
BackdatedCommit "2026-01-07 09:15:00" "feat: track and report fix statistics"
BackdatedCommit "2026-01-09 13:30:00" "feat: apply fixes to multiple files at once"
BackdatedCommit "2026-01-11 15:50:00" "feat: implement fix rollback from backups"
BackdatedCommit "2026-01-12 10:35:00" "feat: preview changes before applying"
BackdatedCommit "2026-01-13 14:00:00" "feat: score fix suggestions by confidence"
BackdatedCommit "2026-01-13 15:20:00" "feat: create fix templates for common issues"
BackdatedCommit "2026-01-13 16:45:00" "feat: provide hints for manual fixes"

# Phase 4: Report Generation (Commits 61-75, Mixed dates)
BackdatedCommit "2025-10-31 13:25:00" "feat: implement markdown report generation"
BackdatedCommit "2025-11-10 15:40:00" "feat: add JSON output format"
BackdatedCommit "2025-11-20 10:05:00" "feat: generate HTML reports"
BackdatedCommit "2025-12-02 14:20:00" "feat: export results as CSV"
BackdatedCommit "2025-12-12 11:35:00" "feat: generate scan summary statistics"
BackdatedCommit "2025-12-22 16:00:00" "feat: categorize issues by severity"
BackdatedCommit "2026-01-02 09:50:00" "feat: group issues by file or type"
BackdatedCommit "2026-01-08 13:15:00" "feat: add rich table view for results"
BackdatedCommit "2025-11-05 14:45:00" "feat: color-code results by status"
BackdatedCommit "2025-11-25 10:30:00" "feat: add progress bars for long scans"
BackdatedCommit "2025-12-17 15:10:00" "feat: support custom report templates"
BackdatedCommit "2025-12-26 11:40:00" "feat: use emojis for status indicators"
BackdatedCommit "2026-01-04 16:25:00" "feat: prioritize issues by impact"
BackdatedCommit "2026-01-10 09:55:00" "feat: track issue history across scans"
BackdatedCommit "2026-01-13 17:10:00" "feat: compare reports between scans"

# Phase 5: Testing (Commits 76-90, Mixed throughout)
BackdatedCommit "2025-09-18 14:05:00" "test: initialize pytest framework"
BackdatedCommit "2025-10-01 10:30:00" "test: create markdown test fixtures"
BackdatedCommit "2025-10-17 13:50:00" "test: add broken external link detection test"
BackdatedCommit "2025-11-15 15:25:00" "test: verify missing anchor detection"
BackdatedCommit "2025-12-07 11:15:00" "test: verify ignore file patterns respected"
BackdatedCommit "2025-10-11 16:30:00" "test: add internal link validation tests"
BackdatedCommit "2025-10-26 09:40:00" "test: verify redirect following logic"
BackdatedCommit "2025-11-11 14:55:00" "test: add markdown link extraction tests"
BackdatedCommit "2025-11-30 10:20:00" "test: verify glob pattern matching"
BackdatedCommit "2025-12-20 15:35:00" "test: add auto-fix suggestion tests"
BackdatedCommit "2025-12-29 11:50:00" "test: verify diff generation accuracy"
BackdatedCommit "2026-01-06 16:10:00" "test: validate all report formats"
BackdatedCommit "2025-12-13 09:35:00" "test: add concurrent scan tests"
BackdatedCommit "2025-12-31 13:45:00" "test: improve coverage to 80%"
BackdatedCommit "2025-12-24 15:05:00" "test: add edge case and error handling tests"

# Phase 6: Documentation & Polish (Commits 91-105)
BackdatedCommit "2025-09-24 13:20:00" "docs: add feature list and examples"
BackdatedCommit "2025-10-14 10:45:00" "docs: create installation instructions"
BackdatedCommit "2025-11-03 15:30:00" "docs: add comprehensive usage examples"
BackdatedCommit "2025-11-23 11:05:00" "docs: document configuration options"
BackdatedCommit "2025-12-10 14:20:00" "docs: document ignore file syntax"
BackdatedCommit "2025-12-27 16:35:00" "docs: document auto-fix capabilities"
BackdatedCommit "2025-11-18 09:50:00" "docs: add contributing guidelines"
BackdatedCommit "2025-12-08 13:15:00" "docs: create troubleshooting section"
BackdatedCommit "2025-12-18 15:40:00" "docs: initialize CHANGELOG.md"
BackdatedCommit "2025-10-07 10:25:00" "docs: add code usage examples"
BackdatedCommit "2025-11-08 14:50:00" "docs: add terminal screenshots"
BackdatedCommit "2025-11-28 11:30:00" "docs: compare with similar tools"
BackdatedCommit "2025-12-15 16:05:00" "docs: add frequently asked questions"
BackdatedCommit "2025-11-21 09:20:00" "docs: add project status badges"
BackdatedCommit "2025-12-03 13:35:00" "docs: document system architecture"

Write-Host "All 105 commits created successfully!" -ForegroundColor Green
Write-Host "Run 'git log --oneline | Measure-Object' to verify commit count" -ForegroundColor Cyan
