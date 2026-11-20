"""Write the static frontend's API base URL for local or Render builds."""

import json
import os
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
is_render = bool(os.getenv("RENDER_SERVICE_ID"))
configured = os.getenv("JAVA_API_URL", "").strip().rstrip("/")
if is_render and not configured:
    raise SystemExit("JAVA_API_URL must be set for a Render frontend build.")
if not configured:
    configured = "http://localhost:8080"
if not configured.startswith(("http://", "https://")):
    configured = f"https://{configured}"
parsed = urlparse(configured)
if parsed.scheme not in {"http", "https"} or not parsed.hostname:
    raise SystemExit("JAVA_API_URL must be an absolute HTTP(S) URL or hostname.")
if parsed.username or parsed.password:
    raise SystemExit("JAVA_API_URL must not contain credentials.")
if is_render and parsed.hostname.lower() in {"localhost", "127.0.0.1", "::1"}:
    raise SystemExit("JAVA_API_URL cannot point to localhost in a Render frontend build.")
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
