import json
import traceback
from detective import run_detective
from profiler import run_profiler

# Master coordinator — calls all agents in sequence
# Each agent receives output from the previous agent

def run_agent(
    email: str,
    myactivity_content: str,
    location_content: str,
    sms_headers: str
) -> dict:

    print("\n========================================")
    print("   ShadowTrace Agent Pipeline Starting")
    print("========================================\n")

    # ─────────────────────────────────────────
    # AGENT 1 — THE DETECTIVE
    # ─────────────────────────────────────────
    try:
        detective_output = run_detective(
            email=email,
            myactivity_content=myactivity_content,
            location_content=location_content,
            sms_headers=sms_headers
        )
        print("\n[Coordinator] Agent 1 complete.")
        print(f"[Coordinator] Companies found: {detective_output.get('total_companies_found', 0)}")
        print(f"[Coordinator] Breaches found: {detective_output.get('total_breaches_found', 0)}")
        print(f"[Coordinator] Risk score: {detective_output.get('risk_score', 0)}/100")

    except Exception as e:
        print(f"\n[Coordinator] WARNING: Agent 1 error. Using fallback.")
        print(traceback.format_exc())
        detective_output = {
            "resolved_companies": [],
            "breached_companies": [],
            "aadhaar_result": {"aadhaar_found": False},
            "risk_score": 0,
            "location_data": {"city": "Unknown", "location_count": 0, "sample_locations": []},
            "total_companies_found": 0,
            "total_breaches_found": 0,
            "activity_companies": []
        }

    # ─────────────────────────────────────────
    # AGENT 2 — THE PROFILER
    # ─────────────────────────────────────────
    try:
        profiler_output = run_profiler(
            email=email,
            location_data=detective_output['location_data'],
            resolved_companies=detective_output['resolved_companies'],
            breached_companies=detective_output['breached_companies'],
            risk_score=detective_output['risk_score']
        )
        print("\n[Coordinator] Agent 2 complete.")

    except Exception as e:
        print(f"\n[Coordinator] WARNING: Agent 2 error. Using fallback.")
        print(traceback.format_exc())
        profiler_output = {
            "ghost_profile_nodes": {},
            "consent_expiry": [],
            "shadow_profile": {
                "email": email,
                "city": "Unknown",
                "exposure_level": "LOW",
                "total_companies_tracking": 0,
                "total_breaches": 0,
                "sensitive_companies": [],
                "leaked_passwords": [],
                "unique_data_types_exposed": [],
                "most_sensitive_exposure": "Personal data"
            },
            "predictive_score": {
                "probability_percentage": 0,
                "risk_window": "next 6 months",
                "primary_threat": "Data aggregation",
                "confidence": "medium"
            }
        }

    # ─────────────────────────────────────────
    # AGENT 3 — THE HACKER (Day 5)
    # ─────────────────────────────────────────
    print("\n[Agent 3 — Hacker] Generating threat simulation... (placeholder)")
    hacker_output = {
        "phishing_sim": {
            "subject": "Placeholder — built on Day 5",
            "body": "Placeholder — built on Day 5",
            "simulated": True,
            "watermark": "SIMULATED THREAT — FOR AWARENESS ONLY"
        },
        "propagation_graph": [],
        "credential_stuffing_score": 0
    }
    print("[Agent 3 — Hacker] Done.")

    # ─────────────────────────────────────────
    # AGENT 4 — THE LAWYER (Day 5)
    # ─────────────────────────────────────────
    print("\n[Agent 4 — Lawyer] Drafting legal package... (placeholder)")
    lawyer_output = {
        "legal_letters": [],
        "compliance_deadlines": [],
        "evidence_bundle": None
    }
    print("[Agent 4 — Lawyer] Done.")

    # ─────────────────────────────────────────
    # FINAL OUTPUT
    # ─────────────────────────────────────────
    print("\n========================================")
    print("   ShadowTrace Pipeline Complete")
    print("========================================\n")

    return {
        "status": "complete" if detective_output.get('total_companies_found', 0) > 0 else "partial_fallback",
        "email": email,

        # Agent 1
        "resolved_companies": detective_output['resolved_companies'],
        "breached_companies": detective_output['breached_companies'],
        "aadhaar_result": detective_output['aadhaar_result'],
        "risk_score": detective_output['risk_score'],
        "location_data": detective_output['location_data'],
        "total_companies_found": detective_output.get('total_companies_found', 0),
        "total_breaches_found": detective_output.get('total_breaches_found', 0),

        # Agent 2
        "ghost_profile_nodes": profiler_output['ghost_profile_nodes'],
        "consent_expiry": profiler_output['consent_expiry'],
        "shadow_profile": profiler_output['shadow_profile'],
        "predictive_score": profiler_output['predictive_score'],

        # Agent 3
        "phishing_sim": hacker_output['phishing_sim'],
        "propagation_graph": hacker_output['propagation_graph'],
        "credential_stuffing_score": hacker_output['credential_stuffing_score'],

        # Agent 4
        "legal_letters": lawyer_output['legal_letters'],
        "compliance_deadlines": lawyer_output['compliance_deadlines'],
        "evidence_bundle": lawyer_output['evidence_bundle']
    }