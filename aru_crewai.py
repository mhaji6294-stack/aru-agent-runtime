import os, json, hashlib, requests
from datetime import datetime, timezone
from typing import Any
from pydantic import Field

try:
    from crewai.tools import BaseTool
except ImportError:
    raise ImportError("crewai not installed. Run: pip install crewai")

ARU_API_URL = os.environ.get("ARU_API_URL", "https://aru-runtime.com/api/v1/certify")
ARU_API_KEY = os.environ.get("ARU_API_KEY", "")
ARU_LEDGER = os.environ.get("ARU_LEDGER_PATH", "aru_cert_ledger.jsonl")

def _hash_cert(data):
    raw = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()

def _append_ledger(entry):
    with open(ARU_LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def _certify(tool_name, tool_input):
    if not ARU_API_KEY:
        raise RuntimeError("ARU_API_KEY not set.")
    payload = {
        "intent": f"Execute CrewAI tool '{tool_name}' with input: {str(tool_input)[:200]}",
        "constraints": [
            {"rule": "Tool must serve the agent task intent", "severity": "hard"},
            {"rule": "No unauthorized data exfiltration", "severity": "hard"},
            {"rule": "Action must be reversible or low-risk", "severity": "soft"}
        ]
    }
    try:
        resp = requests.post(ARU_API_URL, json=payload, headers={"Authorization": f"Bearer {ARU_API_KEY}", "Content-Type": "application/json"}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        approved = data.get("status") == "SUCCESS" and data.get("certification", {}).get("status") in ("CERTIFIED", "REFINED")
        reason = data.get("certification", {}).get("output", "No reason.")
        cert_id = data.get("certification", {}).get("id", "unknown")
        _append_ledger({"timestamp": datetime.now(timezone.utc).isoformat(), "cert_id": cert_id, "tool": tool_name, "approved": approved, "hash": _hash_cert({"cert_id": cert_id, "tool": tool_name, "approved": approved})})
        return approved, reason, cert_id
    except requests.exceptions.RequestException as e:
        return False, f"ARU unreachable: {str(e)}", "none"

class ARUToolWrapper(BaseTool):
    name: str = "ARU Certified Tool"
    description: str = "ARU-certified tool wrapper"
    wrapped_tool: Any = Field(default=None, exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, tool, **kwargs):
        super().__init__(name=f"[ARU] {tool.name}", description=tool.description, wrapped_tool=tool, **kwargs)

    def _run(self, **kwargs):
        approved, reason, cert_id = _certify(self.wrapped_tool.name, kwargs)
        if not approved:
            return f"[ARU REJECTED] cert_id={cert_id} | Reason: {reason}"
        return f"[ARU:{cert_id}] {self.wrapped_tool._run(**kwargs)}"

class ARUCertifiedToolkit:
    def __init__(self, tools):
        self.tools = [ARUToolWrapper(t) for t in tools]
    def __iter__(self):
        return iter(self.tools)

def aru_certified(func):
    def wrapper(*args, **kwargs):
        tool_name = getattr(func, "name", getattr(func, "__name__", "unknown_tool"))
        approved, reason, cert_id = _certify(tool_name, args[0] if args else kwargs)
        if not approved:
            return f"[ARU REJECTED] cert_id={cert_id} | Reason: {reason}"
        result = func(*args, **kwargs)
        return f"[ARU:{cert_id}] {result}"
    try:
        wrapper.__name__ = getattr(func, "__name__", "aru_tool")
        wrapper.__doc__ = getattr(func, "__doc__", "")
    except Exception:
        pass
    return wrapper
