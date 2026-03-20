import json
import re
import requests
import os
from aadhaar_check import detect_aadhaar

# Cache for HIBP breaches — fetched once per session
_hibp_cache = None

def load_sms_lookup():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sms_path = os.path.join(current_dir, 'data', 'sms_lookup.json')
    with open(sms_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_known_breaches():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    breach_path = os.path.join(current_dir, 'data', 'breach_db.json')
    with open(breach_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Function 1 — Parse MyActivity.json
def parse_myactivity(file_content: str) -> list:
    try:
        data = json.loads(file_content)
        companies = []

        if isinstance(data, list):
            for item in data:
                if 'header' in item:
                    company = item['header']
                    if company and company not in companies:
                        companies.append(company)
                if 'subtitles' in item:
                    for subtitle in item['subtitles']:
                        if 'name' in subtitle:
                            name = subtitle['name']
                            if name and name not in companies:
                                companies.append(name)

        return companies

    except Exception:
        return []

# Function 2 — Parse Location History.json
def parse_location(file_content: str) -> dict:
    try:
        data = json.loads(file_content)
        locations = []

        if 'locations' in data:
            raw = data['locations'][:100]
            for loc in raw:
                if 'latitudeE7' in loc and 'longitudeE7' in loc:
                    lat = loc['latitudeE7'] / 1e7
                    lng = loc['longitudeE7'] / 1e7
                    locations.append({"lat": lat, "lng": lng})

        city = "Unknown"
        if 'timelineObjects' in data:
            for obj in data['timelineObjects'][:50]:
                if 'placeVisit' in obj:
                    place = obj['placeVisit']
                    if 'location' in place:
                        address = place['location'].get('address', '')
                        if address:
                            parts = address.split(',')
                            if len(parts) >= 3:
                                city = parts[-3].strip()
                            elif len(parts) >= 2:
                                city = parts[-2].strip()
                            break

        return {
            "city": city,
            "location_count": len(locations),
            "sample_locations": locations[:5]
        }

    except Exception:
        return {"city": "Unknown", "location_count": 0, "sample_locations": []}

# Function 3 — Resolve SMS headers to company names
def resolve_sms_headers(headers_text: str) -> list:
    sms_lookup = load_sms_lookup()
    resolved = []
    seen_companies = set()

    raw_headers = re.split(r'[\n,\s]+', headers_text.strip())

    for header in raw_headers:
        header = header.strip().upper()
        if not header:
            continue

        if header in sms_lookup:
            company_data = sms_lookup[header]
            company_name = company_data["company"]

            # Deduplicate by company name
            if company_name in seen_companies:
                continue
            seen_companies.add(company_name)

            resolved.append({
                "header": header,
                "company": company_name,
                "category": company_data["category"],
                "dpo_email": company_data.get("dpo_email"),
                "data_held": company_data.get("data_held", []),
                "website": company_data.get("website", ""),
                "source": "sms"
            })
        else:
            # FIX: Deduplicate unknown headers so they don't inflate the company count
            if "Unknown Company" not in seen_companies:
                seen_companies.add("Unknown Company")
                resolved.append({
                    "header": "VARIOUS_UNKNOWN",
                    "company": "Unknown Company",
                    "category": "Unknown",
                    "dpo_email": None,
                    "data_held": [],
                    "website": "",
                    "source": "sms",
                    "note": "Unresolved headers grouped here"
                })

    return resolved

# Function 4 — Get all breaches from HIBP free endpoint with caching
def get_all_breaches() -> list:
    global _hibp_cache

    if _hibp_cache is not None:
        print("[Agent 1 — Detective] Using cached breach data...")
        return _hibp_cache

    try:
        url = "https://haveibeenpwned.com/api/v3/breaches"
        headers = {"user-agent": "ShadowTrace-App"}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            _hibp_cache = response.json()
            return _hibp_cache
        else:
            return []

    except Exception:
        return []

# Function 5 — Cross reference companies with HIBP breach list
def match_breaches_to_companies(resolved_companies: list, all_breaches: list) -> list:
    breached_companies = []

    breach_lookup = {}
    for breach in all_breaches:
        domain = breach.get('Domain', '').lower()
        if domain:
            breach_lookup[domain] = breach

    for company_data in resolved_companies:
        website = company_data.get('website', '').lower()
        website = website.replace('https://', '').replace('http://', '').replace('www.', '')

        if not website:
            continue

        matched_breach = None
        for breach_domain, breach_info in breach_lookup.items():
            # FIX: Tighter domain matching. 
            # We use heuristic domain matching for real-time inference. 
            # Production version would use normalized domain mapping.
            if breach_domain and (website == breach_domain or website.endswith('.' + breach_domain) or breach_domain.endswith('.' + website)):
                matched_breach = breach_info
                break

        if matched_breach:
            breached_companies.append({
                "company": company_data['company'],
                "header": company_data.get('header', ''),
                "breach_name": matched_breach.get('Name', ''),
                "breach_date": matched_breach.get('BreachDate', ''),
                "records_exposed": matched_breach.get('PwnCount', 0),
                "data_types": matched_breach.get('DataClasses', []),
                "is_verified": matched_breach.get('IsVerified', False)
            })

    return breached_companies

# Function 6 — Merge activity companies into resolved list
def merge_activity_companies(
    resolved_companies: list,
    activity_companies: list
) -> list:

    existing_names = {c['company'].lower() for c in resolved_companies}
    merged = resolved_companies.copy()

    for company_name in activity_companies:
        # FIX: Filter out ultra-short junk labels to reduce noise
        if len(company_name.strip()) < 3:
            continue
            
        if company_name.lower() not in existing_names:
            merged.append({
                "company": company_name,
                "category": "Google Activity",
                "dpo_email": None,
                "data_held": ["activity data"],
                "website": "",
                "source": "google_activity",
                "note": "Unverified activity label"
            })
            existing_names.add(company_name.lower())

    return merged

# Function 7 — Calculate risk score
def calculate_risk_score(
    resolved_companies: list,
    breached_companies: list,
    aadhaar_result: dict,
    location_data: dict
) -> int:

    score = 0

    # Deduplicate companies before scoring
    unique_companies = {c['company'] for c in resolved_companies}
    company_count = len(unique_companies)

    # Number of companies holding data (max 25 points)
    if company_count >= 50:
        score += 25
    elif company_count >= 30:
        score += 20
    elif company_count >= 15:
        score += 15
    elif company_count >= 5:
        score += 10
    else:
        score += 5

    # Number of breaches found (max 30 points)
    unique_breaches = {c['company'] for c in breached_companies}
    breach_count = len(unique_breaches)

    if breach_count >= 10:
        score += 30
    elif breach_count >= 5:
        score += 22
    elif breach_count >= 3:
        score += 15
    elif breach_count >= 1:
        score += 8

    # Sensitive data exposure (max 25 points)
    sensitive_categories = ['Banking', 'Fintech', 'Healthcare', 'Government']
    sensitive_count = len({
        c['company'] for c in resolved_companies
        if c.get('category') in sensitive_categories
    })

    if sensitive_count >= 5:
        score += 25
    elif sensitive_count >= 3:
        score += 18
    elif sensitive_count >= 1:
        score += 10

    # Aadhaar exposure (max 20 points)
    if aadhaar_result.get('aadhaar_found'):
        score += 20

    return min(score, 100)

# Master Agent 1 function
def run_detective(
    email: str,
    myactivity_content: str,
    location_content: str,
    sms_headers: str
) -> dict:

    print("[Agent 1 — Detective] Starting investigation...")

    # Step 1 — Parse Google activity
    print("[Agent 1 — Detective] Parsing MyActivity.json...")
    activity_companies = parse_myactivity(myactivity_content)

    # Step 2 — Parse location
    print("[Agent 1 — Detective] Parsing Location History.json...")
    location_data = parse_location(location_content)

    # Step 3 — Resolve SMS headers
    print("[Agent 1 — Detective] Resolving SMS headers...")
    sms_companies = resolve_sms_headers(sms_headers)

    # Step 4 — Merge activity companies into SMS resolved list
    print("[Agent 1 — Detective] Merging activity data...")
    resolved_companies = merge_activity_companies(sms_companies, activity_companies)

    # Step 5 — Get all breaches from HIBP (cached after first call)
    print("[Agent 1 — Detective] Checking breach databases...")
    all_breaches = get_all_breaches()

    # Step 6 — Match companies to breaches
    print("[Agent 1 — Detective] Cross-referencing Indian breaches...")
    breached_companies = match_breaches_to_companies(resolved_companies, all_breaches)

    # Step 7 — Aadhaar check
    # Build meaningful text context for detection
    print("[Agent 1 — Detective] Running Aadhaar pattern check...")
    breach_text_context = " ".join([
        f"aadhaar uid {b.get('company','')} {' '.join(b.get('data_types', []))}"
        for b in breached_companies
        if 'aadhaar' in [dt.lower() for dt in b.get('data_types', [])]
    ])
    aadhaar_result = detect_aadhaar(breach_text_context + " " + email)

    if aadhaar_result['aadhaar_found']:
        print("[Agent 1 — Detective] ⚠ CRITICAL — Aadhaar pattern detected")
    else:
        print("[Agent 1 — Detective] Aadhaar check clean")

    # Step 8 — Calculate risk score
    print("[Agent 1 — Detective] Calculating risk score...")
    risk_score = calculate_risk_score(
        resolved_companies,
        breached_companies,
        aadhaar_result,
        location_data
    )

    print(f"[Agent 1 — Detective] Complete. Risk score: {risk_score}/100")

    return {
        "email": email,
        "activity_companies": activity_companies,
        "location_data": location_data,
        "resolved_companies": resolved_companies,
        "breached_companies": breached_companies,
        "aadhaar_result": aadhaar_result,
        "risk_score": risk_score,
        "total_companies_found": len(resolved_companies),
        "total_breaches_found": len(breached_companies)
    }