import os
import json
from openai import OpenAI
import pandas as pd
import asyncio
import time
from data_prcessing import load_csv, normalize_columns, get_events
from break_detector import detect_breaks
from agents.classifier_agent import classify_reconciliation_breaks
from agents.prioritizer_agent import prioritize_breaks
from agents.remediation_agent import draft_custodian_tickets
from write_to_excel import combine_and_export


async def run_both(items: list):
    # Run both agents concurrently
    
    prioritize_task = asyncio.create_task(asyncio.to_thread(prioritize_breaks, items))
    draft_task = asyncio.create_task(asyncio.to_thread(draft_custodian_tickets, items))

    prioritize_result, draft_result = await asyncio.gather(prioritize_task, draft_task)
    return prioritize_result


async def main():

    # --- File paths ---
    NBIM_CSV = "data/NBIM_Dividend_Bookings 1 (2).csv"
    CUSTODY_CSV = "data/CUSTODY_Dividend_Bookings 1 (2).csv"


    # --- Load and normalize ---
    nbim = load_csv(NBIM_CSV)
    custody = load_csv(CUSTODY_CSV)
    nbim, custody = normalize_columns(nbim, custody)



    # --- Prepare event objects ---
    events = get_events(nbim, custody)
    

    # --- Detect breaks ---
    breaks = detect_breaks(events)
    print(f"Detected {len(breaks)} reconciliation breaks.")

    # --- Classify breaks ---
    classified = classify_reconciliation_breaks(breaks)
    
    with open("reports/classified_reconciliation_breaks.json", "w", encoding="utf-8") as f:
            json.dump(classified, f, ensure_ascii=False, indent=2)

    print(f"✅ Wrote {len(classified)} classified breaks to reports/classified_reconciliation_breaks.json")

    # --- Prioritize breaks & draft tickets ---
    prioritized = await run_both(classified)

    with open("reports/prioritized_breaks.json", "w", encoding="utf-8") as f:
        json.dump(prioritized, f, ensure_ascii=False, indent=2)

    print(f"✅ Wrote {len(prioritized)} prioritized breaks to reports/prioritized_breaks.json")

    # --- Combine into Excel ---
    time.sleep(0.5)  # wait a moment for file write to complete
    combine_and_export()



if __name__ == "__main__":
    asyncio.run(main())