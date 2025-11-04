import json
from pathlib import Path
import pandas as pd


def load_data(breaks_path: Path, classes_path: Path):
    with open(breaks_path, "r", encoding="utf-8") as f:
        data_a = json.load(f)
    with open(classes_path, "r", encoding="utf-8") as f:
        data_b = json.load(f)

    # A: {"reconciliation_breaks": [ {...}, ... ]}
    df_a = pd.DataFrame(data_a["reconciliation_breaks"])

    # B: [ {...}, {...} ]
    df_b = pd.DataFrame(data_b)

    # --- Ensure join keys exist on both sides with the SAME names & dtypes ---
    # Left side uses uppercase keys
    # Right side may use lowercase 'coac_event_key'/'bank_account' or only 'event_key'
    if "coac_event_key" in df_b.columns:
        df_b = df_b.rename(columns={"coac_event_key": "COAC_EVENT_KEY"})
    if "bank_account" in df_b.columns:
        df_b = df_b.rename(columns={"bank_account": "BANK_ACCOUNT"})

    # If either side only has 'event_key' like "123|456", split it
    if "event_key" in df_b.columns and (("COAC_EVENT_KEY" not in df_b.columns) or ("BANK_ACCOUNT" not in df_b.columns)):
        parts = df_b["event_key"].astype(str).str.split("|", n=1, expand=True)
        df_b["COAC_EVENT_KEY"] = parts[0]
        df_b["BANK_ACCOUNT"] = parts[1]

    # Normalize dtypes of join keys to string on BOTH sides
    if "COAC_EVENT_KEY" in df_a.columns:
        df_a["COAC_EVENT_KEY"] = df_a["COAC_EVENT_KEY"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    if "BANK_ACCOUNT" in df_a.columns:
        df_a["BANK_ACCOUNT"] = df_a["BANK_ACCOUNT"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    if "COAC_EVENT_KEY" in df_b.columns:
        df_b["COAC_EVENT_KEY"] = df_b["COAC_EVENT_KEY"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    if "BANK_ACCOUNT" in df_b.columns:
        df_b["BANK_ACCOUNT"] = df_b["BANK_ACCOUNT"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    # ------------------------------------------------------------------------

    # Flatten nested action_params in df_b if present
    if "action_params" in df_b.columns:
        df_b["evidence"] = df_b["action_params"].apply(
            lambda ap: ap.get("evidence") if isinstance(ap, dict) else None
        )
        df_b["notes"] = df_b["action_params"].apply(
            lambda ap: ap.get("notes") if isinstance(ap, dict) else None
        )
        df_b = df_b.drop(columns=["action_params"])

    return df_a, df_b


def combine(df_a: pd.DataFrame, df_b: pd.DataFrame) -> pd.DataFrame:
    # Outer join so nothing is lost if one side is missing
    combined = pd.merge(
        df_a,
        df_b,
        on=["COAC_EVENT_KEY", "BANK_ACCOUNT"],
        how="outer",
        validate="one_to_one",
        suffixes=("", "_b"),
    )

    # Make key names consistent with the rest of the code (lowercase)
    combined = combined.rename(columns={
        "COAC_EVENT_KEY": "coac_event_key",
        "BANK_ACCOUNT": "bank_account"
    })

    # Reorder columns (include only those that exist)
    col_order = [
        "priority","coac_event_key", "bank_account", "custodian", "organisation_name", "classification", "NET_AMOUNT_SC_DIFF", "SETTLEMENT_CURRENCY",
        "description", "confidence",
        "recommended_action", "notes",
    ]
    cols = [c for c in col_order if c in combined.columns]
    combined = combined[cols]

    # Sort: priority asc
    if "priority" in combined.columns and "NET_AMOUNT_SC_DIFF" in combined.columns:
        combined = combined.sort_values(
            ["priority", "NET_AMOUNT_SC_DIFF"], ascending=[True, False]
        )

    return combined


def write_excel(df: pd.DataFrame, out_path: Path):
    with pd.ExcelWriter(out_path, engine="xlsxwriter") as writer:
        # Main sheet
        sheet_name = "Combined"
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        wb = writer.book
        ws = writer.sheets[sheet_name]

        # Column widths
        width_map = {
            "priority": 10, "priority_label": 14, "reason": 60,
            "coac_event_key": 16, "bank_account": 16, "event_key": 22,
            "classification": 24, "description": 80, "confidence": 12,
            "recommended_action": 26, "evidence": 48, "notes": 48,
            "NET_AMOUNT_SC_DIFF": 18, "SETTLEMENT_CURRENCY": 10,
        }
        for idx, col in enumerate(df.columns):
            ws.set_column(idx, idx, width_map.get(col, 18))

        # Header format
        header_fmt = wb.add_format({"bold": True, "text_wrap": True})
        for col_idx, col_name in enumerate(df.columns):
            ws.write(0, col_idx, col_name, header_fmt)



def combine_and_export(breaks_path: str = "reports/prioritized_breaks.json", classes_path: str = "reports/classified_reconciliation_breaks.json", out_path: str = "reports/reconciliation_breaks_combined.xlsx"):
    df_a, df_b = load_data(Path(breaks_path), Path(classes_path))
    combined = combine(df_a, df_b)
    write_excel(combined, Path(out_path))
    return out_path
