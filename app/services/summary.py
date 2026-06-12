import pandas as pd


def create_summary_payload(df: pd.DataFrame, anomaly_objects: list[dict]) -> tuple[dict, dict]:
    total_spend_by_currency = (
        df.groupby("currency")["amount"].sum().round(2).to_dict()
    )
    merchant_spend = (
        df.groupby("merchant")["amount"].sum().sort_values(ascending=False).head(3)
    )
    top_3_merchants = [
        {"merchant": merchant, "amount": float(amount)}
        for merchant, amount in merchant_spend.items()
    ]
    anomaly_count = len(anomaly_objects)

    if anomaly_count > 5:
        risk_level = "high"
    elif anomaly_count > 2:
        risk_level = "medium"
    else:
        risk_level = "low"

    narrative = (
        f"Processed {len(df)} transactions across {len(total_spend_by_currency)} currencies. "
        f"Top merchants include {', '.join([item['merchant'] for item in top_3_merchants]) or 'none'}. "
        f"Detected {anomaly_count} anomaly{'ies' if anomaly_count != 1 else ''} with a {risk_level} risk profile."
    )

    category_breakdown = df["category"].value_counts().to_dict()

    summary_json = {
        "total_spend_by_currency": total_spend_by_currency,
        "top_3_merchants": top_3_merchants,
        "anomaly_count": anomaly_count,
        "risk_level": risk_level,
        "narrative": narrative,
    }

    return summary_json, category_breakdown
