# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please report it responsibly.

### How to Report

**Do not** open a public GitHub issue for security vulnerabilities.

Instead, email security details to: **matt@bordenet.com**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity (critical issues prioritized)

### Disclosure Policy

- We will acknowledge your report within 48 hours
- We will provide regular updates on our progress
- We will credit you in the security advisory (unless you prefer to remain anonymous)
- We will coordinate disclosure timing with you

## Security Best Practices

### For Users

1. **API Keys and Credentials**
   - Never commit API keys to version control
   - Use `.env` files for local configuration
   - Rotate API keys regularly
   - Use environment variables for sensitive data

2. **Corpus Content**
   - Review corpus for proprietary information before indexing
   - Use blocklist feature to prevent leaking sensitive terms
   - Validate generated content before sharing externally
   - Keep corpus files in secure locations

3. **LLM Providers**
   - Use local LLMs (Ollama) for sensitive content
   - Review cloud provider terms of service
   - Understand data retention policies
   - Consider data residency requirements

4. **Dependencies**
   - Keep dependencies updated
   - Review security advisories regularly
   - Use `pip-audit` to check for known vulnerabilities

### For Developers

1. **Code Security**
   - Run `bandit` security scanner before committing
   - Run `gitleaks` to detect secrets
   - Use pre-commit hooks for automated checks
   - Follow principle of least privilege

2. **Input Validation**
   - Validate all user inputs
   - Sanitize file paths
   - Check file types and sizes
   - Handle errors gracefully

3. **Dependencies**
   - Pin dependency versions in `pyproject.toml`
   - Review dependency changes in PRs
   - Use `pip-audit` in CI/CD
   - Keep security-critical dependencies updated

## Known Security Considerations

### Local File Access

Bloginator reads and writes local files. Users should:
- Only index trusted content
- Review file paths before extraction
- Use appropriate file permissions
- Avoid running with elevated privileges

### LLM API Calls

When using cloud LLM providers:
- Content is sent to third-party APIs
- Review provider privacy policies
- Consider using local LLMs for sensitive content
- Implement rate limiting for API calls

### Vector Database

ChromaDB stores embeddings locally:
- Embeddings may contain semantic information
- Store databases in secure locations
- Consider encryption for sensitive corpora
- Regularly backup important indices

## Security Tools

This project uses:
- **Gitleaks**: Secret detection in commits
- **Bandit**: Python security linter
- **pip-audit**: Dependency vulnerability scanner
- **Pre-commit hooks**: Automated security checks

Run security checks:
```bash
# Check for secrets
gitleaks detect --source . --verbose

# Run security linter
bandit -r src/bloginator/

# Check dependencies
pip-audit
```

## Acknowledgments

We appreciate responsible disclosure and will acknowledge security researchers who help improve Bloginator's security.
