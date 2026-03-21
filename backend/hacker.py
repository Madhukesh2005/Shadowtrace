import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# Set to True! We are using free Gemini 2.5 Flash now.
USE_REAL_AI = True

def build_propagation_graph(resolved_companies: list, breached_companies: list) -> dict:
    nodes = []
    links = []
    
    breached_names = {b['company'].lower() for b in breached_companies}
    
    nodes.append({"id": "User Identity", "group": "center", "radius": 20})
    
    for company in resolved_companies:
        comp_name = company['company']
        is_breached = comp_name.lower() in breached_names
        category = company.get('category', 'Unknown')
        
        risk_weight = 2 if is_breached and category in ['Banking', 'Fintech'] else (1 if is_breached else 0)
        
        nodes.append({
            "id": comp_name,
            "group": category,
            "breached": is_breached,
            "risk_weight": risk_weight
        })
        
        links.append({
            "source": "User Identity",
            "target": comp_name,
            "value": 2 if is_breached else 1
        })

    return {"nodes": nodes, "links": links}

def generate_phishing_sim(shadow_profile: dict, breached_companies: list, location_data: dict) -> dict:
    email = shadow_profile.get('email', 'user@example.com')
    city = location_data.get('city', 'Unknown City')
    
    passwords = shadow_profile.get('leaked_passwords', [])
    password_hint = passwords[0]['type'] if passwords else "account credentials"
    spoof_target = breached_companies[0]['company'] if breached_companies else "IT Security Team"

    if USE_REAL_AI:
        try:
            # 1. Initialize the NEW Gemini Client
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

            prompt = f"""
            You are a senior cybersecurity awareness trainer conducting a red-team simulation.
            Draft a sophisticated, realistic spear-phishing email using ONLY this leaked data:
            
            Target Email: {email}
            Target City: {city}
            Spoofed Company: {spoof_target}
            Leaked Data Type: {password_hint}
            
            Return ONLY a valid JSON object using this exact schema:
            {{
                "subject": "The email subject line",
                "body": "The email body text",
                "data_sources_used": ["List", "of", "sources"],
                "simulated": true,
                "watermark": "SIMULATED THREAT — FOR AWARENESS ONLY"
            }}
            """

            # 2. Configure the new SDK to output JSON and bypass safety blocks
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.3,
                safety_settings=[
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE,
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE,
                    )
                ]
            )

            # 3. Generate content with Gemini 2.5 Flash
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=config
            )
            
            print("[Agent 3 — Hacker] Threat simulation generated via AI engine...")
            return json.loads(response.text)

        except Exception as e:
            print(f"[Agent 3 — Hacker] Gemini API failed: {str(e)}")
            raise e # Forces the terminal to show you exactly why it failed

    # THE FALLBACK
    return {
        "subject": f"URGENT: Unauthorized login attempt to {spoof_target} from {city}",
        "body": f"Hi,\n\nWe detected a suspicious login attempt to your {spoof_target} account from an unrecognized device in {city}.\n\nTo secure your account and prevent unauthorized access, please verify your identity using {password_hint} immediately.\n\nClick here to secure your account: [MALICIOUS LINK]\n\nRegards,\n{spoof_target} Security Team",
        "data_sources_used": ["Location History", "Breach Database", "SMS Headers"],
        "simulated": True,
        "watermark": "SIMULATED THREAT — FOR AWARENESS ONLY"
    }

def calculate_credential_stuffing_score(breached_companies: list, resolved_companies: list) -> int:
    passwords_leaked = sum(1 for b in breached_companies if any("password" in dt.lower() for dt in b.get('data_types', [])))
    if passwords_leaked == 0:
        return 0
    total_platforms = len(resolved_companies)
    score = min((passwords_leaked * 20) + (total_platforms * 2), 100)
    return score

# Master Agent 3 function
def run_hacker(shadow_profile: dict, breached_companies: list, location_data: dict, resolved_companies: list) -> dict:
    print("\n[Agent 3 — Hacker] Generating threat simulation...")
    phishing_sim = generate_phishing_sim(shadow_profile, breached_companies, location_data)
    
    print("[Agent 3 — Hacker] Building breach propagation graph...")
    propagation_graph = build_propagation_graph(resolved_companies, breached_companies)
    
    print("[Agent 3 — Hacker] Calculating credential stuffing vulnerability...")
    stuffing_score = calculate_credential_stuffing_score(breached_companies, resolved_companies)
    
    print("[Agent 3 — Hacker] Threat generation complete.")

    return {
        "phishing_sim": phishing_sim,
        "propagation_graph": propagation_graph,
        "credential_stuffing_score": stuffing_score
    }