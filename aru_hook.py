import os, requests, json, hashlib
from datetime import datetime, timezone

ARU_API_URL = os.environ.get("ARU_API_URL", "https://aru-runtime.com/api/v1/certify")
ARU_API_KEY = os.environ.get("ARU_API_KEY", "")
WORKSPACE = os.path.join(os.path.dirname(__file__), "workspace")
LEDGER_PATH = os.path.join(WORKSPACE, "cert_ledger.jsonl")


def hash_cert(data: dict) -> str:
    raw = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def append_ledger(entry: dict):
    os.makedirs(WORKSPACE, exist_ok=True)
    with open(LEDGER_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def verify(tool_call: dict) -> tuple:
    if not ARU_API_KEY:
        raise RuntimeError("ARU_API_KEY not set.")

    intent = f"Execute tool '{tool_call['name']}' on path '{tool_call['input'].get('path', 'unknown')}'"
    payload = {
        "intent": intent,
        "constraints": [
            {"rule": "Only read/write within workspace/", "severity": "hard"},
            {"rule": "No path traversal allowed", "severity": "hard"}
        ]
    }

    try:
        resp = requests.post(
            ARU_API_URL,
            json=payload,
            headers={"Authorization": f"Bearer {ARU_API_KEY}", "Content-Type": "application/json"},
            timeout=15
        )
        resp.raise_for_status()
        data = resp.json()

        approved = data.get("status") == "SUCCESS" and data.get("certification", {}).get("status") in ("CERTIFIED", "REFINED")
        reason = data.get("certification", {}).get("output", "No reason.")
        cert_id = data.get("certification", {}).get("id", "unknown")

        ledger_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cert_id": cert_id,
            "tool": tool_call["name"],
            "input_path": tool_call["input"].get("path", "unknown"),
            "approved": approved,
            "reason": reason,
            "hash": hash_cert({
                "cert_id": cert_id,
                "tool": tool_call["name"],
                "approved": approved,
                "intent": intent,
                "aru_status": data.get("status"),
                "cert_status": data.get("certification", {}).get("status")
            })
        }

        append_ledger(ledger_entry)
        return approved, reason

    except requests.exceptions.RequestException as e:
        return False, f"ARU unreachable: {str(e)}"
