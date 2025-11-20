import os
import sys
import pandas as pd
import numpy as np

# ---------------------------------------------
# Load DB connection from utils/
# ---------------------------------------------
CURRENT_DIR = os.path.dirname(__file__)
UTILS_DIR = os.path.join(CURRENT_DIR, "utils")
sys.path.append(UTILS_DIR)

from db_connect import get_connection

# ML models
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_squared_error


# ------------------------------------------------------------
# Helper: safe light encoding
# ------------------------------------------------------------
def safe_encode(df, col, top_k=5):
    """Encode only top K values of a categorical column."""
    if col not in df.columns:
        return df

    top_vals = df[col].value_counts().index[:top_k]
    for v in top_vals:
        name = f"{col}_{str(v).replace(' ', '_')[:40]}"
        df[name] = (df[col] == v).astype(int)

    df.drop(columns=[col], inplace=True, errors="ignore")
    return df


# ------------------------------------------------------------
# MAIN PIPELINE (PRICE PREDICTION)
# ------------------------------------------------------------
def run_models():
    print("\n======================================")
    print("     📈 PRODUCT PRICE PREDICTION")
    print("======================================")

    conn = get_connection()
    if conn is None:
        print("❌ No DB connection.")
        return

    print("✔ Connected to PostgreSQL")

    # ------------------------------------------------------------
    # Load ONLY the useful tables
    # ------------------------------------------------------------
    sales = pd.read_sql("SELECT * FROM fact_sales;", conn)
    menu = pd.read_sql("SELECT * FROM dim_menu_item;", conn)
    cat = pd.read_sql("SELECT * FROM dim_category;", conn)
    time = pd.read_sql("SELECT date, year, month, day, day_of_week FROM dim_time;", conn)

    print("✔ Tables loaded")
    print("   fact_sales:", sales.shape)
    print("   dim_menu_item:", menu.shape)
    print("   dim_category:", cat.shape)
    print("   dim_time:", time.shape)

    # ------------------------------------------------------------
    # Merge (product-focused)
    # ------------------------------------------------------------
    df = (
        sales
        .merge(menu, on="product_id", how="left")
        .merge(cat, on="category_id", how="left")
        .merge(time, on="date", how="left")
    )

    print(f"✔ Merge done. Final shape = {df.shape}")

    # ------------------------------------------------------------
    # Ensure price_sold exists!
    # ------------------------------------------------------------
    if "price_sold" not in df.columns:
        print("❌ ERROR: price_sold column missing — cannot train.")
        return

    if df["price_sold"].isna().all():
        print("❌ price_sold has no values — cannot train.")
        return

    # ------------------------------------------------------------
    # Optional filtering: Only product-level data
    # ------------------------------------------------------------
    df = df[
        [
            "product_id",
            "category_id",
            "units_sold",
            "revenue",
            "price_sold",
            "portion_size",
            "product_name",
            "category_name",
            "year",
            "month",
            "day_of_week",
        ]
    ]

    # ------------------------------------------------------------
    # Encode selected categoricals
    # ------------------------------------------------------------
    for col in ["product_name", "category_name", "portion_size"]:
        df = safe_encode(df, col, top_k=5)

    # ------------------------------------------------------------
    # Build numeric dataset
    # ------------------------------------------------------------
    df_numeric = df.select_dtypes(include=[np.number]).dropna()

    if df_numeric.shape[0] < 30:
        print("⚠ Dataset too small (<30 rows). Skipping ML.")
        return

    y = df_numeric["price_sold"]
    X = df_numeric.drop(columns=["price_sold"], errors="ignore")

    # ------------------------------------------------------------
    # Split
    # ------------------------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42
    )

    print("✔ Training dataset ready")
    print("   Features:", X_train.shape)
    print("   Target:", y_train.shape)

    # ------------------------------------------------------------
    # Models
    # ------------------------------------------------------------
    models = {
        "LinearRegression": LinearRegression(),
        "DecisionTree": DecisionTreeRegressor(max_depth=6, random_state=42)
    }

    print("\n=============================")
    print("        MODEL RESULTS")
    print("=============================")

    for name, model in models.items():
        model.fit(X_train, y_train)
        pred = model.predict(X_test)

        mse = mean_squared_error(y_test, pred)
        rmse = np.sqrt(mse)

        print(f"\n{name}:")
        print("   R²:", round(model.score(X_test, y_test), 4))
        print("   RMSE:", round(rmse, 4))
        print("   MSE:", round(mse, 4))

    print("\n✔ Price prediction pipeline completed successfully\n")


if __name__ == "__main__":
    run_models()
