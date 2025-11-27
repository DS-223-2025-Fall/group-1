import os
import sys

# --- project root on sys.path (works both in script & notebook) ---
if "__file__" in globals():
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
else:
    CURRENT_DIR = os.getcwd()

PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
sys.path.append(PROJECT_ROOT)

import pandas as pd
import numpy as np

from etl.database.db_connect import get_connection

DATA_DIR = os.path.join(PROJECT_ROOT, "etl", "database", "data")

from catboost import CatBoostRegressor, Pool
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import RandomForestRegressor
from joblib import dump

try:
    import matplotlib.pyplot as plt
    _MATPLOTLIB_ERROR = None
except Exception as exc:  # pragma: no cover - import guard
    plt = None
    _MATPLOTLIB_ERROR = exc
import json


# =========================
# 1. Load training data
# =========================
def load_pricing_data():
    conn = get_connection()
    if conn is not None:
        query = """
            SELECT
                fs.price_sold,
                mi.product_name,
                r.location,
                r.type,
                mi.portion_size,
                mi.base_price,
                mi.cost,
                mi.category_id,
                c.age_group
            FROM fact_sales fs
            JOIN dim_menu_item mi   ON fs.product_id    = mi.product_id
            JOIN dim_restaurant r   ON fs.restaurant_id = r.restaurant_id
            JOIN dim_customer c     ON fs.customer_id   = c.customer_id;
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df

    print("No live DB connection; falling back to CSVs from etl/database/data ...")
    csv_files = {
        "fact_sales": "fact_sales.csv",
        "dim_menu_item": "dim_menu_item.csv",
        "dim_restaurant": "dim_restaurant.csv",
        "dim_customer": "dim_customer.csv",
    }
    dataframes = {}
    for name, filename in csv_files.items():
        path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(path):
            raise RuntimeError(f"Required data file missing: {path}")
        dataframes[name] = pd.read_csv(path)

    df = (
        dataframes["fact_sales"]
        .merge(
            dataframes["dim_menu_item"][
                [
                    "product_id",
                    "product_name",
                    "portion_size",
                    "base_price",
                    "cost",
                    "category_id",
                ]
            ],
            on="product_id",
            how="left",
        )
        .merge(
            dataframes["dim_restaurant"][["restaurant_id", "location", "type"]],
            on="restaurant_id",
            how="left",
        )
        .merge(
            dataframes["dim_customer"][["customer_id", "age_group"]],
            on="customer_id",
            how="left",
        )
    )

    expected_cols = [
        "price_sold",
        "product_name",
        "location",
        "type",
        "portion_size",
        "base_price",
        "cost",
        "category_id",
        "age_group",
    ]
    missing_cols = [col for col in expected_cols if col not in df.columns]
    if missing_cols:
        raise RuntimeError(f"Missing columns from merged CSV data: {missing_cols}")

    return df[expected_cols]


# =========================
# 2. Feature engineering
# =========================
def bucket_portion_size(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts raw portion_size into buckets: small / medium / large.

    Assumes portion_size column can be parsed as numeric grams/ml/etc.
    Example values: '250', '250g', '0.25', '500 ml'
    """
    s = (
        df["portion_size"]
        .astype(str)
        .str.extract(r"(\d+\.?\d*)")[0]    # get numeric part
        .astype(float)
    )
    df["portion_numeric"] = s

    # Use min/max of data as guide to split into 3 equal-width bins.
    # Guard against degenerate input where every portion size is identical.
    min_v, max_v = s.min(), s.max()
    span = max_v - min_v
    labels = ["small", "medium", "large"]

    if pd.isna(span) or span <= 0:
        df["portion_bucket"] = "medium"
        return df

    eps = max(span * 1e-6, 1e-9)
    bins = np.linspace(min_v - eps, max_v + eps, num=4)
    df["portion_bucket"] = pd.cut(s, bins=bins, labels=labels)

    return df



