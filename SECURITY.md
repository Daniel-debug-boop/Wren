# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| Latest  | :white_check_mark: |
| < Latest| :x:                |

## Reporting a Vulnerability

We take the security of Wren and its ecosystem seriously. If you believe you have found a security vulnerability, please **do not** open a public issue.

Instead, report it privately by:

1. **Emailing us** at: `security@wren.ai` *(replace with actual security contact)*
2. **Using GitHub's private vulnerability reporting** at: https://github.com/Daniel-debug-boop/Wren/security/advisories/new

Please include as much information as possible:
- Type of vulnerability
- Full path of the affected file(s)
- Steps to reproduce
- Proof of concept (if available)

### What to expect

- **Acknowledgment** within 48 hours
- **Status update** within 5 business days
- **Fix timeline** communicated based on severity

## Disclosure Policy

When we receive a security bug report, we will:

1. Confirm the problem and determine affected versions
2. Audit code to find any similar issues
3. Prepare fixes for all supported versions
4. Release fixes and publish a security advisory on GitHub

## Security Best Practices

When deploying Wren:

- **API Keys**: Never commit API keys to version control. Use environment variables or a secrets manager.
- **Network**: Run the backend behind a reverse proxy (Nginx, Caddy) with TLS enabled.
- **Authentication**: Enable authentication in production deployments.
- **Updates**: Keep dependencies updated. Use `poetry update` regularly.
- **Sandboxing**: Run LLM-generated code in isolated environments (Docker containers).
- **Rate Limiting**: Configure rate limiting on API endpoints to prevent abuse.

## Responsible Disclosure

We believe in responsible disclosure. We will credit security researchers who report vulnerabilities according to these guidelines.

## Scope

The following are in scope:
- The Wren Python backend (`wren/` directory)
- The Wren SDK (`wren-sdk/` directory)
- The Android client (`wren-android/` directory)
- The web frontend (`frontend/` directory)

The following are **out of scope**:
- LLM provider API keys or services
- Third-party dependencies (report those to their respective maintainers)
- Theoretical attacks without proof of concept

## Hall of Fame

We thank the following researchers for their responsible disclosures:

*(This list will be updated as reports are received)*

---

*Last updated: 2026-07-23*
