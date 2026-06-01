"""
BEATEK_ROCm — gfx1100 End-to-End Inference Validation Test
============================================================
Hardware:  AMD Radeon RX 7900 GRE · gfx1100 · Windows 11
Purpose:   Confirm the ROCm KV cache patch resolves the crash and
           GPU inference is running (not CPU fallback).

Usage:
    python gfx1100_inference_test.py --endpoint http://localhost:8080

Exit codes:
    0 — All tests passed, GPU inference confirmed
    1 — One or more tests failed

Requires:
    pip install requests
"""

import argparse
import sys
import time
import json
import requests


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_ENDPOINT = "http://localhost:8080"
TIMEOUT_SECONDS  = 120      # generous timeout for first-token latency
MAX_FIRST_TOKEN  = 10.0     # fail if first token takes longer than this (s)
TARGET_BACKEND   = "GPU"    # expected inference backend label in response


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def check_health(endpoint: str) -> bool:
    """Verify the llama-server is up and responsive."""
    url = f"{endpoint}/health"
    try:
        r = requests.get(url, timeout=10)
        return r.status_code == 200
    except requests.RequestException as e:
        print(f"  [ERROR] Health check failed: {e}")
        return False


def run_inference(endpoint: str, prompt: str) -> dict:
    """
    Send a single inference request to the OpenAI-compatible endpoint.
    Returns the full response dict (or raises on failure).
    """
    url = f"{endpoint}/v1/chat/completions"
    payload = {
        "model": "llama",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 64,
        "temperature": 0.0,
        "stream": False,
    }
    headers = {"Content-Type": "application/json"}

    start = time.monotonic()
    response = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT_SECONDS)
    elapsed = time.monotonic() - start

    response.raise_for_status()
    data = response.json()
    data["_elapsed_seconds"] = elapsed
    return data


def get_model_info(endpoint: str) -> dict:
    """Fetch /props or /v1/models to check backend metadata."""
    try:
        r = requests.get(f"{endpoint}/props", timeout=10)
        if r.status_code == 200:
            return r.json()
    except requests.RequestException:
        pass
    return {}


# ---------------------------------------------------------------------------
# Individual test cases
# ---------------------------------------------------------------------------

def test_server_health(endpoint: str) -> bool:
    print("TEST: Server health check ...")
    ok = check_health(endpoint)
    if ok:
        print("  [PASS] Server is up and responding")
    else:
        print("  [FAIL] Server is not responding — is llama-server running?")
    return ok


def test_inference_completes(endpoint: str) -> tuple[bool, dict]:
    """Confirm inference returns a response without crashing (exit code 2)."""
    print("TEST: Inference completes without crash ...")
    try:
        data = run_inference(endpoint, "What is 2 + 2? Answer with just the number.")
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        elapsed = data.get("_elapsed_seconds", 0)
        print(f"  [PASS] Inference completed in {elapsed:.2f}s")
        print(f"  [INFO] Response: {content.strip()!r}")
        return True, data
    except requests.RequestException as e:
        print(f"  [FAIL] Inference request failed: {e}")
        return False, {}


def test_first_token_latency(data: dict) -> bool:
    """Fail if first token latency exceeds threshold (suggests CPU fallback)."""
    print("TEST: First-token latency check ...")
    elapsed = data.get("_elapsed_seconds", 9999)
    if elapsed <= MAX_FIRST_TOKEN:
        print(f"  [PASS] Latency {elapsed:.2f}s ≤ {MAX_FIRST_TOKEN}s threshold")
        return True
    else:
        print(f"  [WARN] Latency {elapsed:.2f}s > {MAX_FIRST_TOKEN}s — possible CPU fallback")
        print(f"         (CPU mode latency is typically 20–60s on first token)")
        return False


def test_no_cpu_fallback(endpoint: str) -> bool:
    """
    Check server props/metadata for backend indicators.
    llama-server does not always expose backend directly — we use latency
    as the primary signal and log any metadata we can find.
    """
    print("TEST: GPU backend active (no CPU fallback) ...")
    props = get_model_info(endpoint)
    if props:
        print(f"  [INFO] Server props: {json.dumps(props, indent=4)}")
    # Without explicit backend field, we rely on latency (tested separately)
    # This test is informational — mark pass and let latency test fail if needed
    print("  [INFO] Verify 'ROCm0' appears in llama-server startup logs")
    return True


def test_multiple_requests(endpoint: str, count: int = 3) -> bool:
    """Run N requests to confirm stability — no intermittent crashes."""
    print(f"TEST: Stability check ({count} consecutive requests) ...")
    prompts = [
        "What color is the sky?",
        "Name one planet in our solar system.",
        "What is the capital of France?",
    ]
    for i, prompt in enumerate(prompts[:count], 1):
        try:
            data = run_inference(endpoint, prompt)
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"  [PASS] Request {i}/{count}: {content.strip()!r}")
        except requests.RequestException as e:
            print(f"  [FAIL] Request {i}/{count} failed: {e}")
            return False
    return True


# ---------------------------------------------------------------------------
# Main test runner
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="BEATEK gfx1100 inference validation")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT,
                        help="llama-server base URL (default: %(default)s)")
    args = parser.parse_args()

    endpoint = args.endpoint.rstrip("/")
    print(f"BEATEK_ROCm — gfx1100 Inference Validation")
    print(f"Endpoint: {endpoint}")
    print("=" * 60)

    results = []

    # 1. Health
    ok = test_server_health(endpoint)
    results.append(("Server health", ok))
    if not ok:
        print("\n[ABORT] Server not reachable. Start llama-server and retry.")
        sys.exit(1)

    # 2. Inference completes
    ok, inference_data = test_inference_completes(endpoint)
    results.append(("Inference completes", ok))

    # 3. Latency (GPU signal)
    if inference_data:
        ok = test_first_token_latency(inference_data)
        results.append(("First-token latency", ok))

    # 4. Backend check (informational)
    ok = test_no_cpu_fallback(endpoint)
    results.append(("Backend metadata", ok))

    # 5. Stability
    ok = test_multiple_requests(endpoint)
    results.append(("Stability (3 requests)", ok))

    # Summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        mark = "✅" if passed else "❌"
        print(f"  {mark} [{status}] {name}")
        if not passed:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED — GPU inference on gfx1100 is working")
        sys.exit(0)
    else:
        print("❌ ONE OR MORE TESTS FAILED — check output above")
        sys.exit(1)


if __name__ == "__main__":
    main()
