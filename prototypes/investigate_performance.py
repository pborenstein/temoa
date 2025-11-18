#!/usr/bin/env python3
"""
Phase 0.1 Follow-up: Investigate Performance Bottleneck

This script helps identify WHERE the 3+ seconds is being spent.
"""

import subprocess
import time
from pathlib import Path

SYNTHESIS_PATH = Path("old-ideas/synthesis/")


def test_direct_synthesis():
    """Test running Synthesis directly (not via script)"""
    print("\n" + "="*60)
    print("Test 1: Direct Synthesis Call (baseline)")
    print("="*60)

    queries = ["semantic search", "AI agents", "productivity"]
    times = []

    for query in queries:
        print(f"\nQuery: '{query}'")
        start = time.time()

        result = subprocess.run(
            ["uv", "run", "main.py", "search", query, "--json"],
            cwd=SYNTHESIS_PATH,
            capture_output=True,
            text=True,
            timeout=10
        )

        elapsed = time.time() - start
        times.append(elapsed)
        print(f"  Time: {elapsed:.3f}s")
        print(f"  Success: {result.returncode == 0}")

    print(f"\nAverage: {sum(times)/len(times):.3f}s")
    return times


def test_subprocess_overhead():
    """Test just the subprocess overhead (no actual search)"""
    print("\n" + "="*60)
    print("Test 2: Subprocess Overhead (uv --version)")
    print("="*60)

    times = []
    for i in range(5):
        start = time.time()
        subprocess.run(
            ["uv", "--version"],
            cwd=SYNTHESIS_PATH,
            capture_output=True,
            text=True
        )
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"  Run {i+1}: {elapsed:.3f}s")

    avg = sum(times) / len(times)
    print(f"\nAverage subprocess overhead: {avg:.3f}s")
    return avg


def test_python_startup():
    """Test Python/uv startup time"""
    print("\n" + "="*60)
    print("Test 3: Python Startup Time (uv run python --version)")
    print("="*60)

    times = []
    for i in range(5):
        start = time.time()
        subprocess.run(
            ["uv", "run", "python", "--version"],
            cwd=SYNTHESIS_PATH,
            capture_output=True,
            text=True
        )
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"  Run {i+1}: {elapsed:.3f}s")

    avg = sum(times) / len(times)
    print(f"\nAverage Python startup: {avg:.3f}s")
    return avg


def test_synthesis_stats():
    """Test Synthesis stats (simpler than search)"""
    print("\n" + "="*60)
    print("Test 4: Synthesis Stats (simpler operation)")
    print("="*60)

    times = []
    for i in range(3):
        start = time.time()
        result = subprocess.run(
            ["uv", "run", "main.py", "stats"],
            cwd=SYNTHESIS_PATH,
            capture_output=True,
            text=True
        )
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"  Run {i+1}: {elapsed:.3f}s")

    avg = sum(times) / len(times)
    print(f"\nAverage stats time: {avg:.3f}s")
    return avg


def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║  Performance Investigation                                   ║
║  Goal: Find out where the 3+ seconds is being spent          ║
╚══════════════════════════════════════════════════════════════╝
""")

    # Test 1: Direct Synthesis (baseline)
    search_times = test_direct_synthesis()

    # Test 2: Subprocess overhead
    subprocess_overhead = test_subprocess_overhead()

    # Test 3: Python startup
    python_startup = test_python_startup()

    # Test 4: Stats (simpler operation)
    stats_time = test_synthesis_stats()

    # Analysis
    print("\n" + "="*60)
    print("ANALYSIS")
    print("="*60)

    avg_search = sum(search_times) / len(search_times)

    print(f"\nAverage search time:     {avg_search:.3f}s")
    print(f"Subprocess overhead:     {subprocess_overhead:.3f}s ({subprocess_overhead/avg_search*100:.1f}%)")
    print(f"Python startup:          {python_startup:.3f}s ({python_startup/avg_search*100:.1f}%)")
    print(f"Stats operation:         {stats_time:.3f}s")
    print(f"\nEstimated actual search: {avg_search - python_startup:.3f}s")

    print("\n" + "="*60)
    print("CONCLUSIONS")
    print("="*60)

    if python_startup > 2.0:
        print("\n⚠️  Python startup is VERY slow (>2s)")
        print("    This is likely the main bottleneck.")
        print("    Each subprocess call pays this startup cost.")
        print("\n    Mitigation: Keep Synthesis running as daemon/service")
    elif avg_search - python_startup > 1.0:
        print("\n⚠️  Synthesis search itself is slow (>1s after startup)")
        print("    The actual search operation is the bottleneck.")
        print("\n    Mitigation: Optimize Synthesis, use faster model, or cache")
    else:
        print("\n✓ Both startup and search contribute to slowness")
        print("  Need combined approach: daemon + optimization")

    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print("\n1. Test against REAL vault (not test-vault)")
    print("   cd ~/.obsidian/vaults/main/.tools/synthesis")
    print("   uv run main.py process  # if not already processed")
    print("   time uv run main.py search 'your query' --json")
    print("\n2. If real vault is also slow, consider:")
    print("   - Running Synthesis as a daemon (avoid startup cost)")
    print("   - Server-side caching (avoid repeated searches)")
    print("   - Faster model (trade quality for speed)")
    print("\n3. Report findings back to determine Phase 1 approach")


if __name__ == "__main__":
    main()
