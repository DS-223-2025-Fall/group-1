import os
import sys
from typing import Optional

import numpy as np
import pandas as pd
from joblib import load as joblib_load

# --- project root on sys.path ---
if "__file__" in globals():
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
else:
    CURRENT_DIR = os.getcwd()

PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
sys.path.append(PROJECT_ROOT)

DATA_DIR = os.path.join(PROJECT_ROOT, "etl", "database", "data")

# Use an absolute path inside analytics/outputs so the model is easy to locate
MODEL_PATH = os.path.join(CURRENT_DIR, "outputs", "random_forest_model.pkl")


def load_model():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file not found at: {MODEL_PATH}")
    return joblib_load(MODEL_PATH)


# Reference vocabularies captured from the training snapshots so the CLI works
# out-of-the-box without needing to touch the CSVs at runtime.
REFERENCE_VALUES = {
    "product_name": [],
    "location": [
        "Ajapnyak",
        "Arabkir",
        "Kentron",
        "Malatia-Sebastia",
        "Nor Nork",
    ],
    "type": [
        "bakery_cafe",
        "bar_bistro",
        "bar_restaurant",
        "bistro",
        "brewpub",
        "cafe",
        "cafe_bistro",
        "cafe_dessert",
        "cafe_restaurant",
        "coffee_chain",
        "coffee_house",
        "fast_food",
        "gastropub",
        "healthy_cafe",
        "italian_rest",
        "pizzeria",
        "restaurant",
        "wine_bar",
    ],
    "age_group": ["0-17", "18-24", "25-34", "35-44", "45-54", "55+"],
    "portion_bucket": ["small", "medium", "large"],
}

PRODUCT_FEATURES = {}


def _load_product_reference() -> dict:
    menu_path = os.path.join(DATA_DIR, "dim_menu_item.csv")
    if not os.path.exists(menu_path):
        raise FileNotFoundError(f"Menu metadata not found at {menu_path}")

    df = pd.read_csv(menu_path)
    required = [
        "product_name",
        "category_id",
        "base_price",
        "cost",
        "portion_size",
    ]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise RuntimeError(f"Menu metadata missing columns: {missing}")

    meta = df[required].copy()
    meta = meta.dropna(subset=["product_name", "portion_size"])

    # Parse numeric fields
    extracted = meta["portion_size"].astype(str).str.extract(r"(\d+\.?\d*)")[0]
    meta["portion_numeric"] = pd.to_numeric(extracted, errors="coerce")
    for field in ("base_price", "cost"):
        meta[field] = pd.to_numeric(meta[field], errors="coerce")

    for field in ("portion_numeric", "base_price", "cost"):
        median_val = meta[field].median()
        if pd.isna(median_val):
            median_val = 0.0
        meta[field] = meta[field].fillna(median_val)

    # Portion buckets consistent with training logic
    min_v = meta["portion_numeric"].min()
    max_v = meta["portion_numeric"].max()
    span = max_v - min_v
    if pd.isna(span) or span <= 0:
        meta["portion_bucket"] = "medium"
    else:
        eps = max(span * 1e-6, 1e-9)
        bins = np.linspace(min_v - eps, max_v + eps, num=4)
        meta["portion_bucket"] = pd.cut(
            meta["portion_numeric"], bins=bins, labels=["small", "medium", "large"]
        )
        meta["portion_bucket"] = meta["portion_bucket"].astype(str).replace("nan", "medium")

    meta["category_id"] = meta["category_id"].astype(str)

    # Keep a single record per product name (first occurrence is fine)
    meta = meta.sort_values("product_name").drop_duplicates("product_name", keep="first")

    product_map = {}
    for _, row in meta.iterrows():
        product_map[row["product_name"]] = {
            "category_id": row["category_id"],
            "portion_bucket": row["portion_bucket"],
            "portion_numeric": float(row["portion_numeric"]),
            "base_price": float(row["base_price"]),
            "cost": float(row["cost"]),
        }

    return product_map


PRODUCT_FEATURES = _load_product_reference()
REFERENCE_VALUES["product_name"] = sorted(PRODUCT_FEATURES.keys())


def _example_suffix(field: str, max_examples: int = 3) -> str:
    options = REFERENCE_VALUES.get(field, [])
    if not options:
        return ""
    preview = ", ".join(options[:max_examples])
    return f" (e.g. {preview})"


