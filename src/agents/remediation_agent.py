import os, json
from typing import List, Dict, Any
from openai import OpenAI

# --- Compact glossary the agent will see in the system prompt ---
# Keep these short and unambiguous. Include only fields present in your data sample.
FIELD_GLOSSARY = {
    # Shared identifiers
    "COAC_EVENT_KEY": "Corporate action event identifier (dividend event).",
    "ISIN": "Security identifier.",
    "SEDOL": "UK security identifier.",
    "CUSTODIAN": "Custody bank identifier/name.",
    "BANK_ACCOUNT": "Internal bank/cash account at NBIM (where NBIM books the cash).",
    "CUSTODY": "Custody-side account reference (often equals bank account).",
    "EVENT_TYPE": "Corporate action type (e.g., DVCA).",

    # Dates
    "EX_DATE": "Market ex-dividend date (first day shares trade without entitlement).",
    "EVENT_EX_DATE": "Custody view of the ex-dividend date.",
    "RECORD_DATE": "Date issuer determines who is entitled.",
    "PAY_DATE": "Market/custody payment date.",
    "EVENT_PAYMENT_DATE": "Custody view of payment date.",
    "PAYMENT_DATE": "NBIM payment date.",

    # Currencies and FX
    "CURRENCY_QC": "Quotation currency of dividend (declared currency).",
    "CURRENCY_SC": "Settlement currency (cash paid in).",
    "SETTLEMENT_CURRENCY": "Synonym of settlement currency.",
    "SETTLED_CURRENCY": "Synonym of settlement currency.",
    "FX_RATE": "Custody FX rate for QC to SC conversion.",
    "AVG_FX_RATE_QUOTATION_TO_PORTFOLIO": "NBIM internal FX rate for QC to Portfolio conversion.",

    # Amounts & rates
    "DIV_RATE": "Dividend per share in quotation currency.",
    "NOMINAL_BASIS": "Shares eligible for dividend (entitlement quantity).",
    "HOLDING_QUANTITY": "Shares actually held at custody (NOMINAL_BASIS minus LOAN_QUANTITY).",
    "LOAN_QUANTITY": "Shares lent out at record date.",
    "LENDING_PERCENTAGE": "Percent of position lent.",
    "GROSS_AMOUNT_QC": "Gross dividend in quotation currency.",
    "NET_AMOUNT_QC": "Net dividend in quotation currency (after tax).",
    "NET_AMOUNT_SC": "Net dividend in settlement currency (cash paid).",
    "NET_AMOUNT_PORTFOLIO": "NBIM net dividend in portfolio/base currency (internal).",
    "GROSS_AMOUNT_PORTFOLIO": "NBIM gross dividend in portfolio/base currency (internal).",
    "TAX": "Total tax amount withheld (custody).",
    "WTHTAX_COST_QUOTATION": "NBIM withholding tax amount in QC.",
    "WTHTAX_COST_SETTLEMENT": "NBIM withholding tax amount in SC.",
    "WTHTAX_COST_PORTFOLIO": "NBIM withholding tax amount in portfolio currency.",
    "WTHTAX_RATE": "Withholding tax rate (NBIM).",
    "TAX_RATE": "Tax rate (custody or NBIM total tax).",
    "TOTAL_TAX_RATE": "NBIM total tax rate (incl. local where applicable).",

    # Other
    "INSTRUMENT_DESCRIPTION": "Security name.",
    "ORGANISATION_NAME": "Issuer/company name.",
    "IS_CROSS_CURRENCY_REVERSAL": "Custody flag for cross-currency reversal scenarios.",
    "POSSIBLE_RESTITUTION_PAYMENT": "Custody flag: restitution may be due.",
    "POSSIBLE_RESTITUTION_AMOUNT": "Custody amount potentially due as restitution.",
    "ADR_FEE": "ADR fee in custody.",
    "ADR_FEE_RATE": "ADR fee rate.",
}

CLASS_LABELS = [
    "AMOUNT_MISMATCH_TAX",
    "AMOUNT_MISMATCH_RATE",
    "QUANTITY_OR_LENDING_MISMATCH",
    "DATE_MISMATCH",
    "MISSING_RECORD",
    "DUPLICATE_OR_PARTIAL",
    "OTHER"
]

SYSTEM_PROMPT = f"""You are an expert financial operations analyst at NBIM’s Corporate Actions Reconciliation Team.
Your job is to write formal, concise, and professional custodian tickets based on structured reconciliation break data.
Your Goal
Transform each reconciliation break into a short, polished ticket suitable for sending to the custodian as an email or .txt document.
Each ticket must sound as if written by a human analyst, not an AI — clear, polite, and factual.
Output Format
Produce markdown!
Keep it under 250 words unless more detail is strictly necessary.
Structure:
To: {{CUSTODIAN}} — Corporate Actions / Tax Desk
Subject: {{classification}} discrepancy — {{ORGANISATION_NAME}} (COAC {{COAC_EVENT_KEY}})
Body:
A short paragraph summarizing what the discrepancy is and its impact on cash (mention NET_AMOUNT_SC_DIFF if available).
A paragraph describing what NBIM observed vs what custody reported, using simple wording and approximate numbers.
A paragraph politely asking the custodian to review and confirm the relevant details, provide documentation, or advise on next steps.
Sign-off:
Kind regards,
Operations — Corporate Actions (Reconciliations)
NBIM

Writing Style
Sound human and professional, as if written by a senior operations analyst.
Be clear and concise: 2–3 short paragraphs maximum.
Use complete sentences; no bullet lists or numbered questions.
Maintain a neutral and courteous tone.
Never include internal keys like event_key.
Always reference: organization, COAC_EVENT_KEY, BANK_ACCOUNT, classification, and currency if present.
Examples of tone
We have identified a small tax-rate discrepancy between NBIM and custody for Samsung Electronics Co Ltd (COAC 960789012). Custody applied 20% withholding, while NBIM applied 25%, leading to a difference of 342.77 USD in the reported net cash. Please confirm the tax rate applied and provide supporting documentation or clarification if available.

FIELD GLOSSARY (concise):
{json.dumps(FIELD_GLOSSARY, ensure_ascii=False, indent=2)}
"""

USER_PROMPT_TEMPLATE = """Draft a formal custodian ticket as plain text using the following reconciliation-break JSON. Follow the system instructions and the required document structure. Only use facts from the JSON.
JSON: {break_json}

"""

def draft_custodian_ticket(
    breaks: Dict[str, Any],
    model: str = None
):
   
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    model = os.getenv("MODEL")
    
    break_json = json.dumps(breaks, ensure_ascii=False, indent=2)

    user = USER_PROMPT_TEMPLATE.format(
        break_json=break_json,
    )

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user},
            ],
            response_format={"type": "text"},
        )
        content = resp.choices[0].message.content or "{}"
        
    except Exception as e:
        print(e)

    return content

def draft_custodian_tickets(
    breaks: List[Dict[str, Any]],
    model: str = None
):
    """Draft custodian tickets for multiple breaks."""
    for b in breaks:
        if b.get("recommended_action") == "DRAFT_CUSTODIAN_TICKET":
            ticket = draft_custodian_ticket(b, model=model)
            
            # Write each ticket to a separate .txt file
            coac_key = b.get("COAC_EVENT_KEY", "unknown")
            bank_acc = b.get("BANK_ACCOUNT", "unknown")
            filename = f"drafted_tickets/custodian_ticket_{coac_key}_{bank_acc}.md"

            with open(filename, "w", encoding="utf-8") as f:
                f.write(ticket)

            print(f"✅ Wrote custodian ticket to {filename}")
