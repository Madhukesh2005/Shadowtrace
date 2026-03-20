import json
import traceback
from detective import run_detective

# Master coordinator — calls all agents in sequence
# Each agent receives output from previous agent

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
    # Finds all exposure
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
        print(f"\n[Coordinator] ⚠️ WARNING: Agent 1 encountered an error. Using partial fallback.")
        print(traceback.format_exc())
        # Resilient fallback: Inject Zero-State so the API contract survives
        detective_output = {
            "resolved_companies": [],
            "breached_companies": [],
            "aadhaar_result": {"aadhaar_found": False},
            "risk_score": 0,
            "location_data": {"city": "Unknown", "location_count": 0, "sample_locations": []},
            "total_companies_found": 0,
            "total_breaches_found": 0
        }

    # ─────────────────────────────────────────
    # AGENT 2 — THE PROFILER (Day 5)
    # Assembles shadow profile
    # ─────────────────────────────────────────
    print("\n[Agent 2 — Profiler] Building ghost profile... ")
    
    # Transformation: Map flat company list into categorized threat nodes
    threat_nodes_sets = {}
    for comp in detective_output.get('resolved_companies', []):
        cat = comp.get('category', 'Unknown')
        if cat not in threat_nodes_sets:
            threat_nodes_sets[cat] = set()
        threat_nodes_sets[cat].add(comp['company'])
        
    # Convert sets back to lists for clean JSON serialization
    threat_nodes = {k: list(v) for k, v in threat_nodes_sets.items()}

    profiler_output = {
        "ghost_profile_nodes": threat_nodes,
        "shadow_profile": {
            "email": email,
            "city": detective_output['location_data'].get('city', 'Unknown'),
            "total_companies": detective_output.get('total_companies_found', 0),
            "total_breaches": detective_output.get('total_breaches_found', 0),
            "risk_score": detective_output.get('risk_score', 0)
        },
        "consent_expiry": [],
        "predictive_score": detective_output.get('risk_score', 0)
    }
    print("[Agent 2 — Profiler] Done.")

    # ─────────────────────────────────────────
    # AGENT 3 — THE HACKER (Day 6)
    # Simulates attack
    # ─────────────────────────────────────────
    print("\n[Agent 3 — Hacker] Generating threat simulation... (placeholder)")
    hacker_output = {
        "phishing_sim": {
            "subject": "Placeholder — built on Day 6",
            "body": "Placeholder — built on Day 6",
            "simulated": True
        },
        "propagation_graph": [],
        "credential_stuffing_score": 0
    }
    print("[Agent 3 — Hacker] Done.")

    # ─────────────────────────────────────────
    # AGENT 4 — THE LAWYER (Day 6)
    # Takes legal action
    # ─────────────────────────────────────────
    print("\n[Agent 4 — Lawyer] Drafting legal package... (placeholder)")
    lawyer_output = {
        "legal_letters": [],
        "compliance_deadlines": [],
        "evidence_bundle": None
    }
    print("[Agent 4 — Lawyer] Done.")

    # ─────────────────────────────────────────
    # FINAL OUTPUT — everything combined
    # ─────────────────────────────────────────
    print("\n========================================")
    print("   ShadowTrace Pipeline Complete")
    print("========================================\n")

    return {
        "status": "complete" if detective_output.get('total_companies_found', 0) > 0 else "partial_fallback",
        "email": email,

        # Agent 1 output
        "resolved_companies": detective_output['resolved_companies'],
        "breached_companies": detective_output['breached_companies'],
        "aadhaar_result": detective_output['aadhaar_result'],
        "risk_score": detective_output['risk_score'],
        "location_data": detective_output['location_data'],
        "total_companies_found": detective_output.get('total_companies_found', 0),
        "total_breaches_found": detective_output.get('total_breaches_found', 0),

        # Agent 2 output
        "ghost_profile_nodes": profiler_output['ghost_profile_nodes'],
        "shadow_profile": profiler_output['shadow_profile'],
        "consent_expiry": profiler_output['consent_expiry'],
        "predictive_score": profiler_output['predictive_score'],

        # Agent 3 output
        "phishing_sim": hacker_output['phishing_sim'],
        "propagation_graph": hacker_output['propagation_graph'],
        "credential_stuffing_score": hacker_output['credential_stuffing_score'],

        # Agent 4 output
        "legal_letters": lawyer_output['legal_letters'],
        "compliance_deadlines": lawyer_output['compliance_deadlines'],
        "evidence_bundle": lawyer_output['evidence_bundle']
    }