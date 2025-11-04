# LLM-Powered Dividend Reconciliation System

This project automates the reconciliation of dividend data between NBIM’s internal systems and external custodians/brokers.
It detects and classifies reconciliation breaks, prioritizes them by importance, and drafts professional custodian tickets for external resolution.
Finally, all results are compiled into a single Excel report for transparency and auditability.

## Key Features

### Automated Reconciliation Detection

Compares internal and external datasets using rule-based logic.
Main focus is to detect differences in net cash.

### Multi-Agent Reasoning System

The automation pipeline is powered by three specialized LLM-based agents:

- Classifier Agent – analyzes each detected break and assigns a clear classification, as well as the most likely reason of the break.
- Prioritizer Agent – ranks reconciliation breaks by cash impact, confidence, and urgency.
- Remediation Agent – drafts short, formal custodian tickets whenever the issue is external (custodian-side).

Each agent is designed for clarity, precision, and explainability, ensuring the resulting outputs are human-readable and action-ready.

### Excel Report Generation

After all stages, the system merges every layer of analysis into an excel sheet with a structured overview of the findings for each reconciliation break.

## Pipeline overview

```
                    NBIM + Custody CSVs
                            │
                            ▼
                    Rule-based detector   →  Detected breaks
                            │
                            ▼
                    Classifier Agent      →  Classified breaks
                            │
                            ▼
       ┌─────────────── parallel ────────────────┐
       ▼                                         ▼
Prioritizer Agent                          Remediation Agent
→ Prioritized breaks                        → Drafted custodian tickets
       │
       ▼
Excel Report
```

## Project structure

```
NBIM_Case/
├── data/                         # Input CSV files (NBIM + Custody)
├── reports/                      # JSON and Excel outputs
├── drafted_tickets/              # Drafted custodian tickets (.txt/.md)
├── src/
│   ├── agents/
│   │   ├── classifier_agent.py
│   │   ├── prioritizer_agent.py
│   │   └── remediation_agent.py
│   ├── break_detector.py         # Rule-based break detector
│   ├── write_to_excel.py         # Combines reports into an excel file
│   ├── main.py                   # Orchestrates the entire pipeline
│   └── data_prcessing.py
└── README.md
```
