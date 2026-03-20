import json
import os
from datetime import datetime

# Global caches to prevent repetitive disk I/O
_dpo_cache = None
_breach_cache = None

# Load DPO directory with caching
def load_dpo_directory():
    global _dpo_cache
    if _dpo_cache is not None:
        return _dpo_cache
        
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dpo_path = os.path.join(current_dir, 'data', 'dpo_directory.json')
    with open(dpo_path, 'r', encoding='utf-8') as f:
        _dpo_cache = json.load(f)
    return _dpo_cache

# Load known Indian breaches with caching
def load_known_breaches():
    global _breach_cache
    if _breach_cache is not None:
        return _breach_cache
        
    current_dir = os.path.dirname(os.path.abspath(__file__))
    breach_path = os.path.join(current_dir, 'data', 'known_breaches.json')
    with open(breach_path, 'r', encoding='utf-8') as f:
        _breach_cache = json.load(f)
    return _breach_cache

# Function 1 — Build ghost profile nodes for D3.js
def build_ghost_profile(resolved_companies: list, breached_companies: list) -> dict:

    # Build a set of breached company names for quick lookup
    breached_names = {b['company'] for b in breached_companies}

    # Build nodes grouped by category
    nodes = {}
    for company in resolved_companies:
        category = company.get('category', 'Unknown')
        if category not in nodes:
            nodes[category] = []

        nodes[category].append({
            "company": company['company'],
            "category": category,
            "breached": company['company'] in breached_names,
            "data_held": company.get('data_held', []),
            "source": company.get('source', 'sms'),
            "dpo_email": company.get('dpo_email')
        })

    return nodes

# Function 2 — Calculate consent expiry per company
def calculate_consent_expiry(resolved_companies: list) -> list:
    dpo_directory = load_dpo_directory()

    # THE FIX: Correctly read the "companies" list from the JSON
    dpo_lookup = {
        entry["company"].lower(): entry
        for entry in dpo_directory.get("companies", [])
    }

    consent_results = []
    current_date = datetime.now()

    for company in resolved_companies:
        company_name = company['company']
        
        # SAFETY IMPROVEMENT: Handle invisible whitespace
        company_lower = company_name.lower().strip()

        # Find matching DPO entry
        dpo_entry = dpo_lookup.get(company_lower)

        # Determine best contact
        # Determine best contact (Read directly from Agent 1's hard work!)
        contact = company.get('dpo_email')
        contact_type = 'dpo_email' if contact else None
        
        escalation = None
        if dpo_entry:
            escalation = dpo_entry.get('escalation', {})

        # Consent expiry logic
        category = company.get('category', 'Unknown')

        # Categories likely to have expired consent
        high_expiry_categories = ['EdTech', 'Travel', 'Entertainment', 'E-Commerce']
        medium_expiry_categories = ['Food Delivery', 'Services', 'Real Estate']

        if category in high_expiry_categories:
            expiry_status = "likely_expired"
            expiry_message = f"{company_name} may be holding your data beyond the purpose it was collected for."
        elif category in medium_expiry_categories:
            expiry_status = "check_required"
            expiry_message = f"{company_name} should verify their data retention policy."
        else:
            expiry_status = "active"
            expiry_message = f"{company_name} has an ongoing service relationship."

        # Section 16 violation check (No clean DPO contact exposed)
        section_16_violation = contact is None

        consent_results.append({
            "company": company_name,
            "category": category,
            "expiry_status": expiry_status,
            "expiry_message": expiry_message,
            "best_contact": contact,
            "contact_type": contact_type,
            "section_16_violation": section_16_violation,
            "escalation": escalation,
            "dpdp_sections": ["Section 6", "Section 12"] + (["Section 16"] if section_16_violation else [])
        })

    return consent_results

