# Changelog

All notable changes to DocLink Doctor will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-13

### Added
- Initial release of DocLink Doctor
- Markdown file scanning with recursive directory support
- External link validation via HTTP requests
- Internal file reference checking
- Anchor link validation
- `.doctorignore` file support with glob and regex patterns
- Auto-fix suggestion engine with confidence scoring
- Multiple report formats: Markdown, JSON, HTML, CSV
- Rich terminal output with progress bars
- CLI commands: `scan`, `fix`, `report`
- Dry-run mode for safe testing
- Backup system before applying fixes
- Rate limiting for external requests
- Retry logic with exponential backoff

### Features
- Detect dead external links (HTTP 404, 500, etc.)
- Find missing anchor links in documents
- Validate internal file references
- Generate auto-fix suggestions for common issues
- Support comment-based ignore directives
- Handle GitHub-specific URL formats
