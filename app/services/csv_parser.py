import io
import re
import uuid
from typing import List

import pandas as pd

from app.utils.logger import get_logger

logger = get_logger(__name__)

DOMESTIC_CATEGORY_KEYWORDS = {
    "Food": ["restaurant", "cafe", "coffee", "pizza", "burger", "diner", "eatery", "bakery"],
    "Shopping": ["mall", "store", "amazon", "shop", "boutique", "market"],
    "Travel": ["airlines", "hotel", "airbnb", "travel", "uber", "lyft"],
    "Transport": ["transport", "bus", "train", "taxi", "metro", "rail", "uber", "lyft"],
    "Utilities": ["electric", "water", "gas", "internet", "phone", "utility"],
    "Cash Withdrawal": ["atm", "withdrawal", "bank"],
    "Entertainment": ["movie", "cinema", "concert", "theater", "netflix", "spotify"],
}

CURRENCY_CLEANER = re.compile(r"[^0-9.\-]+")

REQUIRED_COLUMNS = ["account_id", "date", "merchant", "amount", "currency", "status"]


def normalize_category(merchant: str) -> str:
    merchant_lower = merchant.lower()
    for category, keywords in DOMESTIC_CATEGORY_KEYWORDS.items():
        if any(keyword in merchant_lower for keyword in keywords):
            return category
    return "Other"


def clean_amount(value: object) -> float:
    if pd.isna(value):
        raise ValueError("Amount value is missing")
    amount_text = str(value)
    cleaned = CURRENCY_CLEANER.sub("", amount_text)
    if cleaned.count(".") > 1:
        cleaned = cleaned.replace(".", "", cleaned.count(".") - 1)
    return float(cleaned)


def load_transactions(contents: str) -> pd.DataFrame:
    df = pd.read_csv(io.StringIO(contents))
    df.columns = [str(column).strip().lower() for column in df.columns]

    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")

    df = df[REQUIRED_COLUMNS + [col for col in df.columns if col not in REQUIRED_COLUMNS]]
    df = df.rename(columns={"amount": "amount", "merchant": "merchant"})

    df["merchant"] = df["merchant"].fillna("Unknown Merchant").astype(str).str.strip()
    df["currency"] = df["currency"].fillna("USD").astype(str).str.strip().str.upper()
    df["status"] = df["status"].fillna("UNKNOWN").astype(str).str.strip().str.upper()

    df["amount"] = df["amount"].apply(clean_amount)
    df["date"] = pd.to_datetime(df["date"], errors="coerce", infer_datetime_format=True)
    df = df[df["date"].notna()].copy()
    df["date"] = df["date"].dt.date

    if "category" in df.columns:
        df["category"] = df["category"].fillna("Other").astype(str).str.title()
    else:
        df["category"] = "Other"

    df.loc[df["category"].isin(["", "nan", "none"]), "category"] = "Other"
    df.loc[df["category"] == "Other", "category"] = df.loc[df["category"] == "Other", "merchant"].apply(normalize_category)
    df["category"] = df["category"].replace({None: "Other"}).astype(str).str.title()
    df.loc[df["category"].str.strip() == "", "category"] = "Other"

    df = df.drop_duplicates(subset=["account_id", "date", "merchant", "amount", "currency", "category", "status"])
    df = df.reset_index(drop=True)
    df["transaction_id"] = [str(uuid.uuid4()) for _ in range(len(df))]

    return df[["transaction_id", "account_id", "date", "merchant", "amount", "currency", "category", "status"]]
