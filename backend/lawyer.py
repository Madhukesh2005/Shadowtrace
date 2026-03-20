import os
from datetime import datetime, timedelta
from google import genai

# Set to True! We are using free Gemini 2.5 Flash now.
USE_REAL_AI = True

def generate_legal_letters(consent_expiry: list, email: str) -> list:
    letters = []
    today = datetime.now()
    # 90-day compliance window under DPDP
    deadline_date = (today + timedelta(days=90)).strftime("%Y-%m-%d")

    # Initialize the NEW Gemini Client
    client = None
    if USE_REAL_AI:
        try:
            client = genai.Client(api_key="AIzaSyCYpYwiTryAIjZosXYb0flnBx8JEbPi9SM")
        except Exception as e:
            print(f"[Agent 4 — Lawyer] Gemini Initialization Error: {e}")

    for company_data in consent_expiry:
        # Defensive access to prevent KeyError
        company_name = company_data.get('company', 'Unknown Company')
        contact = company_data.get('best_contact')
        is_sec_16_violation = company_data.get('section_16_violation', False)
        
        # Grab escalation routing if it exists
        escalation = company_data.get('escalation') or {}
        regulator = escalation.get('regulator', 'the relevant regulatory authority')

        body = ""

        # THE REAL AI BRAIN (GEMINI 2.5)
        if USE_REAL_AI and client:
            try:
                prompt = f"""
                You are a fierce, highly professional data privacy lawyer in India.
                Draft a formal data erasure notice under the Digital Personal Data Protection (DPDP) Act 2025.
                
                Data Points:
                - Sender Email: {email}
                - Target Company: {company_name}
                - Deadline: {deadline_date} (90 days)
                - Section 16 Violation (No public DPO email found): {is_sec_16_violation}
                - Escalation Authority: {regulator}

                Rules:
                1. Cite Section 12 of the DPDP Act for the erasure demand.
                2. If Section 16 Violation is True, aggressively call out their failure to maintain a public DPO contact.
                3. Threaten escalation to {regulator} under Section 33.
                4. Return ONLY the body of the email. Do not include "Subject:" or introductory conversational filler.
                """

                # Generate content with Gemini 2.5 Flash
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                
                body = response.text.strip()
                print(f"[Agent 4 — Lawyer] Successfully drafted letter for {company_name} via Gemini 2.5!")
            
            except Exception as e:
                print(f"[Agent 4 — Lawyer] Gemini API failed for {company_name}: {str(e)}")
                raise e # Force terminal to show errors if it fails

        # THE FALLBACK (Used if USE_REAL_AI is False, or if the API crashes)
        if not body:
            body = f"To: Data Protection Officer / Grievance Officer\n{company_name}\n\n"
            body += f"I am writing to formally invoke my rights under the Digital Personal Data Protection Act 2025.\n\n"
            body += f"Under Section 12, I hereby demand the complete and permanent erasure of all personal data you hold pertaining to me.\n\n"
            
            if is_sec_16_violation:
                body += f"Furthermore, your failure to maintain a publicly accessible Data Protection Officer contact constitutes a violation of Section 16 of the DPDP Act. This has been noted as additional evidence of non-compliance.\n\n"
            
            body += f"Please confirm complete erasure within 90 days of this notice (by {deadline_date}). Non-compliance will be escalated to {regulator} and may result in penalties of up to Rs 250 crore under Section 33.\n\n"
            body += f"Regards,\n{email}"

        # Combine subject and body into the final letter object
        subject = f"Formal Data Erasure Request — DPDP Act 2025 — Section 12"
        
        letters.append({
            "company": company_name,
            "recipient_email": contact or None,
            "delivery_status": "missing_contact" if not contact else "ready",
            "subject": subject,
            "body": body,
            "dpdp_sections_cited": company_data.get('dpdp_sections', ["Section 12", "Section 33"]),
            "compliance_deadline_days": 90,
            "deadline_date": deadline_date,
            "escalation_regulator": regulator
        })

    return letters

# Master Agent 4 function
def run_lawyer(consent_expiry: list, shadow_profile: dict, email: str) -> dict:
    print("\n[Agent 4 — Lawyer] Drafting legal package...")
    
    legal_letters = generate_legal_letters(consent_expiry, email)
    
    # Extract unique deadlines
    deadlines = list(set([letter['deadline_date'] for letter in legal_letters]))
    
    print(f"[Agent 4 — Lawyer] Drafted {len(legal_letters)} legal letters.")
    print("[Agent 4 — Lawyer] Legal package complete.")

    return {
        "legal_letters": legal_letters,
        "compliance_deadlines": deadlines,
        "evidence_bundle": None # Placeholder: Handled on Day 6 by pdf_generator.py
    }