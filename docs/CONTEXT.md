---
phase: "Experimentation"
phase_name: "Obsidian Filter Syntax"
updated: 2026-02-07
last_commit: 4ba9053
branch: filters-and-combs
---

# Current Context

## Current Focus

Obsidian-compatible filter syntax implemented! Full lexer+parser with property syntax, boolean operators, and backward compatibility.

## Active Tasks

- [x] Implement FilterLexer (tokenization)
- [x] Implement FilterParser (AST building)
- [x] AST evaluation (evaluateAST, evaluateFilter)
- [x] Update UI (remove ANY/ALL toggle, new help panel)
- [x] State migration (comma syntax → OR)
- [x] Testing (11 unit tests, 30 manual test cases)

## Blockers

None.

## Context

- **Property syntax**: `[type:gleaning]`, `[status:active]`
- **Boolean operators**: `OR`, implicit `AND`, `-` (NOT)
- **Grouping**: `(tag:a OR tag:b) path:c`
- **Performance**: <2ms parse, <10ms eval, no regression
- **Backward compat**: Comma syntax auto-converts to OR

## Next Session

Optional: Manual testing with vault, server-side type/status filtering, UI error display.
