# ARU Agent Runtime

A minimal deterministic agent runtime where every tool call is certified by [ARU](https://aru-runtime.com) before execution.

Natural language in → certified working code out.

---

## What it does

Every action an AI agent takes — reading a file, writing code, executing a script — is certified by the ARU API before it runs. Every certification is hashed and logged to a tamper-evident ledger you can audit.

```
python cli.py "build a bitcoin price tracker, save and run it"
```

```
=== Steps ===
1. [OK] write_file → btc_price.py       cert_mnsmp0xs
2. [OK] run_code   → btc_price.py       cert_mnsmp5fb
```

---

## Quick start

```bash
git clone https://github.com/mhaji6294-stack/aru-agent-runtime
cd aru-agent-runtime
pip install anthropic requests

export ANTHROPIC_API_KEY=sk-ant-...
export ARU_API_KEY=aru_live_...

python cli.py "write hello world to test.txt" --steps
```

Get your ARU API key at [aru-runtime.com](https://aru-runtime.com) — 100 free certifications/month.

---

## CrewAI integration

Add ARU certification to any CrewAI agent in 2 lines:

```python
from aru_crewai import ARUToolWrapper

certified_tool = ARUToolWrapper(your_existing_tool)
agent = Agent(..., tools=[certified_tool])
```

Every tool call your agent makes is now certified before execution and logged with a SHA256 hash.

---

## Dashboard

Open `aru_dashboard.html` in any browser. Drag and drop your `aru_cert_ledger.jsonl` to view all certifications.

No server. No login. Works offline.

---

## File structure

```
cli.py              — run any task from the command line
agent.py            — Claude-powered loop with memory and retry
tools.py            — read_file / write_file / run_code
aru_hook.py         — certify every tool call via ARU API
aru_crewai.py       — drop-in CrewAI integration
aru_dashboard.html  — local certification viewer
workspace/
  memory.md         — persists context across sessions
  logs/             — YYYY-MM-DD.jsonl run logs
  cert_ledger.jsonl — tamper-evident certification log
```

---

## How certification works

1. Agent decides to call a tool
2. `aru_hook.py` sends the intent + constraints to ARU API
3. ARU certifies or rejects
4. If approved — tool executes, cert ID + SHA256 hash logged
5. If rejected — agent retries with revised approach (max 3 retries)

The cert ledger is append-only. Each entry contains a SHA256 hash of the certification response — any tampering is detectable.

---

## Why

AI agents are taking real actions in production. Without a certification layer, there is no way to prove an action was authorized, no audit trail for compliance, and no mechanism to block unauthorized behavior before it executes.

ARU is the runtime layer that makes agent actions provable.

---

Built on [ARU](https://aru-runtime.com) · [@Mhaji62](https://x.com/Mhaji62)
