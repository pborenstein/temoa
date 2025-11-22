# Phase 0 Prototypes

This directory contains test scripts for Phase 0: Discovery & Validation.

**Important**: These scripts are meant to be run on **your machine with internet access**, not in the VM.

## Current Task: 0.1 - Test Synthesis Performance

### What You Need to Do

1. **Pull the latest changes** from this repo on your machine (with internet)

2. **Configure Synthesis to use your vault**:
   ```bash
   cd /path/to/temoa
   python prototypes/setup_vault.py ~/Obsidian/toy-vault
   ```

   This updates `synthesis/synthesis_config.json` to point at your vault.

3. **Process the vault** (create embeddings - may take a few minutes):
   ```bash
   cd synthesis
   uv run main.py process
   ```

   This will:
   - Download the model (all-MiniLM-L6-v2, ~80-90MB) on first run
   - Index all markdown files in your vault
   - Create embeddings in the `embeddings/` directory

4. **Run the performance test**:
   ```bash
   cd ../..  # back to temoa root
   python prototypes/test_synthesis_performance.py
   ```

5. **Copy the output** and report back via commit message, issue, or however we're communicating

### What the Script Tests

- ✅ Available models (downloads on first run if needed)
- ✅ Vault statistics (file count, indexed directories)
- ✅ Cold start search performance
- ✅ Warm start search performance (3 queries)
- ✅ Different model performance
- ✅ Archaeology feature (temporal analysis)

### What I Need From You

After running the script, please report:

1. **Full output** of the script
2. **Are daily notes indexed?** (look in stats output)
3. **What's the average warm search time?** (should be < 1s, ideally < 500ms)
4. **Did models download successfully?** (on first run)
5. **How many files are indexed?** (does it match your vault?)

### Next Steps

After you report the results, I'll:
- Analyze the performance data
- Document findings in `docs/phase0-results.md`
- Move to Task 0.2 (subprocess integration prototype)
- Continue through Phase 0 tasks

---

## 🚨 CRITICAL FINDING: Performance Issue

**Initial test results show 3+ second search time** on a 13-file vault.

- Target: < 1 second (ideally < 500ms)
- Actual: 3.3 seconds average
- **This is 6x slower than target**

### What You Need to Do Next

#### Option A: Quick Investigation (Recommended)

Run the performance investigation script:

```bash
cd /path/to/temoa
python prototypes/investigate_performance.py
```

This will help identify WHERE the time is being spent:
- Subprocess overhead?
- Python startup time?
- Synthesis search itself?

#### Option B: Test Your Vault Directly

You can also test Synthesis directly from its directory:

```bash
cd synthesis
time uv run main.py search "semantic search" --json
```

This bypasses the subprocess and lets you measure Synthesis performance directly.
Compare timing to the subprocess results from the performance test.

#### Option C: Both (Best)

Do both A and B, then report all findings.

### Why This Matters

At 3+ seconds per search:
- ❌ Too slow for mobile use
- ❌ Won't form habit (too much friction)
- ❌ May need different architecture (daemon, cache, etc.)

We need to understand the bottleneck before proceeding to Phase 1.

---

## Communication Pattern

1. I create scripts and push to repo
2. You pull and run on your machine (with internet/vault access)
3. You report results back
4. I analyze and create next script
5. Repeat until Phase 0 is complete

This way we work around the VM's internet limitations while still being able to test the actual system.
