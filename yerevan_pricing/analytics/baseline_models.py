import os
import sys
import warnings
import pandas as pd
import numpy as np

CURRENT_DIR = os.path.dirname(__file__)
UTILS_DIR = os.path.join(CURRENT_DIR, "utils")

if UTILS_DIR not in sys.path:
    sys.path.append(UTILS_DIR)

from db_connect import get_connection



# Make sure the analytics utils folder is importable (works whether run as script or module)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "utils")))
try:
    from db_connect import get_connection
except Exception:
    # fallback if running from a different working dir
    try:
        sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "analytics", "utils")))
        from db_connect import get_connection
    except Exception:
        get_connection = None

# ML
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor

import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings("ignore")


def run_models(verbose=True):
    """Run the baseline modeling & dynamic pricing pipeline.

    This function converts the notebook workflow into a runnable script.
    It reads tables from Postgres via `get_connection()` (from analytics/utils/db_connect.py),
    preprocesses data, trains baseline models, evaluates them, and prints summaries.
    """

    if get_connection is None:
        raise RuntimeError("Could not import `get_connection` from analytics/utils/db_connect.py")

    conn = get_connection()
    if conn is not None:
        if verbose:
            print("✔ Connected to PostgreSQL")
    else:
        raise RuntimeError("❌ Database connection failed")

    # === Load tables ===
    sales = pd.read_sql("SELECT * FROM fact_sales;", conn)
    menu = pd.read_sql("SELECT * FROM dim_menu_item;", conn)
    rest = pd.read_sql("SELECT * FROM dim_restaurant;", conn)
    cust = pd.read_sql("SELECT * FROM dim_customer;", conn)
    cat = pd.read_sql("SELECT * FROM dim_category;", conn)
    time = pd.read_sql("SELECT * FROM dim_time;", conn)
    market = pd.read_sql("SELECT * FROM fact_market_prices;", conn)
    market_dim = pd.read_sql("SELECT * FROM dim_market;", conn)

    # === Merge ===
    menu_clean = menu.drop(columns=["restaurant_id"], errors='ignore')
    df = (
        sales
        .merge(menu_clean, on="product_id", how="left")
        .merge(rest, on="restaurant_id", how="left")
        .merge(cust, on="customer_id", how="left")
        .merge(cat, on="category_id", how="left")
        .merge(time, on="date", how="left")
        .merge(market, on="date", how="left")
        .merge(market_dim, on="market_id", how="left")
    )

    df = df.rename(columns={"date": "sale_date"})
    df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")

    # safe types
    if "available" in df.columns:
        try:
            df["available"] = df["available"].astype(int)
        except Exception:
            pass

    # Fill numeric NaNs with medians where appropriate
    df = df.fillna({
        col: df[col].median() for col in [
            "price", "usdprice", "rating", "avg_spending", "units_sold", "price_sold", "revenue"
        ] if col in df.columns
    })

    # Categorical fill
    categorical_cols = [
        "product_name", "portion_size", "category_name",
        "gender", "age_group", "season",
        "commodity", "unit", "priceflag", "pricetype", "currency",
        "market_name", "admin1", "admin2",
        "location", "type"
    ]

    for col in categorical_cols:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown")

    # One-hot / top-k encoding helper
    def encode_top_k(local_df, col, k=20):
        top = local_df[col].value_counts().index[:k]
        for val in top:
            safe_name = str(val).replace(" ", "_")[:50]
            local_df[f"{col}_{safe_name}"] = (local_df[col] == val).astype(int)
        local_df.drop(columns=[col], inplace=True, errors='ignore')

    for col in categorical_cols:
        if col in df.columns:
            encode_top_k(df, col, k=20)

    # Prepare target and features for revenue prediction
    if "revenue" not in df.columns:
        raise RuntimeError("`revenue` column not found in merged data")

    y = df["revenue"]
    X = df.drop(columns=["revenue", "sale_date"], errors='ignore')
    X = X.select_dtypes(include=[np.number])
    X = X.replace([np.inf, -np.inf], np.nan).dropna()
    y = y.loc[X.index]

    if verbose:
        print(f"Final dataset shape: X={X.shape}, y={y.shape}")

    # If dataset is empty or too small, skip training and exit gracefully
    if X.shape[0] < 10:
        print("Not enough data to train models (rows < 10). Skipping model training.")
        return

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    if verbose:
        print(f"Train set: {len(X_train)} samples")
        print(f"Test set: {len(X_test)} samples")

    # ===== Train baseline models =====
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    pred_lr = lr.predict(X_test)

    dt = DecisionTreeRegressor(max_depth=10, random_state=42)
    dt.fit(X_train, y_train)
    pred_dt = dt.predict(X_test)

    rf = RandomForestRegressor(
        n_estimators=10,
        max_depth=8,
        max_samples=0.5 if hasattr(RandomForestRegressor, 'max_samples') else None,
        random_state=42,
        n_jobs=-1,
        warm_start=False
    )
    # If max_samples isn't supported, ignore the kwarg by creating without it
    try:
        rf.fit(X_train, y_train)
    except TypeError:
        rf = RandomForestRegressor(n_estimators=10, max_depth=8, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)

    pred_rf = rf.predict(X_test)

    # Metrics
    results = []
    for name, pred in [('Linear Regression', pred_lr), ('Decision Tree', pred_dt), ('Random Forest', pred_rf)]:
        results.append({'Model': name, 'R²': r2_score(y_test, pred), 'RMSE': mean_squared_error(y_test, pred, squared=False), 'MAE': np.mean(np.abs(y_test - pred))})

    results_df = pd.DataFrame(results)
    if verbose:
        print('\n' + '='*60)
        print('MODEL PERFORMANCE SUMMARY')
        print('='*60)
        print(results_df.to_string(index=False))
        print('='*60)

    # Basic visualizations (will display when run interactively)
    try:
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (14, 10)
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))

        axes[0, 0].scatter(y_test, pred_lr, alpha=0.5, s=20)
        axes[0, 0].plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
        axes[0, 0].set_title(f'Linear Regression\nR² = {r2_score(y_test, pred_lr):.4f}')

        axes[0, 1].scatter(y_test, pred_dt, alpha=0.5, s=20, color='orange')
        axes[0, 1].plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
        axes[0, 1].set_title(f'Decision Tree\nR² = {r2_score(y_test, pred_dt):.4f}')

        axes[0, 2].scatter(y_test, pred_rf, alpha=0.5, s=20, color='green')
        axes[0, 2].plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
        axes[0, 2].set_title(f'Random Forest\nR² = {r2_score(y_test, pred_rf):.4f}')

        residuals_lr = y_test - pred_lr
        axes[1, 0].hist(residuals_lr, bins=30, alpha=0.7, color='blue', edgecolor='black')
        axes[1, 0].axvline(0, color='r', linestyle='--', lw=2)
        axes[1, 0].set_title('Linear Regression - Residuals')

        residuals_dt = y_test - pred_dt
        axes[1, 1].hist(residuals_dt, bins=30, alpha=0.7, color='orange', edgecolor='black')
        axes[1, 1].axvline(0, color='r', linestyle='--', lw=2)
        axes[1, 1].set_title('Decision Tree - Residuals')

        residuals_rf = y_test - pred_rf
        axes[1, 2].hist(residuals_rf, bins=30, alpha=0.7, color='green', edgecolor='black')
        axes[1, 2].axvline(0, color='r', linestyle='--', lw=2)
        axes[1, 2].set_title('Random Forest - Residuals')

        plt.tight_layout()
        plt.show()
    except Exception:
        # If plotting fails in headless environment, continue silently
        if verbose:
            print("Plotting skipped (headless or error)")

    # === Dynamic pricing pieces (price prediction & recommendations) ===
    # Rebuild dataset for pricing
    df_pricing = df.copy()
    product_pricing = df_pricing.groupby('product_id').agg({
        'price_sold': ['mean', 'std', 'min', 'max'],
        'units_sold': 'mean',
        'revenue': 'sum',
        'customer_id': 'count'
    }).round(2)
    product_pricing.columns = ['avg_price', 'price_std', 'min_price', 'max_price', 'avg_units_sold', 'total_revenue', 'transaction_count']
    product_pricing = product_pricing.reset_index()

    if verbose:
        print('\nTop 10 Products by Revenue:')
        top_products = product_pricing.nlargest(10, 'total_revenue')
        print(top_products[['product_id', 'avg_price', 'avg_units_sold', 'total_revenue']].to_string(index=False))

    # Price elasticity estimation (limited sample)
    elasticity_data = []
    for product_id in df_pricing['product_id'].unique()[:20]:
        prod_data = df_pricing[df_pricing['product_id'] == product_id].copy()
        if len(prod_data) > 10 and 'price_sold' in prod_data.columns and 'units_sold' in prod_data.columns:
            try:
                price_bins = pd.qcut(prod_data['price_sold'], q=5, duplicates='drop')
                demand_by_price = prod_data.groupby(price_bins)['units_sold'].mean()
                if len(demand_by_price) >= 2:
                    low = demand_by_price.iloc[0]
                    high = demand_by_price.iloc[-1]
                    low_mid = demand_by_price.index[0].mid
                    high_mid = demand_by_price.index[-1].mid
                    price_change = (high_mid - low_mid) / (low_mid if low_mid != 0 else 1)
                    demand_change = (high - low) / (low if low != 0 else 1)
                    elasticity = demand_change / price_change if price_change != 0 else 0
                    elasticity_data.append({'product_id': product_id, 'avg_price': prod_data['price_sold'].mean(), 'elasticity': elasticity, 'price_sensitive': 'Yes' if abs(elasticity) > 1 else 'No'})
            except Exception:
                continue

    elasticity_df = pd.DataFrame(elasticity_data)
    if not elasticity_df.empty and verbose:
        print('\nPrice Elasticity Estimates:')
        print(elasticity_df.sort_values('elasticity', ascending=False).head(10).to_string(index=False))

    # Price prediction model (simple)
    if 'price_sold' in df.columns:
        y_price = df['price_sold']
        X_price = df.drop(columns=['revenue', 'sale_date', 'price_sold'], errors='ignore')
        X_price = X_price.select_dtypes(include=[np.number])
        X_price = X_price.replace([np.inf, -np.inf], np.nan).dropna()
        y_price = y_price.loc[X_price.index]

        if len(X_price) > 10:
            X_train_price, X_test_price, y_train_price, y_test_price = train_test_split(X_price, y_price, test_size=0.2, random_state=42)
            lr_price = LinearRegression()
            lr_price.fit(X_train_price, y_train_price)
            pred_price_lr = lr_price.predict(X_test_price)

            dt_price = DecisionTreeRegressor(max_depth=8, random_state=42)
            dt_price.fit(X_train_price, y_train_price)
            pred_price_dt = dt_price.predict(X_test_price)

            pricing_results = []
            pricing_results.append({'Model': 'Linear Regression (Price)', 'R²': r2_score(y_test_price, pred_price_lr), 'RMSE': mean_squared_error(y_test_price, pred_price_lr, squared=False), 'MAE': np.mean(np.abs(y_test_price - pred_price_lr))})
            pricing_results.append({'Model': 'Decision Tree (Price)', 'R²': r2_score(y_test_price, pred_price_dt), 'RMSE': mean_squared_error(y_test_price, pred_price_dt, squared=False), 'MAE': np.mean(np.abs(y_test_price - pred_price_dt))})
            pricing_results_df = pd.DataFrame(pricing_results)
            if verbose:
                print('\n' + '-'*70)
                print('PRICE PREDICTION MODEL PERFORMANCE')
                print('-'*70)
                print(pricing_results_df.to_string(index=False))

            # Recommendations: simple heuristic using elasticity
            recommendations = []
            for product_id in df_pricing['product_id'].unique()[:10]:
                prod_data = df_pricing[df_pricing['product_id'] == product_id]
                current_avg_price = prod_data['price_sold'].mean() if 'price_sold' in prod_data.columns else np.nan
                current_avg_revenue = prod_data['revenue'].mean() if 'revenue' in prod_data.columns else np.nan
                if not elasticity_df.empty and product_id in elasticity_df['product_id'].values:
                    elasticity_val = float(elasticity_df.loc[elasticity_df['product_id'] == product_id, 'elasticity'].iloc[0])
                    price_multiplier = 0.95 if elasticity_val < -1 else 1.05
                else:
                    price_multiplier = 1.0
                optimal_price = current_avg_price * price_multiplier if not np.isnan(current_avg_price) else np.nan
                recommendations.append({'product_id': product_id, 'current_price': current_avg_price, 'optimal_price': optimal_price, 'price_change_%': (price_multiplier - 1) * 100, 'current_revenue': current_avg_revenue, 'strategy': 'Lower Price (Elastic)' if price_multiplier < 1 else 'Raise Price (Inelastic)'})

            recommendations_df = pd.DataFrame(recommendations)
            if verbose:
                print('\nTop 10 Product Pricing Recommendations:')
                print(recommendations_df.to_string(index=False))

    if verbose:
        print('\n' + '='*70)
        print('Pipeline complete')


if __name__ == '__main__':
    run_models()
