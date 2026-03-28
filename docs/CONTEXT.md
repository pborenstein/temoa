---
phase: "Production Hardening"
phase_name: "Part 10: Service Management"
updated: 2026-03-28
last_commit: 4d2176c
branch: main
---

# Current Context

## Current Focus

Rewrote `dev.sh` and launchd scripts to use modern `launchctl bootstrap/bootout` API. Service now reliably stops (even with KeepAlive=true), no exit prompt, subcommands for start/stop/status.

## Active Tasks

- [x] Rewrite dev.sh with subcommands (dev/start/stop/status)
- [x] Modernize launchctl calls in install.sh and uninstall.sh
- [x] Remove deprecated load/unload from all scripts
- [ ] 181 remaining empty gleaning descriptions — accept or manual

## Blockers

None

## Context

- `launchctl bootout` force-kills the process, unlike deprecated `unload` which KeepAlive could override
- `launchctl bootstrap` replaces `load`; `launchctl print` replaces `list | grep`
- Service label is `dev.pborenstein.temoa` (reverse-domain convention, not username)
- Same changes applied to apantli for consistency
- Old `dev.philip.*` plist files cleaned up from ~/Library/LaunchAgents/
- Test baseline: 196 passed, 0 failed, 0 skipped

## Next Session

Move to Experimentation phase: document baseline search performance and start parameter tuning with the Search Harness.
