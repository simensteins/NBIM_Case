# LLM-Powered Dividend Reconciliation System

This project automates the reconciliation of dividend data between NBIM’s internal systems and external custodians/brokers.
It detects and classifies reconciliation breaks, prioritizes them by importance, and drafts professional custodian tickets for external resolution.
Finally, all results are compiled into a single Excel report for transparency and auditability.

## Key Features

### Automated Reconciliation Detection

Compares internal (NBIM) and external (custody) datasets using rule-based logic.
Main focus is to detect differences in net cash.

### Multi-Agent Reasoning System

The automation pipeline is powered by three specialized LLM-based agents:

- Classifier Agent – analyzes each detected break and assigns a clear classification (e.g., AMOUNT_MISMATCH_TAX).
- Prioritizer Agent – ranks reconciliation breaks by cash impact, confidence, and urgency.
- Remediation Agent – drafts short, formal custodian tickets whenever the issue is external (custodian-side).

Each agent is designed for clarity, precision, and explainability, ensuring the resulting outputs are human-readable and action-ready.

### Excel Report Generation

After all stages, the system merges every layer of analysis into an excel sheet with a structured overview of the findings for each reconciliation break.

## Pipeline overview

## Project structure

NBIM_Case/
├── data/ # Input CSV files (NBIM + Custody)
├── reports/ # JSON and Excel outputs
├── drafted_tickets/ # Drafted custodian tickets (.txt/.md)
├── src/
│ ├── agents/
│ │ ├── classifier_agent.py
│ │ ├── prioritizer_agent.py
│ │ └── remediation_agent.py
│ ├── break_detector.py
│ ├── write_to_excel.py
│ ├── main.py # Orchestrates the entire pipeline
│ └── data_prcessing.py
└── README.md
