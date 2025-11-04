import os, json
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

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

SYSTEM_PROMPT = f"""You are a senior dividend reconciliation analyst.
You receive JSON objects ('breaks') where NBIM and Custody disagree on the net cash received.
Your job: classify and recommend actions for each break.

IMPORTANT SCOPE:
- Primary comparison: NBIM NET_AMOUNT_SC vs Custody NET_AMOUNT_SC.
- Do NOT compare NBIM AVG_FX_RATE_QUOTATION_TO_PORTFOLIO with Custody FX_RATE; those convert to different targets.
- Use other fields (e.g., TAX_RATE, DIV_RATE, NOMINAL_BASIS, dates) only as context to explain the cash mismatch.

CLASS LABELS (choose one):
{CLASS_LABELS}


RECOMMENDED ACTION (choose one):
- AUTO_CLOSE_WITHIN_TOL   (if trivial or timing-only and likely to clear)
- DRAFT_CUSTODIAN_TICKET  (if custody-side seems incorrect or needs investigation)
- PROPOSE_NBIM_CORRECTION (if NBIM-side setup looks wrong)
- ESCALATE                (if large/critical and uncertain or multi-factor)

Return strict JSON with: event_key, COAC_EVENT_KEY, BANK_ACCOUNT, CUSTODIAN, ORGANISATION_NAME, classification, description (1–2 sentences), confidence (0–1),
recommended_action, action_params {{ evidence: [..], notes: "..." }}, NET_AMOUNT_SC_DIFF, SETTLEMENT_CURRENCY.

FIELD GLOSSARY (concise):
{json.dumps(FIELD_GLOSSARY, ensure_ascii=False, indent=2)}
"""

USER_PROMPT_TEMPLATE = """Break input (cash mismatch already detected):
{break_json}

"""

def classify_reconciliation_breaks(
    breaks: List[Dict[str, Any]],
    model: str = None
):
    """Classify and prioritize reconciliation breaks using an LLM."""
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    model = os.getenv("MODEL")

    results: List[Dict[str, Any]] = []

    for b in breaks:
    
        # Keep the entire break payload (nbim_rows, custody_rows, NET_AMOUNT_SC_DIFF, etc.)
        break_json = json.dumps(b, ensure_ascii=False, indent=2)

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
                response_format={"type": "json_object"},
            )
            content = resp.choices[0].message.content or "{}"
            parsed = json.loads(content)
        except Exception as e:
            print(e)

        results.append(parsed)

    return results
