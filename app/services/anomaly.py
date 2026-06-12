import pandas as pd


def detect_anomalies(df: pd.DataFrame) -> list[dict]:
    results: list[dict] = []
    if df.empty:
        return results

    account_medians = df.groupby("account_id")["amount"].median()

    for _, row in df.iterrows():
        reasons = []
        account_median = account_medians.get(row["account_id"], 0.0)
        if account_median and row["amount"] > account_median * 3:
            reasons.append("Amount exceeds 3x median spend for account")

        foreign_currency = row["currency"] not in {"USD", "EUR", "GBP", "CAD", "AUD"}
        domestic_indicators = [
            "bank", "supermarket", "grocery", "fuel", "gas", "pharmacy", "utility", "train", "bus", "taxi",
        ]
        if foreign_currency and any(indicator in row["merchant"].lower() for indicator in domestic_indicators):
            reasons.append("Merchant appears domestic but transaction uses foreign currency")

        duplicate_mask = (
            (df["account_id"] == row["account_id"]) &
            (df["date"] == row["date"]) &
            (df["merchant"] == row["merchant"]) &
            (df["amount"] == row["amount"]) &
            (df["currency"] == row["currency"]) &
            (df["status"] == row["status"])
        )
        if df[duplicate_mask].shape[0] > 1:
            reasons.append("Suspicious duplicate transaction")

        for reason in reasons:
            results.append({"transaction_id": row["transaction_id"], "anomaly_reason": reason})

    return results
