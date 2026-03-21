import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables securely
load_dotenv()

# PROTECTING YOUR CREDITS & LIMITS
# Set to True for live generation.
USE_REAL_AI = True

def generate_legal_letters(consent_expiry: list, email: str) -> list:
    letters = []
    today = datetime.now()
    deadline_date = (today + timedelta(days=90)).strftime("%Y-%m-%d")

    client = None
    if USE_REAL_AI:
        try:
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        except Exception as e:
            print(f"[Agent 4 — Lawyer] Gemini Initialization Error: {e}")

    # 1. Build the batch list of companies for a single prompt
    companies_text = ""
    for i, company_data in enumerate(consent_expiry):
        company_name = company_data.get('company', 'Unknown Company')
        is_sec_16 = company_data.get('section_16_violation', False)
        escalation = company_data.get('escalation') or {}
        regulator = escalation.get('regulator', 'the Data Protection Board of India')
        
        companies_text += f"{i+1}. Company: {company_name} | Section16Violation: {is_sec_16} | Regulator: {regulator}\n"

    # 2. Make a SINGLE Gemini call for all letters
    ai_bodies = {}
    if USE_REAL_AI and client:
        try:
            prompt = f"""
            You are drafting formal legal letters under the Digital Personal Data Protection (DPDP) Act 2025.
            
            Sender Email: {email}
            Deadline: {deadline_date} (90 days)
            
            Draft one legal letter for EACH company listed below:
            {companies_text}
            
            Rules for EVERY letter:
            1. Write in FIRST PERSON as {email} themselves. NOT as a lawyer or advocate.
            2. Never use placeholders like [Name]. Use {email} as the sender identity.
            3. Address each letter to the Data Protection Officer of that specific company.
            4. Cite Section 12 of the DPDP Act 2025 as the legal basis for the erasure demand.
            5. If Section16Violation is True, firmly call out that company for failing to maintain a publicly accessible DPO contact.
            6. Threaten escalation to the listed Regulator under Section 33.
            7. End every letter with "Regards," followed by {email} on the next line.
            8. Keep the tone firm, professional, and legally authoritative.
            
            Return ONLY a valid JSON object using the exact company numbers as keys:
            {{
                "1": "full letter body for company 1",
                "2": "full letter body for company 2"
            }}
            """

            # Force perfect JSON output and set a high token limit to prevent truncation
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
                max_output_tokens=8000 
            )

            print(f"[Agent 4 — Lawyer] Sending batch request to AI engine for {len(consent_expiry)} companies...")
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=config
            )

            # Native JSON loading (Because of the config, we know it's clean JSON)
            ai_bodies = json.loads(response.text)
            print(f"[Agent 4 — Lawyer] Successfully drafted all {len(consent_expiry)} letters via AI engine.")

        except Exception as e:
            print(f"[Agent 4 — Lawyer] Gemini API failed: {str(e)}")
            print(f"[Agent 4 — Lawyer] Using fallback templates for all companies...")
            ai_bodies = {}

    # 3. Build the final letters list
    for i, company_data in enumerate(consent_expiry):
        company_name = company_data.get('company', 'Unknown Company')
        contact = company_data.get('best_contact')
        is_sec_16_violation = company_data.get('section_16_violation', False)
        escalation = company_data.get('escalation') or {}
        regulator = escalation.get('regulator', 'the Data Protection Board of India')

        # Try to get the AI generated body using the string index ("1", "2", etc.)
        body = ai_bodies.get(str(i+1), "")

        # The Fallback (If the AI failed, or skipped a company)
        if not body:
            body = f"To the Data Protection Officer,\n{company_name}\n\n"
            body += f"I am writing to formally invoke my rights under the Digital Personal Data Protection Act 2025.\n\n"
            body += f"Under Section 12, I hereby demand the complete and permanent erasure of all personal data you hold pertaining to me.\n\n"
            
            if is_sec_16_violation:
                body += f"Furthermore, your failure to maintain a publicly accessible Data Protection Officer contact constitutes a violation of Section 16 of the DPDP Act. This has been noted as additional evidence of non-compliance.\n\n"
            
            body += f"Please confirm complete erasure within 90 days of this notice (by {deadline_date}). Non-compliance will be escalated to {regulator} and may result in penalties of up to Rs 250 crore under Section 33.\n\n"
            body += f"Regards,\n{email}"

        letters.append({
            "company": company_name,
            "recipient_email": contact or None,
            "delivery_status": "missing_contact" if not contact else "ready",
            "subject": "Formal Data Erasure Request — DPDP Act 2025 — Section 12",
            "body": body,
            "dpdp_sections_cited": company_data.get('dpdp_sections', ["Section 12", "Section 33"]),
            "compliance_deadline_days": 90,
            "deadline_date": deadline_date,
            "escalation_regulator": regulator
        })

    return letters

def run_lawyer(consent_expiry: list, shadow_profile: dict, email: str) -> dict:
    print("\n[Agent 4 — Lawyer] Drafting legal package...")
    
    legal_letters = generate_legal_letters(consent_expiry, email)
    
    # Extract unique deadlines
    deadlines = list(set([letter['deadline_date'] for letter in legal_letters]))
    
    print(f"[Agent 4 — Lawyer] Legal package complete.")

    return {
        "legal_letters": legal_letters,
        "compliance_deadlines": deadlines,
        "evidence_bundle": None 
    }