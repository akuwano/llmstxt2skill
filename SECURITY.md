# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it by opening a GitHub issue or contacting the maintainers directly.

**Please include:**
- A description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Any suggested fixes (optional)

We will respond to security reports within 7 days and aim to release patches for confirmed vulnerabilities promptly.

## Security Considerations

This tool:
- Fetches content from URLs provided by the user
- Writes files to the local filesystem (`~/.claude/skills/` by default)

Users should only use this tool with trusted URLs.
