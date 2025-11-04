import pandas as pd
import math

#methods for csv loading and normalizing column names

def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";")
    return df

def normalize_columns(nbim, custody):
    nbim_map = {
        "EXDATE": "EX_DATE",
        "QUOTATION_CURRENCY": "CURRENCY_QC",
        "SETTLEMENT_CURRENCY": "CURRENCY_SC",
        "AVG_FX_RATE_QUOTATION_TO_PORTFOLIO": "FX_RATE",
        "TOTAL_TAX_RATE": "TAX_RATE",
        "GROSS_AMOUNT_QUOTATION": "GROSS_AMOUNT_QC",
        "GROSS_AMOUNT_QUOTATION": "GROSS_AMOUNT_QC",
        "NET_AMOUNT_QUOTATION": "NET_AMOUNT_QC",
        "NET_AMOUNT_SETTLEMENT": "NET_AMOUNT_SC",
        "DIVIDENDS_PER_SHARE": "DIV_RATE",
    }

    custody_map = {
        "CURRENCIES": "CURRENCY_QC",
        "SETTLED_CURRENCY": "CURRENCY_SC",
        "FX_RATE": "FX_RATE",
        "TAX_RATE": "TAX_RATE",
        "GROSS_AMOUNT": "GROSS_AMOUNT_QC",
        "NET_AMOUNT_SETTLED": "NET_AMOUNT_SC",
        "DIV_RATE": "DIV_RATE",
        "BANK_ACCOUNTS": "BANK_ACCOUNT",
    }

    nbim = nbim.rename(columns=nbim_map)
    custody = custody.rename(columns=custody_map)
    return nbim, custody


def get_all_keys(nbim: pd.DataFrame, custody: pd.DataFrame):
    """
    Find all unique combinations of COAC_EVENT_KEY and BANK_ACCOUNTS across both datasets.
    Returns (key_columns, combined_keys).
    """
    # Define key columns we care about
    key_cols = ["COAC_EVENT_KEY", "BANK_ACCOUNT"]

    # Build combined key tuples
    def make_keys(df: pd.DataFrame):
        if not key_cols:
            return set()
        cols = [c for c in key_cols if c in df.columns]
        if not cols:
            return set()
        tmp = df[cols].dropna().astype(str)
        return set(tuple(x) for x in tmp.itertuples(index=False, name=None))

    nb_keys = make_keys(nbim)
    cu_keys = make_keys(custody)

    combined = sorted(nb_keys | cu_keys)
    return key_cols, combined


def rows_for_key(df: pd.DataFrame, key_cols, key_tuple):
    """
    Get rows matching a composite key (e.g., (COAC_EVENT_KEY, BANK_ACCOUNTS)).
    Returns list of row dicts.
    """
    if not all(k in df.columns for k in key_cols):
        return []

    # Build boolean mask for all key columns
    mask = pd.Series(True, index=df.index)
    for col, val in zip(key_cols, key_tuple):
        mask &= df[col].astype(str) == str(val)

    sub = df[mask]
    recs = []
    for _, row in sub.iterrows():
        d = {c: (None if isinstance(v, float) and math.isnan(v) else v)
             for c, v in row.items()}
        recs.append(d)
    return recs