# Function 3 — Build shadow profile card
def build_shadow_profile(
    email: str,
    location_data: dict,
    resolved_companies: list,
    breached_companies: list
) -> dict:

    # Extract sensitive data types from breaches
    all_data_types = []
    leaked_passwords = []

    for breach in breached_companies:
        data_types = breach.get('data_types', [])
        all_data_types.extend(data_types)
        
        # Robust password detection
        if any("password" in dt.lower() for dt in data_types):
            year_raw = breach.get('breach_date') or breach.get('year', 'Unknown')
            year_str = str(year_raw)[:4]
            
            leaked_passwords.append({
                "source": breach['company'],
                "year": year_str,
                "type": "password hash"
            })

    # Count sensitive categories
    sensitive_categories = ['Banking', 'Fintech', 'Healthcare', 'Government']
    sensitive_companies = [
        c['company'] for c in resolved_companies
        if c.get('category') in sensitive_categories
    ]

    # Normalize data types for strict, case-insensitive comparison
    lower_types = [x.lower() for x in all_data_types]

    # Determine exposure level
    total_breaches = len(breached_companies)
    if total_breaches >= 5:
        exposure_level = "CRITICAL"
    elif total_breaches >= 3:
        exposure_level = "HIGH"
    elif total_breaches >= 1:
        exposure_level = "MEDIUM"
    else:
        exposure_level = "LOW"

    return {
        "email": email,
        "city": location_data.get('city', 'Unknown'),
        "exposure_level": exposure_level,
        "total_companies_tracking": len(resolved_companies),
        "total_breaches": total_breaches,
        "sensitive_companies": sensitive_companies,
        "leaked_passwords": leaked_passwords,
        "unique_data_types_exposed": list(set(all_data_types)),
        "most_sensitive_exposure": "Aadhaar" if "aadhaar" in lower_types else
                                   "Passport" if "passport" in lower_types else
                                   "Financial data" if any(
                                       x in lower_types for x in
                                       ['credit card', 'bank account', 'pan']
                                   ) else "Personal data"
    }

# Function 4 — Calculate predictive breach score
def calculate_predictive_score(
    risk_score: int,
    breached_companies: list,
    resolved_companies: list
) -> dict:

    # Base probability from risk score
    base_probability = risk_score

    # Boost if recent breaches exist
    recent_breaches = []
    for b in breached_companies:
        year_raw = b.get('breach_date') or b.get('year')
        try:
            if year_raw:
                year_int = int(str(year_raw)[:4])
                if year_int >= 2020:
                    recent_breaches.append(b)
        except (ValueError, TypeError):
            pass

    if len(recent_breaches) >= 3:
        base_probability = min(base_probability + 20, 99)
    elif len(recent_breaches) >= 1:
        base_probability = min(base_probability + 10, 99)

    # Boost if password was leaked
    password_leaked = any(
        any("password" in dt.lower() for dt in b.get('data_types', []))
        for b in breached_companies
    )

    if password_leaked:
        base_probability = min(base_probability + 15, 99)

    return {
        "probability_percentage": base_probability,
        "risk_window": "next 6 months",
        "primary_threat": "Credential stuffing" if password_leaked else "Data aggregation",
        "confidence": "medium"
    }

# Master Agent 2 function
def run_profiler(
    email: str,
    location_data: dict,
    resolved_companies: list,
    breached_companies: list,
    risk_score: int
) -> dict:

    print("\n[Agent 2 — Profiler] Starting profile assembly...")

    # Step 1 — Build ghost profile nodes
    print("[Agent 2 — Profiler] Building ghost profile visualization data...")
    ghost_profile_nodes = build_ghost_profile(resolved_companies, breached_companies)

    # Step 2 — Calculate consent expiry
    print("[Agent 2 — Profiler] Calculating consent expiry per company...")
    consent_expiry = calculate_consent_expiry(resolved_companies)

    # Step 3 — Build shadow profile
    print("[Agent 2 — Profiler] Assembling shadow profile card...")
    shadow_profile = build_shadow_profile(
        email, location_data, resolved_companies, breached_companies
    )

    # Step 4 — Calculate predictive score
    print("[Agent 2 — Profiler] Calculating predictive breach probability...")
    predictive_score = calculate_predictive_score(
        risk_score, breached_companies, resolved_companies
    )

    print("[Agent 2 — Profiler] Profile assembly complete.")

    return {
        "ghost_profile_nodes": ghost_profile_nodes,
        "consent_expiry": consent_expiry,
        "shadow_profile": shadow_profile,
        "predictive_score": predictive_score
    }