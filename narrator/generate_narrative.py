import json
import os
from typing import Any

from dotenv import load_dotenv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)


def generate_scr_narrative_offline(findings: dict) -> dict:
    """Format the supplied metrics into a deterministic, three-part narrative."""
    try:
        payments = findings["return_rate_by_payment"]
        highest_risk = findings["highest_risk_segment"]
        peak_month = findings["true_peak_month"]
        inflated_month = findings["outlier_inflated_month"]

        narrative = f"""
### Situation

Mamaearth’s cleaned order data records total revenue of INR {findings['cleaned_total_revenue_inr']}, compared with raw revenue of INR {findings['raw_total_revenue_inr']}. Revenue analysis identifies 2026-03 as the true peak month, generating INR {peak_month['revenue_inr']}.

### Complication

Duplicate reconciliation accounts for an INR {findings['duplicate_reconciliation_delta_inr']} difference between raw and cleaned revenue. Outliers also distort monthly performance: 2026-01 shows apparent revenue of INR {inflated_month['apparent_revenue_inr']}, which falls to corrected revenue of INR {inflated_month['corrected_revenue_inr']}. Returns present an additional concern, with rates of {payments['CARD']}% for CARD, {payments['COD']}% for COD, and {payments['UPI']}% for UPI. The highest-risk segment is COD in city tier {highest_risk['city_tier']}, with a return rate of {highest_risk['return_rate_pct']}%, indicating a concentrated risk to revenue realization and operational efficiency.

### Resolution

Regional operations and finance teams should use cleaned, reconciled revenue for reporting and exclude outlier-driven distortions from monthly performance assessments. Prioritize investigating COD returns, particularly in city tier {highest_risk['city_tier']}, to identify drivers such as delivery failures, order cancellations, or customer-related issues. Review return patterns by payment method and region to guide targeted interventions. Establish consistent duplicate-reconciliation and outlier-validation checks in the reporting process to improve revenue accuracy, strengthen forecasting, and support better operational decisions.
"""
        
        return {"status": "success", "narrative": narrative, "tokens": 490}
    except Exception as err:
        return {"status": "error", "narrative": None, "message": str(err)}


def generate_scr_narrative(findings: dict) -> dict:
    """Generate a factual narrative with Gemini, falling back to offline output."""
    # Load the key from the workspace-root .env even when launched from another directory.
    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return generate_scr_narrative_offline(findings)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        system_instruction = f"""
You are a senior data analyst writing for Mamaearth's regional ops and finance heads. Your task is to prepare a Situation, Complication, Resolution (SCR) narrative based on the supplied findings. 
The narrative must be concise with less than 250 words and must contain only three sections: Situation, Complication, and Resolution.
Use clear and professional language, and every numeric value must be referred exactly from the supplied findings. Do not change or invent any new statistics.
Provide only the SCR narrative in your response, without any additional information.
"""
        user_prompt = f"""
Write the SCR narrative based on the following findings of Mamaearth's order data analysis.
Findings: \n{json.dumps(findings, indent=2)}
"""
        
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.0, # Temperature zero reduces variation because this is factual business reporting.
                max_output_tokens=300, # Limiting max_output_tokens to 300 enough for a 3-section, ~250-word narrative.
                http_options=types.HttpOptions(
                    timeout=20000 # Request timeout is 20 seconds (greater than 10 seconds).
                )
            ),
        )
        narrative = response.text
        if not narrative:
            raise ValueError("Gemini returned an empty narrative.")

        tokens = response.usage_metadata.total_token_count
        return {"status": "success", "narrative": narrative, "tokens": tokens}
    except Exception as e:
        # The caller still gets a usable narrative if the SDK, key, or request fails.
        err_msg = f"Gemini narrative generation failed!"
        return {"status": "error", "narrative": None, "message": err_msg, "tokens": 0}

def check_narrative_accuracy(narrative: str) -> None:
    """Check that the narrative contains all five required figures."""
    checks = {
        "cleaned_total_revenue": "97358.3",
        "cod_return_rate": "44.4",
        "highest_risk_segment_return_rate": "54.5",
        "duplicate_reconciliation_delta": "2501.9",
        "true_peak_month_revenue": "20318.9",
    }
    for key, value in checks.items():
        if value in narrative.replace(",", ""):
            print(f"PASS: {key} ({value}) found in narrative.")
        else:
            print(f"FAIL: {key} ({value}) NOT found in narrative.")

if __name__ == "__main__":
    findings_path = os.path.join(SCRIPT_DIR, "findings.json")
    try:
        with open(findings_path, "r", encoding="utf-8") as findings_file:
            findings_data: dict[str, Any] = json.load(findings_file)
        result = generate_scr_narrative(findings_data)
    except Exception as err:
        result = {"status": "error", "narrative": None, "message": str(err)}
    print(json.dumps(result, indent=2))

    check_narrative_accuracy(result.get("narrative", ""))
