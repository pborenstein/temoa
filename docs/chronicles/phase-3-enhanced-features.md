# Phase 3: Enhanced Features - Chronicles

> **Timeline**: 2025-11-26 onwards
> **Status**: In Progress
> **Goal**: Fix technical debt, improve search quality, polish UX

---

## Entry 20: Multi-Vault Support - Preventing Data Loss (2025-11-26)

**Problem**: The `--vault` flag was broken and dangerous.

**What was broken**:
```bash
# This command was SUPPOSED to index vault2:
temoa index --vault ~/vaults/vault2

# But ACTUALLY stored the index in vault1's .temoa/:
# vault1/.temoa/index.json  ← OVERWRITTEN with vault2 data!
```

**Root cause** (in `src/temoa/cli.py`):
```python
# CLI accepted --vault override:
vault_path = Path(vault) if vault else config.vault_path  ✅

# But always used config's storage:
storage_dir = config.storage_dir  ❌ ALWAYS vault1/.temoa/!

# Created client with mismatched paths:
client = SynthesisClient(
    vault_path=vault2,        # Index vault2's files
    storage_dir=vault1/.temoa  # But store in vault1's directory!
)
```

**Impact**:
- **Data loss**: Indexing vault2 overwrote vault1's embeddings
- **Corruption**: File tracking mixed up between vaults
- **Incremental reindex broken**: Tracked wrong files
- **Silent failure**: No warning, user unaware of problem

### The Fix: Vault-Aware Storage Derivation

**Core strategy**: Storage directory must follow vault path.

**New module**: `src/temoa/storage.py` (195 lines)

**Key functions**:

1. **`derive_storage_dir(vault_path, config_vault_path, config_storage_dir)`**
   ```python
   if vault_path == config_vault_path:
       return config_storage_dir  # Honor user's config
   else:
       return vault_path / ".temoa"  # Auto-derive for other vaults
   ```

2. **`validate_storage_safe(storage_dir, vault_path, operation, force=False)`**
   ```python
   # Read existing index.json
   if index_file.exists():
       stored_vault = index_data["vault_path"]
       if stored_vault != vault_path and not force:
           raise ConfigError(f"""
Storage directory mismatch detected!

Operation: {operation}
Target vault: {vault_path}
Existing index vault: {stored_vault}
Storage dir: {storage_dir}

This would overwrite the index for a different vault.

Solutions:
  1. Use correct vault: --vault {stored_vault}
  2. Delete old index: rm -rf {storage_dir}
  3. Force overwrite: {operation} --vault {vault_path} --force
           """)
   ```

3. **Auto-migration for old indexes**:
   ```python
   if "vault_path" not in index_data:
       # Old index without metadata - add it
       index_data["vault_path"] = str(vault_path.resolve())
       index_data["vault_name"] = vault_path.name
       index_data["migrated_at"] = datetime.now().isoformat()
       # Write back
       index_file.write_text(json.dumps(index_data, indent=2))
   ```

### CLI Updates (All 5 Commands)

**Pattern applied to**: `index`, `reindex`, `search`, `archaeology`, `stats`

```python
# Before (BROKEN):
def command(vault):
    config = Config()
    vault_path = Path(vault) if vault else config.vault_path
    client = SynthesisClient(
        vault_path=vault_path,
        storage_dir=config.storage_dir  # ❌ WRONG
    )

# After (FIXED):
def command(vault, force=False):  # Added --force flag for index/reindex
    from .storage import derive_storage_dir, validate_storage_safe

    config = Config()

    # Derive vault and storage together
    if vault:
        vault_path = Path(vault)
        storage_dir = derive_storage_dir(
            vault_path, config.vault_path, config.storage_dir
        )
    else:
        vault_path = config.vault_path
        storage_dir = config.storage_dir

    # Validate before write operations
    if operation_is_write:  # index, reindex
        validate_storage_safe(storage_dir, vault_path, "command", force)

    client = SynthesisClient(
        vault_path=vault_path,
        storage_dir=storage_dir  # ✅ CORRECT
    )
```

**New flags**:
- `--force` added to `index` and `reindex` for override (with warning)
- `--vault` added to `search`, `archaeology`, `stats` (read-only ops)

### Vault Metadata in Index

**Added to `index.json`** (in `src/temoa/synthesis.py:950`):
```python
model_info = {
    "model_name": self.pipeline.engine.model_name,
    "embedding_dim": embeddings.shape[1],
    "vault_path": str(self.vault_path.resolve()),  # ← NEW
    "vault_name": self.vault_path.name,            # ← NEW
    "indexed_at": datetime.now().isoformat()       # ← NEW
}
```

**Purpose**:
- **Validation**: Detect vault mismatches before operations
- **Logging**: Better error messages with vault names
- **Future**: Multi-vault search, vault switching

### Testing

**Unit tests** (`tests/test_storage.py` - 13 tests, all passing):
- ✅ Storage derivation for config vault vs other vaults
- ✅ Vault mismatch detection raises ConfigError
- ✅ Force flag bypasses validation
- ✅ Auto-migration of old indexes
- ✅ Corrupted index doesn't crash validation
- ✅ Metadata retrieval functions

**Integration tests** (`tests/test_multi_vault_integration.py`):
- Marked as requiring Synthesis (manual testing)
- Provides test structure for future CI/CD

