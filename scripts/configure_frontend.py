"""Write the static frontend's API base URL for local or Render builds."""

import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
configured = os.getenv("JAVA_API_URL", "http://localhost:8080").strip().rstrip("/")
if not configured.startswith(("http://", "https://")):
    configured = f"https://{configured}"
if configured.endswith("/api"):
    api_url = configured
else:
    api_url = f"{configured}/api"

output = ROOT / "frontend" / "js" / "runtime-config.js"
output.write_text(
    "// Generated during the static-site build.\n"
    f"window.MAILGUARD_API = {json.dumps(api_url)};\n",
    encoding="utf-8",
)
print(f"Configured frontend API base: {api_url}")