def _suggest_alternative(bad_input: str, field: str) -> Optional[str]:
    options = REFERENCE_VALUES.get(field, [])
    if not options:
        return None
    first_letter = bad_input[:1].lower()
    same_letter = [opt for opt in options if opt.lower().startswith(first_letter)]
    if same_letter:
        return same_letter[0]
    return options[0]


def _prompt_with_validation(field: str, prompt_label: str, default: Optional[str] = None) -> str:
    suffix = _example_suffix(field)
    prompt = f"  {prompt_label}{suffix}"
    if default is not None:
        prompt += f" [{default}]"
    prompt += ": "
    valid_values = REFERENCE_VALUES.get(field, [])
    normalized = {val.lower(): val for val in valid_values}

    while True:
        value = input(prompt).strip()
        if not value:
            if default is not None:
                return default
            print("    Please enter a value.")
            continue
        norm_value = value.lower()
        if not valid_values:
            return value
        if norm_value in normalized:
            return normalized[norm_value]

        suggestion = _suggest_alternative(value, field)
        if not suggestion:
            print(f"    '{value}' is not recognized. Please try again.")
            continue
        confirm = input(
            f"    '{value}' is not a known {field}. Use '{suggestion}' instead? [Y/n]: "
        ).strip().lower()
        if confirm in ("", "y", "yes"):
            return suggestion
        print("    Let's try again.")


def _prompt_numeric(prompt_label: str, default: float) -> float:
    prompt = f"  {prompt_label} [{round(float(default), 2)}]: "
    while True:
        value = input(prompt).strip()
        if not value:
            return float(default)
        try:
            return float(value)
        except ValueError:
            print("    Please enter a numeric value (e.g. 250 or 3990).")


def ask_user_input():
    """
    Ask the user for feature values in the terminal and return a one-row DataFrame
    that matches the RF training schema.
    """
    print("Enter feature values for price prediction:")
    product_name = _prompt_with_validation("product_name", "product_name")
    if product_name not in PRODUCT_FEATURES:
        raise ValueError(f"No metadata found for '{product_name}'.")
    product_meta = PRODUCT_FEATURES[product_name]

    location = _prompt_with_validation("location", "location")
    rest_type = _prompt_with_validation("type", "type")
    age_group = _prompt_with_validation("age_group", "age_group")

    portion_bucket = _prompt_with_validation(
        "portion_bucket", "portion_bucket", product_meta["portion_bucket"]
    )
    portion_numeric = _prompt_numeric("portion_numeric (grams/ml)", product_meta["portion_numeric"])
    base_price = _prompt_numeric("base_price", product_meta["base_price"])
    cost = _prompt_numeric("cost", product_meta["cost"])

    data = {
        "location": [location],
        "type": [rest_type],
        "age_group": [age_group],
        "category_id": [product_meta["category_id"]],
        "portion_bucket": [portion_bucket],
        "portion_numeric": [portion_numeric],
        "base_price": [base_price],
        "cost": [cost],
    }
    X = pd.DataFrame(data)
    return X


def prepare_features_for_rf(rf_model, X_raw: pd.DataFrame):
    """
    Apply the same encoding logic as in training:
    - get_dummies (keep all levels so single-row input keeps its indicator)
    - reindex columns to rf_model.feature_names_in_
    """
    # Don't drop the first level here; otherwise a single-row input loses
    # every dummy column and we end up feeding zeros into the model.
    X_enc = pd.get_dummies(X_raw, drop_first=False)

    # feature_names_in_ is stored by sklearn for models trained on a DataFrame
    expected_cols = list(rf_model.feature_names_in_)
    X_enc = X_enc.reindex(columns=expected_cols, fill_value=0)

    return X_enc


def main():
    rf = load_model()
    while True:
        X_raw = ask_user_input()
        X_enc = prepare_features_for_rf(rf, X_raw)

        pred = rf.predict(X_enc)[0]
        print("\n==============================")
        print(" Predicted price_sold:", round(float(pred), 2))
        print("==============================\n")

        again = input("Predict another item? [y/N]: ").strip().lower()
        if again not in ("y", "yes"):
            break
        print()


if __name__ == "__main__":
    main()