**Manual testing** (2025-11-26):
```bash
# Test 1: Config vault unchanged
$ temoa stats
Vault path: /Users/philip/Obsidian/amoxtli
Storage: /Users/philip/Obsidian/amoxtli/.temoa
Files indexed: 3067  ✅ Still works

# Test 2: Other vault derives storage
$ temoa stats --vault /tmp/temoa-test-vault-2
Vault path: /tmp/temoa-test-vault-2
Storage: /tmp/temoa-test-vault-2/.temoa  ✅ Auto-derived!

# Test 3: Each vault independent
$ ls /Users/philip/Obsidian/amoxtli/.temoa/
index.json  all-mpnet-base-v2/  ✅ Config vault's index

$ ls /tmp/temoa-test-vault-2/.temoa/
all-mpnet-base-v2/  ✅ Separate directory
```

### User Experience

**For single-vault users** (99% of users):
- ✅ No changes needed
- ✅ Works exactly as before
- ✅ Auto-migration adds metadata (one-time, automatic)

**For multi-vault users**:
- ✅ Each vault gets independent `.temoa/` directory
- ✅ Can switch vaults with `--vault` flag
- ✅ Validation prevents accidental overwrites
- ✅ Clear error messages with solutions

**Error messages** (example):
```
Storage directory mismatch detected!

Operation: index
Target vault: /Users/philip/vaults/vault2
Existing index vault: /Users/philip/vaults/vault1
Storage dir: /Users/philip/vaults/vault1/.temoa

This would overwrite the index for a different vault, causing data loss.

Solutions:
  1. Use correct vault path:
     temoa index --vault /Users/philip/vaults/vault1

  2. Delete existing index (if you're sure):
     rm -rf /Users/philip/vaults/vault1/.temoa

  3. Force overwrite (DANGER - will lose existing index):
     temoa index --vault /Users/philip/vaults/vault2 --force
```

### Design Decisions

**DEC-036: Multi-Vault Storage Strategy**
- **Decision**: Auto-derive storage as `vault/.temoa/` for non-config vaults
- **Alternative considered**: Centralized storage (e.g., `~/.config/temoa/indexes/`)
- **Rationale**:
  - Co-location is intuitive (index lives with vault)
  - Simpler for users (no additional path management)
  - Easier to backup/sync (vault + index together)
  - Matches Obsidian's .obsidian/ pattern
- **Trade-off**: Index not portable across machines (but embeddings aren't either)

**DEC-037: Validation Before Operations**
- **Decision**: Validate vault match before write operations, fail early
- **Alternative considered**: Warn but allow (soft validation)
- **Rationale**:
  - Data loss is catastrophic (can't undo)
  - Better to block and require --force
  - Clear error messages guide users to solution
  - Prevents accidental mistakes

**DEC-038: Auto-Migration of Old Indexes**
- **Decision**: Automatically add metadata to old indexes on first access
- **Alternative considered**: Require manual reindex
- **Rationale**:
  - Seamless upgrade experience
  - No user action required
  - One-time cost (only missing metadata)
  - Logged for visibility

### Backward Compatibility

**100% backward compatible**:
- ✅ Existing configs work without changes
- ✅ Old indexes auto-migrate on first use
- ✅ Single-vault users see no difference
- ✅ Storage location unchanged for config vault
- ✅ All existing CLI commands work

**Breaking changes**: None

**Deprecations**: None

### Files Changed

1. **`src/temoa/storage.py`** (195 lines) - NEW FILE
   - Core vault-aware storage utilities
   - Validation and auto-migration logic

2. **`src/temoa/cli.py`** (5 commands updated)
   - `index()` - Added --force, storage derivation, validation
   - `reindex()` - Added --force, storage derivation, validation
   - `search()` - Added --vault support
   - `archaeology()` - Added --vault support
   - `stats()` - Added --vault support

3. **`src/temoa/synthesis.py`** (3 lines added)
   - Added vault metadata to `model_info` dict (line 953-955)

4. **`tests/test_storage.py`** (282 lines) - NEW FILE
   - 13 unit tests, all passing

5. **`tests/test_multi_vault_integration.py`** (188 lines) - NEW FILE
   - Integration test structure (manual testing)

6. **`pyproject.toml`** (1 line added)
   - Added pytest as dev dependency

7. **`uv.lock`** (updated dependencies)

### Commit

```
feat: implement multi-vault support with safe storage derivation

This fixes the critical bug where `temoa index --vault /other/vault`
would store the index in the config vault's .temoa/, causing data loss.

Closes: Phase 3 Part 0 - Multi-Vault Support
Resolves: Data loss bug from IMPLEMENTATION.md line 1149
```

### What's Next

**Phase 3 Part 1: Technical Debt** (next up):
- Fix module-level initialization
- Remove sys.path manipulation
- Introduce service layer

**Phase 3 Part 2: Search Quality**:
- Cross-encoder re-ranking
- Query expansion
- Time-aware scoring

**Phase 3 Part 3: UI/UX Polish**:
- PWA support
- Keyboard shortcuts
- Search history

### Key Insight

**From PHASE-3-READY.md**:
> This bug was a **time bomb**. Anyone using `--vault` for testing or multi-vault workflows risked silent data corruption. The fix is surgical: validate before operations, fail with clear solutions, provide escape hatch via --force.

**Lesson learned**: Optional flags that change behavior (like `--vault`) must be comprehensively tested across all code paths. Path derivation must be atomic (vault + storage together, not separately).

---

**Entry created**: 2025-11-26
**Author**: Claude (Sonnet 4.5)
**Status**: Multi-vault support implemented, tested, and documented
