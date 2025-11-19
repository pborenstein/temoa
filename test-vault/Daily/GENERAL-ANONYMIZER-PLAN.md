# General-Purpose Anonymization Agent - Implementation Plan

*Derived from fish-history anonymization project - patterns and lessons learned*

## Executive Summary

Create a comprehensive CLI tool for sanitizing sensitive data from any text-based files, based on real-world patterns discovered during fish shell history anonymization.

## Core Architecture

### Multi-Pass Scanning System
1. **Critical Pass**: SSNs, credentials, API keys, secrets (STOP IMMEDIATELY if found)
2. **Personal Pass**: Names, emails, phones, addresses, usernames
3. **Domain Pass**: Company domains, servers, project names
4. **Cultural Pass**: Religious, political, cultural references
5. **Cleanup Pass**: Comments, metadata, file paths

## Pattern Libraries Discovered

### 1. Credentials & Secrets (CRITICAL - Zero Tolerance)
```yaml
# From real examples found:
api_keys:
  - 'sk-ant-[A-Za-z0-9]{48}'  # Anthropic API keys
  - 'sk-[A-Za-z0-9]{48}'      # OpenAI API keys
  - '[a-f0-9]{32}'            # Generic 32-char hex keys
  - 'ghp_[A-Za-z0-9]{36}'     # GitHub tokens

ssh_credentials:
  - 'ssh [a-zA-Z0-9]+@[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+'

environment_vars:
  - 'export.*API_KEY=.*'
  - 'export.*SECRET.*=.*'
  - 'export.*TOKEN.*=.*'

social_security:
  - '[0-9]{3}-[0-9]{2}-[0-9]{4}'
  - '[0-9]{9}'  # When in comments

phone_numbers:
  - '[0-9]{3}-[0-9]{3}-[0-9]{4}'
```

### 2. Personal Identifiers
```yaml
usernames:
  - Common patterns like 'pb', 'developer' in project names
  - Email prefixes before '@'
  - SSH usernames

domains:
  - Personal domains (developer.com → example.com)
  - Internal server names
  - Project-specific domains

file_paths:
  - '/Users/[username]/' → '/Users/user/'
  - Personal directory names
  - Dropbox paths with personal info
```

### 3. Cultural/Religious Content
```yaml
# Real examples anonymized:
religious_terms:
  - 'sefaria' → 'text-study-app'
  - 'jewish-wedding' → 'ceremony-planning'
  - 'Vatican' → 'Historical'
  - 'religious-digital-resources' → 'digital-resources'

cultural_files:
  - Pattern: '[religious-term].*\.(md|pdf|txt)'
  - Replace with generic equivalents
```

### 4. Comment Line Removal
```yaml
# CRITICAL: Comments often contain most sensitive data
comment_patterns:
  - '^[[:space:]]*#.*'  # All lines starting with #
  - '//.*'              # C-style comments
  - '/\*.*\*/'          # Block comments
```

## Replacement Strategy Framework

### Format-Preserving Replacements
- IP addresses: `192.168.1.100` → `XXX.XXX.XXX.XXX`
- Domains: Keep TLD structure (`developer.com` → `example.com`)
- API keys: Maintain length (`sk-abc123...` → `sk-XXXXXX...`)

### Context-Aware Substitutions
- Project names: Add generic prefix (`pb-project` → `user-project`)
- File paths: Preserve structure (`/Users/philip/` → `/Users/user/`)
- SSH commands: Keep command structure intact

### Consistent Mapping
- Same input always produces same output within session
- Maintain audit log of all replacements
- Allow reconstruction key for authorized users

## CLI Tool Specification

### Command Structure
```bash
anonymize [OPTIONS] [FILES...]

Options:
  --level {paranoid,high,medium,low}    Sensitivity level
  --dry-run                             Preview changes only
  --backup                              Create .bak files
  --audit                              Generate audit log
  --config FILE                        Custom pattern file
  --skip-cultural                      Skip cultural content
  --preserve-format                    Keep original formatting
  --whitelist PATTERN                  Skip these patterns
  --output-dir DIR                     Output directory
```

### Configuration Files
```
~/.anonymizer/
├── config/
│   ├── credentials.yaml    # API keys, tokens, secrets
│   ├── personal.yaml       # Names, SSNs, phones
│   ├── cultural.yaml       # Religious, political
│   └── metadata.yaml       # Comments, timestamps
├── replacements/
│   ├── generic.yaml        # Standard substitutions
│   └── custom.yaml         # User-defined mappings
└── logs/
    └── audit.log          # What was changed when
```

## Implementation Priority

### Phase 1: Core Engine (Critical Security)
- SSN detection and removal
- API key pattern matching
- Comment line elimination
- Basic file backup system

### Phase 2: Personal Data (High Priority)
- Name/username detection
- Email/phone patterns
- IP address anonymization
- Domain substitution

### Phase 3: Cultural Content (Medium Priority)
- Religious term detection
- Cultural reference mapping
- Political content identification

### Phase 4: Advanced Features (Low Priority)
- Multiple file format support
- Custom pattern definition
- Web-based configuration UI
- Integration plugins

## Key Lessons from Fish History Project

1. **Comments are the danger zone** - Most sensitive data lives in comments
2. **Multiple passes required** - Single pass misses contextual patterns
3. **Format preservation critical** - Users need functional output
4. **Audit trails essential** - Must know what changed and why
5. **Cultural sensitivity matters** - Religious/political content needs care
6. **SSNs can appear anywhere** - Zero tolerance, remove immediately

## Real-World Patterns Catalog

*Actual patterns found and anonymized in fish-history-sample.txt:*

- `sk-ant-XXXXXXXX` (Anthropic API key)
- `xiMk2pnchlGTo6RtA33NyNjytLD40X1q` (NYTimes API)
- `d62ed2ba3fffa2a56419e113da2aa166` (Flickr API)
- `fcd02d9266af42ccb59edbb96da8509e5086ea7e` (GitHub token)
- `# 025-82-9479` (SSN in comment - CRITICAL)
- `ssh pb@24.147.30.157` (SSH login)
- `developer.com/dev/2025` (personal domains)
- `sefaria-toy`, `jewish-wedding` (cultural content)

## Success Metrics

- **Zero sensitive data leakage** (SSN, API keys)
- **Functional output preservation** (commands still work)
- **Cultural sensitivity maintained** (no bias, inclusive)
- **Audit completeness** (every change logged)
- **User experience** (simple, fast, reliable)

---

*Generated from: fish-history-project anonymization - December 2024*
*Next steps: Implement Phase 1 (Core Engine) when ready*