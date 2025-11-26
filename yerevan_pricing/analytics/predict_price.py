import os
import sys
import pickle
from typing import Optional
import pandas as pd

# --- project root on sys.path ---
if "__file__" in globals():
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
else:
    CURRENT_DIR = os.getcwd()

PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
sys.path.append(PROJECT_ROOT)

# Use an absolute path inside analytics/outputs so the model is easy to locate
MODEL_PATH = os.path.join(CURRENT_DIR, "outputs", "random_forest_model.pkl")


def load_model():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file not found at: {MODEL_PATH}")
    with open(MODEL_PATH, "rb") as f:
        rf = pickle.load(f)
    return rf


# Reference vocabularies captured from the training snapshots so the CLI works
# out-of-the-box without needing to touch the CSVs at runtime.
REFERENCE_VALUES = {
    "product_name": [
        "Aperol Spritz",
        "Beef Steak",
        "Black Tea",
        "Brownie",
        "Bruschetta",
        "Cappuccino",
        "Caprese Croissant",
        "Cheesecake",
        "Chicken Caesar",
        "Chicken Pasta",
        "Chicken Sandwich",
        "Chocolate Mousse",
        "Club Sandwich",
        "Cold Brew",
        "Eggs Benedict",
        "Espresso",
        "Flat White",
        "Fresh Orange Juice",
        "Greek Salad",
        "Guacamole Toast",
        "Herbal Tea",
        "Hummus Plate",
        "Latte",
        "Macchiato",
        "Margarita Pizza",
        "Matcha Latte",
        "Mineral Water",
        "Mojito",
        "Omelet / Scramble",
        "Parma Pizza",
        "Quattro Formaggi",
        "Raf",
        "Ricotta Croissant",
        "Salmon Croissant",
        "Salmon Steak",
        "Tarte Tatin",
        "Ventricina Pizza",
    ],
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


def _prompt_with_validation(field: str, prompt_label: str) -> str:
    suffix = _example_suffix(field)
    prompt = f"  {prompt_label}{suffix}: "
    valid_values = REFERENCE_VALUES.get(field, [])
    normalized = {val.lower(): val for val in valid_values}

    while True:
        value = input(prompt).strip()
        if not value:
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


def ask_user_input():
    """
    Ask the user for feature values in the terminal and return a one-row DataFrame.
    These must match the features used in training: product_name, location, type,
    portion_bucket, age_group.
    """
    print("Enter feature values for price prediction:")
    product_name = _prompt_with_validation("product_name", "product_name")
    location = _prompt_with_validation("location", "location")
    rest_type = _prompt_with_validation("type", "type")
    portion_bucket = _prompt_with_validation("portion_bucket", "portion_bucket")
    age_group = _prompt_with_validation("age_group", "age_group")

    data = {
        "product_name": [product_name],
        "location": [location],
        "type": [rest_type],
        "portion_bucket": [portion_bucket],
        "age_group": [age_group],
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
