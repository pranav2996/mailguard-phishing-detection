def summarize_risk(prediction, keyword_groups, urls):
    flagged_urls = sum(bool(u["indicators"]) for u in urls)
    evidence_count = len(keyword_groups) + flagged_urls
    if prediction == "PHISHING" or evidence_count >= 3: level = "HIGH"
    elif evidence_count: level = "MEDIUM"
    else: level = "LOW"
    reasons = []
    if prediction == "PHISHING": reasons.append("The trained text model found patterns similar to phishing examples in its training data.")
    for group, matches in keyword_groups.items():
        if matches: reasons.append(f"{group.replace('_', ' ').capitalize()} language detected: {', '.join(matches[:5])}.")
    for item in urls:
        if item["indicators"]: reasons.append(f"URL {item['host']} has: {', '.join(item['indicators'])}.")
    if not reasons: reasons.append("No configured keyword or URL indicators were found.")
    return level, reasons
