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

- Classifier Agent – analyzes each detected break and assigns a clear classification, most likely reason, and a suggested action.
- Prioritizer Agent – ranks reconciliation breaks by cash impact, confidence, and urgency.
- Remediation Agent – drafts short, formal custodian tickets whenever the issue is external (custodian-side).

Each agent is designed for clarity, precision, and explainability, ensuring the resulting outputs are human-readable and action-ready.

### Documentation Generation

After all processing stages, the system compiles:

- Excel report that presents each reconciliation break in a clear, structured format. This report focuses on the key insights and metrics needed for review.
- Detailed JSON reports containing the full metadata and reasoning behind each classification and prioritization.
- Custodian ticket drafts for all reconciliation breaks identified as likely caused by external parties such as custodians or brokers.

The result is a streamlined and auditable workflow where:

- The Excel file provides a concise, high-level operational overview.
- The JSON reports retain full analytical detail for traceability.
- The drafted tickets enable rapid communication and resolution with external stakeholders.

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
