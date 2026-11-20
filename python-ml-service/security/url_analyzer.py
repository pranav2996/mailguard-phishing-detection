import ipaddress
import re
from urllib.parse import urlparse

URL_RE = re.compile(r"(?i)\b(?:https?://|www\.)[^\s<>\"']+")
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "buff.ly", "cutt.ly"}

def analyze_urls(text):
    results = []
    for raw in URL_RE.findall(str(text)):
        url = raw.rstrip(".,;:!?)]}")
        candidate = url if "://" in url else "http://" + url
        try:
            parsed = urlparse(candidate)
            host = (parsed.hostname or "").lower()
        except ValueError:
            results.append({"url": url, "host": "", "scheme": "", "length": len(url), "indicators": ["Malformed URL"]})
            continue
        indicators = []
        try:
            ipaddress.ip_address(host)
            indicators.append("IP address used as host")
        except ValueError:
            pass
        if host in SHORTENERS: indicators.append("URL shortener domain")
        if len(url) > 100: indicators.append("Unusually long URL")
        if "@" in parsed.netloc: indicators.append("User information embedded in URL")
        if host.count("-") >= 3: indicators.append("Multiple hyphens in host")
        if host.count(".") >= 4: indicators.append("Unusually deep subdomain")
        if re.search(r"(?:paypa1|micros0ft|g00gle|app1e)", host): indicators.append("Possible lookalike brand spelling")
        results.append({"url": url, "host": host, "scheme": parsed.scheme, "length": len(url), "indicators": indicators})
    return results
