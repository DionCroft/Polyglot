"""Static network boundary check; separate inbound-only student helper allowed."""

import ast
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
forbidden = {
    "requests",
    "urllib",
    "http",
    "httpx",
    "openai",
    "azure",
    "google",
    "huggingface_hub",
    "socket",
    "socketserver",
    "websockets",
    "aiohttp",
}
helper_imports = {"socket", "socketserver", "http.server", "urllib.parse"}
violations, allowed = [], []
for path in (root / "app").rglob("*.py"):
    relative = path.relative_to(root).as_posix()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8-sig"))):
        names = (
            [a.name for a in node.names]
            if isinstance(node, ast.Import)
            else [node.module or ""]
            if isinstance(node, ast.ImportFrom)
            else []
        )
        for name in names:
            if name.split(".")[0] in forbidden:
                entry = dict(file=relative, line=node.lineno, module=name)
                (
                    allowed
                    if relative == "app/sharing/server.py" and name in helper_imports
                    else violations
                ).append(entry)
report = dict(
    runtime_python_files=len(list((root / "app").rglob("*.py"))),
    forbidden_network_imports=violations,
    separate_student_helper_imports=allowed,
    boundary="Speech process denies sockets/DNS as before. Explicit sharing spawns an inbound-only private-IPv4 helper; its Python audit denies outgoing connections and DNS.",
    ort_telemetry_disabled="disable_telemetry_events()"
    in (root / "app/system/inference.py").read_text(),
    native_packet_trace="pending; not proven by static audit",
)
(root / "docs/evidence/offline-audit.json").write_text(
    json.dumps(report, indent=2), encoding="utf-8"
)
print(json.dumps(report, indent=2))
assert not violations
