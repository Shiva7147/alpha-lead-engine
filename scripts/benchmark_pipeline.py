"""Benchmarking script evaluating multi-engine discovery latency, parsing throughput, and MX checks.
"""

import time
from alpha_lead_engine.auditor.syntax_and_mx_validator import SyntaxAndMXValidator


def run_benchmark():
    print("=" * 60)
    print("⚡ ALPHA LEAD ENGINE - Performance & Latency Benchmark")
    print("=" * 60)

    validator = SyntaxAndMXValidator()
    test_domains = [
        "google.com", "microsoft.com", "apple.com", "amazon.com", "github.com",
        "invalid-domain-that-does-not-exist-12345.com", "example.com"
    ]

    print(f"\n[Benchmarking DNS / MX Validation across {len(test_domains)} domains]...")
    start_t = time.perf_counter()
    for d in test_domains:
        valid, reason = validator.validate_email(f"test@{d}")
        print(f"  {d:35} -> MX Valid: {str(valid):5} ({reason[:35]})")
    mx_elapsed = time.perf_counter() - start_t
    print(f"✔ MX Validation Time: {mx_elapsed:.3f}s (Average: {mx_elapsed / len(test_domains) * 1000:.1f}ms / domain)")
    print("=" * 60)


if __name__ == "__main__":
    run_benchmark()
