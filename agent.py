import os, anthropic
from tools import TOOLS_SCHEMA, dispatch
from aru_hook import verify
MAX_RETRIES = 3
WORKSPACE = os.path.join(os.path.dirname(__file__), "workspace")
MEMORY_PATH = os.path.join(WORKSPACE, "memory.md")
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
def load_memory():
    if os.path.exists(MEMORY_PATH):
        with open(MEMORY_PATH, "r", encoding="utf-8") as f: return f.read()
    return ""
def save_memory(content):
    os.makedirs(WORKSPACE, exist_ok=True)
    with open(MEMORY_PATH, "w", encoding="utf-8") as f: f.write(content)
def run(task):
    memory = load_memory()
    system = "You are a deterministic agent. Complete tasks using only the tools provided. After finishing, summarize what you did in 2-3 sentences."
    if memory: system += f"\n\n## Memory:\n{memory}"
    history = [{"role": "user", "content": task}]
    retries, steps = 0, []
    while True:
        response = client.messages.create(model="claude-opus-4-5", max_tokens=4096, system=system, tools=TOOLS_SCHEMA, messages=history)
        history.append({"role": "assistant", "content": response.content})
        if response.stop_reason == "end_turn":
            final = "".join(b.text for b in response.content if hasattr(b, "text"))
            save_memory(f"## Last session\n{final[:500]}")
            return {"output": final, "steps": steps, "memory_saved": True}
        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type != "tool_use": continue
                approved, reason = verify({"id": block.id, "name": block.name, "input": block.input})
                step = {"tool": block.name, "input": block.input, "approved": approved, "reason": reason}
                if approved:
                    try:
                        result = dispatch(block.name, block.input)
                        step["result"] = result
                        tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})
                    except Exception as e:
                        step["result"] = str(e)
                        tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": str(e), "is_error": True})
                else:
                    retries += 1
                    step["result"] = f"REJECTED: {reason}"
                    tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": f"ARU rejected: {reason}. Revise.", "is_error": True})
                steps.append(step)
            history.append({"role": "user", "content": tool_results})
            if retries >= MAX_RETRIES: return {"output": f"Aborted after {MAX_RETRIES} ARU rejections.", "steps": steps, "memory_saved": False}
        else:
            return {"output": f"Unexpected stop: {response.stop_reason}", "steps": steps, "memory_saved": False}
