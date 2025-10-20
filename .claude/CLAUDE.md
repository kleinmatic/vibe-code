# Project Instructions for Claude Code

## Security - Credential Handling

**CRITICAL: This repository is public. Never write, save, or commit any sensitive information to this directory.**

### Prohibited Content
- API keys, tokens, or secrets
- Passwords or authentication credentials
- Private keys, certificates, or .pem files
- .env files containing sensitive data
- Personal information (email addresses, phone numbers, physical addresses)
- Database connection strings with credentials
- OAuth secrets or client secrets
- Any hardcoded credentials in source code

### Best Practices
- Use environment variables for secrets (document them in README, never include values)
- Add `.env*` to .gitignore (already configured)
- If credentials are needed for testing, use placeholder values like `YOUR_API_KEY_HERE`
- Recommend external credential management in documentation
- Always verify files before committing

### Reminder
This is a public repository showcasing educational and experimental code. All content must be safe for public viewing.
