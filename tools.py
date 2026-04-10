import os, subprocess, sys
TOOLS_SCHEMA = [
    {"name":"read_file","description":"Read a file from workspace.","input_schema":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}},
    {"name":"write_file","description":"Write a file to workspace.","input_schema":{"type":"object","properties":{"path":{"type":"string"},"content":{"type":"string"}},"required":["path","content"]}},
    {"name":"run_code","description":"Execute a Python file in workspace and return output.","input_schema":{"type":"object","properties":{"path":{"type":"string","description":"Path to .py file in workspace to execute"}},"required":["path"]}}
]
WORKSPACE = os.path.join(os.path.dirname(__file__), "workspace")
def read_file(path):
    full = os.path.join(WORKSPACE, path)
    if not os.path.abspath(full).startswith(os.path.abspath(WORKSPACE)): raise PermissionError("Path traversal denied.")
    with open(full, "r", encoding="utf-8") as f: return f.read()
def write_file(path, content):
    full = os.path.join(WORKSPACE, path)
    if not os.path.abspath(full).startswith(os.path.abspath(WORKSPACE)): raise PermissionError("Path traversal denied.")
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f: f.write(content)
    return f"Written: {path}"
def run_code(path):
    full = os.path.join(WORKSPACE, path)
    if not os.path.abspath(full).startswith(os.path.abspath(WORKSPACE)): raise PermissionError("Path traversal denied.")
    if not os.path.exists(full): raise FileNotFoundError(f"File not found: {path}")
    result = subprocess.run([sys.executable, full], capture_output=True, text=True, timeout=30, cwd=WORKSPACE)
    output = result.stdout + result.stderr
    return output[:3000] if output else "No output."
def dispatch(tool_name, tool_input):
    if tool_name == "read_file": return read_file(tool_input["path"])
    elif tool_name == "write_file": return write_file(tool_input["path"], tool_input["content"])
    elif tool_name == "run_code": return run_code(tool_input["path"])
    else: raise ValueError(f"Unknown tool: {tool_name}")
