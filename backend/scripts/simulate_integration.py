"""Exercise Cerviqon's real risk API using synthetic client-side transaction facts."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
import uuid

SCENARIOS = {
    "cold-start": {"amount": 12000, "account_id": "synthetic-acct-cold-001", "beneficiary_id": "synthetic-ben-new-001", "device_id": "synthetic-device-new-001"},
    "established": {"amount": 12000, "account_id": "synthetic-acct-established-001", "beneficiary_id": "synthetic-ben-established-001", "device_id": "synthetic-device-established-001"},
    "high-value": {"amount": 850000, "account_id": "synthetic-acct-high-001", "beneficiary_id": "synthetic-ben-new-002", "device_id": "synthetic-device-new-002"},
}


def submit(base_url: str, api_key: str, payload: dict, timeout: float) -> dict:
    request = urllib.request.Request(
        base_url.rstrip("/") + "/v1/risk/score",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-API-Key": api_key, "X-Request-ID": "sim-" + uuid.uuid4().hex},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Risk API returned HTTP {exc.code}: {detail}") from None
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Risk API connection failed or timed out: {exc}") from None
    try:
        result = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise RuntimeError("Risk API returned invalid JSON") from None
    if not isinstance(result, dict):
        raise RuntimeError("Risk API returned an unexpected response")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=SCENARIOS, default="cold-start")
    parser.add_argument("--transaction-id", default=None, help="Synthetic idempotency key; generated when omitted")
    parser.add_argument("--repeat", action="store_true", help="Submit identical facts twice and verify idempotent replay")
    parser.add_argument("--timeout", type=float, default=8.0)
    args = parser.parse_args()
    base_url = os.environ.get("CERVIQON_API_URL", "http://127.0.0.1:8000")
    api_key = os.environ.get("CERVIQON_API_KEY", "")
    if not api_key:
        print("Set CERVIQON_API_KEY to a development/test key configured on the API.", file=sys.stderr)
        return 2
    transaction_id = args.transaction_id or "synthetic-txn-" + uuid.uuid4().hex
    suffix = hashlib.sha256(transaction_id.encode("utf-8")).hexdigest()[:12]
    fixture = SCENARIOS[args.scenario]
    payload = {"transaction_id": transaction_id, "account_id": fixture["account_id"] + "-" + suffix,
        "amount": fixture["amount"], "beneficiary_id": fixture["beneficiary_id"] + "-" + suffix,
        "device_id": fixture["device_id"] + "-" + suffix, "currency": "NGN", "channel": "api"}
    try:
        first = submit(base_url, api_key, payload, args.timeout)
        print(json.dumps({"scenario": args.scenario, "response": first}, indent=2))
        if args.repeat:
            second = submit(base_url, api_key, payload, args.timeout)
            if first.get("assessment_id") != second.get("assessment_id"):
                raise RuntimeError("Repeated request returned a different assessment_id")
            print("Identical retry returned the same assessment_id.")
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
