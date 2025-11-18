#!/usr/bin/env python3
"""
Phase 0.1: Test Synthesis Performance

This script tests Synthesis search performance and gathers baseline metrics.
Run this on your machine with internet access to download models and test.

Usage:
    cd /path/to/temoa
    python prototypes/test_synthesis_performance.py
"""

import subprocess
import json
import time
from pathlib import Path

# Adjust this to point to your actual Synthesis location
# Could be: old-ideas/synthesis/ OR ~/.obsidian/vaults/main/.tools/synthesis
SYNTHESIS_PATH = Path("old-ideas/synthesis/")


def run_synthesis_command(args: list, timeout: int = 30) -> tuple[bool, str, str, float]:
    """
    Run a Synthesis command and measure execution time.

    Returns: (success, stdout, stderr, elapsed_time)
    """
    start = time.time()

    try:
        result = subprocess.run(
            ["uv", "run", "main.py"] + args,
            cwd=SYNTHESIS_PATH,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        elapsed = time.time() - start
        return (result.returncode == 0, result.stdout, result.stderr, elapsed)
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        return (False, "", f"Command timed out after {timeout}s", elapsed)


def test_search_performance():
    """Test a single search query and print results."""
    query = "semantic search"
    run_name = "search"

    print(f"\n{'='*60}")
    print(f"Test: {run_name}")
    print(f"Query: '{query}'")
    print(f"{'='*60}")

    success, stdout, stderr, elapsed = run_synthesis_command(
        ["search", query, "--json"]
    )

    print(f"Time: {elapsed:.3f}s")
    print(f"Success: {success}")

    if success:
        try:
            data = json.loads(stdout)
            results = data.get('results', [])
            print(f"Results: {len(results)} matches")

            if results:
                print(f"\nTop 3 results:")
                for i, result in enumerate(results[:3], 1):
                    print(f"  {i}. {result.get('title', 'Untitled')}")
                    print(f"     Score: {result.get('similarity_score', 0):.3f}")
                    print(f"     Path: {result.get('relative_path', 'unknown')}")
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse JSON: {e}")
            print(f"Output: {stdout[:200]}...")
    else:
        print(f"ERROR: {stderr}")

    return elapsed


def test_stats():
    """Get vault statistics from Synthesis."""
    print(f"\n{'='*60}")
    print(f"Test: Vault Statistics")
    print(f"{'='*60}")

    success, stdout, stderr, elapsed = run_synthesis_command(["stats"])

    print(f"Time: {elapsed:.3f}s")

    if success:
        print(stdout)
    else:
        print(f"ERROR: {stderr}")


def test_models():
    """List available models."""
    print(f"\n{'='*60}")
    print(f"Test: Available Models")
    print(f"{'='*60}")

    success, stdout, stderr, elapsed = run_synthesis_command(["models"])

    if success:
        print(stdout)
    else:
        print(f"ERROR: {stderr}")


def test_archaeology():
    """Test temporal archaeology feature."""
    topic = "artificial intelligence"

    print(f"\n{'='*60}")
    print(f"Test: Archaeology - '{topic}'")
    print(f"{'='*60}")

    success, stdout, stderr, elapsed = run_synthesis_command(
        ["archaeology", topic, "--json"]
    )

    print(f"Time: {elapsed:.3f}s")

    if success:
        try:
            data = json.loads(stdout)
            print(f"Temporal analysis completed")
            # Could print summary of results if needed
        except json.JSONDecodeError:
            print(stdout[:500])
    else:
        print(f"ERROR: {stderr}")


def main():
    """Run all Phase 0.1 tests."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║  Phase 0.1: Synthesis Performance Testing                   ║
║  Testing location: {synthesis_path}
╚══════════════════════════════════════════════════════════════╝
""".format(synthesis_path=SYNTHESIS_PATH))

    # Check if Synthesis directory exists
    if not SYNTHESIS_PATH.exists():
        print(f"ERROR: Synthesis directory not found at {SYNTHESIS_PATH}")
        print(f"Please update SYNTHESIS_PATH in this script to point to your Synthesis installation")
        return

    times = []

    # Test 1: Get models (will download on first run)
    print("\n📦 Checking available models (may download on first run)...")
    test_models()

    # Test 2: Get stats
    print("\n📊 Getting vault statistics...")
    test_stats()

    # Test 3: Cold start search
    print("\n❄️  COLD START TEST (first search after startup)")
    t1 = test_search_performance("semantic search", "Cold Start")
    times.append(("Cold Start", t1))

    # Test 4-6: Warm searches
    print("\n🔥 WARM START TESTS (subsequent searches)")
    t2 = test_search_performance("AI agents", "Warm #1")
    times.append(("Warm #1", t2))

    t3 = test_search_performance("productivity systems", "Warm #2")
    times.append(("Warm #2", t3))

    t4 = test_search_performance("obsidian plugins", "Warm #3")
    times.append(("Warm #3", t4))

    # Test 7: Different model
    print("\n🔬 TESTING DIFFERENT MODEL (all-mpnet-base-v2)")
    success, stdout, stderr, elapsed = run_synthesis_command(
        ["search", "machine learning", "--model", "all-mpnet-base-v2", "--json"]
    )
    print(f"Time: {elapsed:.3f}s")
    if success:
        try:
            data = json.loads(stdout)
            print(f"Results: {len(data.get('results', []))} matches")
        except:
            pass
    times.append(("Different Model", elapsed))

    # Test 8: Archaeology
    print("\n🏺 TESTING ARCHAEOLOGY")
    test_archaeology("artificial intelligence")

    # Summary
    print(f"\n{'='*60}")
    print(f"PERFORMANCE SUMMARY")
    print(f"{'='*60}")

    for name, t in times:
        print(f"{name:20s}: {t:6.3f}s")

    warm_times = [t for name, t in times if "Warm" in name]
    if warm_times:
        avg_warm = sum(warm_times) / len(warm_times)
        print(f"\nAverage warm search: {avg_warm:.3f}s")
        print(f"Min warm search:     {min(warm_times):.3f}s")
        print(f"Max warm search:     {max(warm_times):.3f}s")

    print(f"\n{'='*60}")
    print("QUESTIONS TO ANSWER:")
    print(f"{'='*60}")
    print("1. Are daily notes indexed? (check stats output)")
    print("2. Is search < 1s for warm queries? (target < 500ms ideal)")
    print("3. Did model download work on first run?")
    print("4. What's the file count vs your actual vault?")
    print("\nPlease report these findings back to continue Phase 0.")


if __name__ == "__main__":
    main()
