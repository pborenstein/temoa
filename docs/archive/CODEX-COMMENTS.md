# CODEX COMMENTS: Project Assessment Plan (Single Customer)

## Context

This document captures a practical assessment plan for Temoa with the explicit constraint that this is a **single-customer** project. The goal is not enterprise scaling; the goal is sustained reliability, maintainability, and continued usefulness for one real user.

---

## Executive Assessment

Temoa is a strong, technically ambitious single-customer product with a clear value proposition: local semantic search over Obsidian data, optimized for mobile access, with meaningful quality features (hybrid retrieval, re-ranking, query expansion, time awareness, chunking).

The primary risk is not feature insufficiency. The primary risk is **complexity concentration** and **maintainability drift** over time (especially in server orchestration and evolving docs/config defaults).

---

## Strengths

1. **Clear customer fit**
   - Solves a concrete workflow problem (surfacing notes quickly by meaning).
   - Strong alignment with privacy/local-first requirements.

2. **High-quality search pipeline**
   - Semantic + BM25 hybrid retrieval.
   - Optional query expansion for short prompts.
   - Cross-encoder re-ranking for precision gains.
   - Time-aware scoring and adaptive chunking.

3. **Strong documentation culture**
   - Comprehensive docs for architecture, deployment, testing, and evolution.
   - Useful for continuity and future maintenance.

4. **Operational maturity for solo usage**
   - Health checks, reindex/extract automation paths, launchd/systemd options.
   - Security hardening appropriate for trusted-network deployment (CORS/rate limits/path validation).

5. **Good test discipline**
   - Broad test coverage for core behavior and edge cases.
   - Clear test status reporting and guidance.

---

## Weaknesses

1. **Server complexity concentration**
   - `src/temoa/server.py` contains many responsibilities (routing, filtering, pipeline debugging, orchestration).
   - This increases change risk and cognitive load.

2. **Potential docs/config drift**
   - Minor inconsistencies in defaults/versions/model references across docs can create confusion during updates/incidents.

3. **Packaging fragility for portability**
   - Local path dependency (`nahuatl-frontmatter`) may complicate reproducible setup on another machine.

4. **Feature breadth vs maintenance capacity**
   - Experimental features are valuable, but could outpace sustainable maintenance for one-customer operations.

5. **Environment assumptions**
   - Reliability depends on Tailscale, local model caches, and local machine state; migration/setup could be smoother.

---

## Improvements (Prioritized for One Customer)

### Priority 1: Reduce risk while preserving velocity

1. **Modularize server responsibilities**
   - Split request parsing, filtering, scoring pipeline, and response formatting into separate modules.
   - Expected result: safer iteration and easier testing.

2. **Define “stable core” vs “experimental” surface**
   - Keep core endpoints and UI defaults stable.
   - Gate experimental features behind explicit config flags.

3. **Create a production profile for this customer**
   - Pin model, search defaults, chunking settings, and operational limits in one canonical profile.
   - Reduces accidental behavior changes.

### Priority 2: Improve maintainability and reproducibility

4. **Unify defaults in one source of truth**
   - Centralize defaults and use docs references/generated snippets where possible.
   - Reduces drift.

5. **Harden dependency strategy**
   - Replace or formalize local-path dependencies for easier machine portability.

### Priority 3: Practical reliability polish

6. **Add lightweight operational telemetry endpoint**
   - Track last successful extract/reindex, index age, and recent search latency.

7. **Codify a pre-release smoke checklist/script**
   - Health, search sanity, mobile access, reindex, and Obsidian deep-link checks.

---

## 30-Day Implementation Plan (Single-Customer Focus)

### Week 1
- Refactor high-risk sections of `server.py` into helper modules (no behavior change).
- Add/adjust tests to lock current behavior.

### Week 2
- Introduce stable vs experimental config toggles.
- Document canonical customer production profile.

### Week 3
- Resolve dependency portability concerns.
- Add lightweight operational status endpoint.

### Week 4
- Create release smoke-check script and runbook.
- Run one full upgrade/restart drill to validate repeatability.

---

## Bottom Line

Temoa is already effective and production-usable for one customer. The best next step is not adding many new features; it is consolidating maintainability and reliability so the existing quality remains sustainable over time.
