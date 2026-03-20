import re

def detect_aadhaar(text: str) -> dict:

    # Only flag if context suggests Aadhaar
    context_keywords = ["aadhaar", "aadhar", "uid", "uidai", "unique identification"]
    text_lower = text.lower()
    context_found = any(keyword in text_lower for keyword in context_keywords)

    # Aadhaar pattern — 12 digits with optional spaces or dashes
    pattern = r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
    matches = re.findall(pattern, text)

    # Filter false positives — valid Aadhaar never starts with 0 or 1
    valid_matches = []
    for match in matches:
        digits_only = re.sub(r'[\s-]', '', match)
        if len(digits_only) == 12 and digits_only[0] not in ['0', '1']:
            valid_matches.append(match)

    if valid_matches and context_found:
        return {
            "aadhaar_found": True,
            "count": len(valid_matches),
            "severity": "critical",
            "message": f"Aadhaar pattern detected in breach data. {len(valid_matches)} instance(s) found.",
            "flag": "CRITICAL — Aadhaar exposure is the most serious data breach possible in India"
        }

    if valid_matches and not context_found:
        return {
            "aadhaar_found": False,
            "count": 0,
            "severity": "low",
            "message": "12-digit pattern found but no Aadhaar context detected. Possible false positive.",
            "flag": ""
        }

    return {
        "aadhaar_found": False,
        "count": 0,
        "severity": "none",
        "message": "No Aadhaar pattern detected",
        "flag": ""
    }