def preprocess_data(df: pd.DataFrame):
    # Basic cleaning
    df = df.dropna(
        subset=["price_sold", "product_name", "location", "type", "portion_size", "age_group"]
    ).copy()

    # Create S/M/L buckets
    df = bucket_portion_size(df)

    # Safe numeric conversions
    numeric_cols = ["portion_numeric", "base_price", "cost"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df[col].fillna(df[col].median())

    df["category_id"] = df["category_id"].astype(str)

    # Features and target
    feature_cols = [
        "location",
        "type",
        "age_group",
        "category_id",
        "portion_bucket",
        "portion_numeric",
        "base_price",
        "cost",
    ]
    target_col = "price_sold"

    X = df[feature_cols]
    y = df[target_col]

    # Categorical feature names (CatBoost will handle them)
    cat_features = ["location", "type", "age_group", "category_id", "portion_bucket"]

    return X, y, cat_features


# =========================
# 3. Train CatBoost model
# =========================
def train_catboost_model(X_train, X_valid, y_train, y_valid, cat_features):
    cat_indices = [X_train.columns.get_loc(col) for col in cat_features]

    train_pool = Pool(X_train, y_train, cat_features=cat_indices)
    valid_pool = Pool(X_valid, y_valid, cat_features=cat_indices)

    model = CatBoostRegressor(
    iterations=2000,
    learning_rate=0.03,
    depth=7,
    loss_function="RMSE",
    eval_metric="RMSE",
    l2_leaf_reg=5.0,
    random_seed=42,
    verbose=100,
    od_type="Iter",
    od_wait=100,  # early stopping patience 
    )


    model.fit(train_pool, eval_set=valid_pool, use_best_model=True)

    # Evaluation
    y_pred = model.predict(valid_pool)
    mse = mean_squared_error(y_valid, y_pred)
    rmse = float(np.sqrt(mse))
    mae = mean_absolute_error(y_valid, y_pred)

    print(f"CatBoost RMSE: {rmse:.3f}")
    print(f"CatBoost MAE : {mae:.3f}")

    metrics = {"rmse": rmse, "mae": float(mae)}
    return model, y_pred, metrics


def train_random_forest_baseline(X_train, X_valid, y_train, y_valid):
    # One-hot encode categoricals for RF
    X_train_enc = pd.get_dummies(X_train, drop_first=True)
    X_valid_enc = pd.get_dummies(X_valid, drop_first=True)

    # Align columns (some categories may only appear in train)
    X_valid_enc = X_valid_enc.reindex(columns=X_train_enc.columns, fill_value=0)

    rf = RandomForestRegressor(
        n_estimators=200,
        max_depth=None,
        random_state=42,
        n_jobs=-1,
    )
    rf.fit(X_train_enc, y_train)
    y_pred = rf.predict(X_valid_enc)

    mse = mean_squared_error(y_valid, y_pred)
    rmse = float(np.sqrt(mse))
    mae = mean_absolute_error(y_valid, y_pred)

    print(f"RandomForest RMSE: {rmse:.3f}")
    print(f"RandomForest MAE : {mae:.3f}")

    metrics = {"rmse": rmse, "mae": float(mae)}
    return rf, y_pred, metrics

def make_output_plots_and_metrics(y_valid, cat_pred, rf_pred,
                                  cat_metrics, rf_metrics,
                                  output_dir="outputs"):
    os.makedirs(output_dir, exist_ok=True)

    if plt is None:
        print("Matplotlib is unavailable; skipping plots.")
        if _MATPLOTLIB_ERROR:
            print(f"Original import error: {_MATPLOTLIB_ERROR}")
    else:
        # 1) Bar plot: model comparison (RMSE & MAE)
        plt.figure(figsize=(6, 4))
        models = ["CatBoost", "RandomForest"]
        rmse_vals = [cat_metrics["rmse"], rf_metrics["rmse"]]
        mae_vals = [cat_metrics["mae"], rf_metrics["mae"]]

        x = np.arange(len(models))
        width = 0.35

        plt.bar(x - width/2, rmse_vals, width, label="RMSE")
        plt.bar(x + width/2, mae_vals, width, label="MAE")
        plt.xticks(x, models)
        plt.ylabel("Error")
        plt.title("Model Performance Comparison")
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "model_comparison.png"))
        plt.close()

        # 2) Scatter plot: y_true vs y_pred (CatBoost)
        plt.figure(figsize=(5, 5))
        plt.scatter(y_valid, cat_pred, alpha=0.4)
        min_v = min(y_valid.min(), cat_pred.min())
        max_v = max(y_valid.max(), cat_pred.max())
        plt.plot([min_v, max_v], [min_v, max_v], "r--")
        plt.xlabel("True price_sold")
        plt.ylabel("Predicted price_sold")
        plt.title("CatBoost: True vs Predicted")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "catboost_true_vs_pred.png"))
        plt.close()

        # 3) Scatter plot: y_true vs y_pred (RandomForest)
        plt.figure(figsize=(5, 5))
        plt.scatter(y_valid, rf_pred, alpha=0.4)
        min_v = min(y_valid.min(), rf_pred.min())
        max_v = max(y_valid.max(), rf_pred.max())
        plt.plot([min_v, max_v], [min_v, max_v], "r--")
        plt.xlabel("True price_sold")
        plt.ylabel("Predicted price_sold")
        plt.title("RandomForest: True vs Predicted")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "rf_true_vs_pred.png"))
        plt.close()

    # 4) Save metrics to JSON
    results = {
        "catboost": cat_metrics,
        "random_forest": rf_metrics,
    }
    with open(os.path.join(output_dir, "metrics.json"), "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved plots and metrics to: {os.path.abspath(output_dir)}")

import pickle

def save_models(cat_model, rf_model, output_dir="outputs"):
    os.makedirs(output_dir, exist_ok=True)

    # Save CatBoost model in native format
    cat_path = os.path.join(output_dir, "catboost_model.cbm")
    cat_model.save_model(cat_path)
    print(f"Saved CatBoost model to: {cat_path}")

    # Save RandomForest using joblib without compression (faster to load)
    rf_path = os.path.join(output_dir, "random_forest_model.pkl")
    dump(rf_model, rf_path)
    print(f"Saved RandomForest model to: {rf_path}")




if __name__ == "__main__":
    # 1) Load data
    df = load_pricing_data()
    print("Sample data:")
    print(df.head())

    # 2) Preprocess
    X, y, cat_features = preprocess_data(df)

    # 3) Single train/valid split
    X_train, X_valid, y_train, y_valid = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # 4) Train models
    print("\nTraining CatBoost...")
    cat_model, cat_pred, cat_metrics = train_catboost_model(
        X_train, X_valid, y_train, y_valid, cat_features
    )

    print("\nTraining RandomForest baseline...")
    rf_model, rf_pred, rf_metrics = train_random_forest_baseline(
        X_train, X_valid, y_train, y_valid
    )

    # 5) Make plots + metrics
    make_output_plots_and_metrics(
        y_valid, cat_pred, rf_pred,
        cat_metrics, rf_metrics,
        output_dir="outputs"
    )

    # 6) Save trained models
    save_models(cat_model, rf_model, output_dir="outputs")
