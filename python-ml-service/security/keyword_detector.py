import re

PATTERNS = {
 "urgent": r"\b(?:urgent|immediately|act now|expires today|final warning|within 24 hours)\b",
 "credential_request": r"\b(?:password|login credentials|verify your account|confirm your identity|sign in|one[- ]time code|security code)\b",
 "financial_request": r"\b(?:wire transfer|bank account|credit card|payment details|billing information|invoice overdue|gift card)\b",
 "threat_or_reward": r"\b(?:account suspended|account will be closed|you have won|prize claim|legal action)\b",
}

def detect_keywords(text):
    low = str(text).lower()
    return {category: sorted({m.group(0) for m in re.finditer(pattern, low)}) for category, pattern in PATTERNS.items() if re.search(pattern, low)}
