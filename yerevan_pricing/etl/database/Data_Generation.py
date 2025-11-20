import os

import numpy as np
import pandas as pd

np.random.seed(42)

# ---------------------------
# 0. Setup & load market data
# ---------------------------
os.makedirs("data", exist_ok=True)

# Load final_df (already cleaned + extended)
final_df = pd.read_csv("final_pricing_data.csv", parse_dates=["date"])

final_df["price"] = pd.to_numeric(final_df["price"], errors="coerce")
final_df["usdprice"] = pd.to_numeric(final_df["usdprice"], errors="coerce")
final_df = final_df.dropna(subset=["date", "price"]).reset_index(drop=True)

# --------------------------------
# 1. dim_season
# --------------------------------
dim_season = pd.DataFrame({
    "season": ["Winter", "Spring", "Summer", "Autumn"],
    "months": ["Dec,Jan,Feb", "Mar,Apr,May", "Jun,Jul,Aug", "Sep,Oct,Nov"]
})
dim_season.to_csv("data/dim_season.csv", index=False)

# --------------------------------
# 2. dim_time (2023–2025)
# --------------------------------
all_dates = pd.date_range("2022-01-01", "2025-12-31", freq="D")

dim_time = pd.DataFrame({"date": all_dates})
dim_time["year"] = dim_time["date"].dt.year
dim_time["month"] = dim_time["date"].dt.month
dim_time["day"] = dim_time["date"].dt.day
dim_time["day_of_week"] = dim_time["date"].dt.weekday

def season_of_month(m):
    if m in [12,1,2]: return "Winter"
    if m in [3,4,5]: return "Spring"
    if m in [6,7,8]: return "Summer"
    return "Autumn"

dim_time["season"] = dim_time["month"].apply(season_of_month)
dim_time.to_csv("data/dim_time.csv", index=False)

# --------------------------------
# 3. dim_market (Yerevan market)
# --------------------------------
lat_mean = 40.181111
lon_mean = 44.513611

dim_market = pd.DataFrame([{
    "market_id": 1,
    "admin1": "Yerevan",
    "admin2": "Yerevan",
    "market_name": "Yerevan Market",
    "latitude": lat_mean,
    "longitude": lon_mean
}])

dim_market.to_csv("data/dim_market.csv", index=False)

# --------------------------------
# 4. fact_market_prices
# --------------------------------
fact_market_prices = final_df.copy()
fact_market_prices.insert(0, "price_id", range(1, len(fact_market_prices)+1))
fact_market_prices["market_id"] = 1

fact_market_prices = fact_market_prices[[
    "price_id", "date", "market_id",
    "category", "commodity", "unit",
    "priceflag", "pricetype", "currency",
    "price", "usdprice"
]]

fact_market_prices.to_csv("data/fact_market_prices.csv", index=False)

# --------------------------------
# 5. dim_category (menu categories)
# --------------------------------
categories = [
    "Coffee",
    "Tea & Matcha",
    "Breakfast",
    "Pizza",
    "Main Dishes",
    "Salads",
    "Desserts",
    "Cocktails",
    "Soft Drinks",
    "Appetizers",
    "Sandwiches",
]

dim_category = pd.DataFrame({
    "category_id": list(range(1, len(categories)+1)),
    "category_name": categories
})
dim_category.to_csv("data/dim_category.csv", index=False)

cat_map = dict(zip(dim_category["category_name"], dim_category["category_id"]))

# --------------------------------
# 6. dim_restaurant (40 restaurants)
# --------------------------------
restaurant_info = [
    ("Gallia", "Kentron", "restaurant"),
    ("Afro Lab Roastery", "Kentron", "coffee_house"),
    ("De Angelo", "Nor Nork", "restaurant"),
    ("Aperitivo", "Kentron", "bar_bistro"),
    ("Babajanyan", "Kentron", "restaurant"),
    ("Vostan", "Kentron", "restaurant"),
    ("Louis Charden", "Arabkir", "bakery_cafe"),
    ("Coffeeshop Company", "Kentron", "coffee_chain"),
    ("The Kond House", "Kentron", "restaurant"),
    ("Tiziano", "Arabkir", "cafe"),
    ("Al Mayass", "Kentron", "restaurant"),
    ("Lavash", "Kentron", "restaurant"),
    ("Pandok Yerevan", "Kentron", "restaurant"),
    ("Ankyun", "Kentron", "cafe_bistro"),
    ("Mangiare", "Malatia-Sebastia", "restaurant"),
    ("Super Kidob", "Ajapnyak", "fast_food"),
    ("Ray's", "Kentron", "bar_bistro"),
    ("Caffeine Brew Lab", "Arabkir", "coffee_house"),
    ("Dargett", "Kentron", "brewpub"),
    ("Eat & Fit", "Kentron", "healthy_cafe"),
    ("Camilla", "Arabkir", "cafe_bistro"),
    ("Mayrig", "Kentron", "restaurant"),
    ("Seasons", "Kentron", "restaurant"),
    ("Limone", "Arabkir", "cafe_restaurant"),
    ("Amar", "Kentron", "wine_bar"),
    ("Wine Republic", "Kentron", "wine_bar"),
    ("In Vino", "Kentron", "wine_bar"),
    ("El Sky Bar", "Kentron", "bar_restaurant"),
    ("Bureaucrat Café & Books", "Kentron", "cafe"),
    ("Charentsi 28", "Kentron", "restaurant"),
    ("Pandok Yerevan Riverside", "Nor Nork", "restaurant"),
    ("Pizzarella", "Malatia-Sebastia", "pizzeria"),
    ("Dine Sky", "Kentron", "restaurant"),
    ("Marmelad Café", "Malatia-Sebastia", "cafe_dessert"),
    ("Toast Bistro", "Ajapnyak", "bistro"),
    ("Ponchik Monchik (Cascade)", "Kentron", "cafe_dessert"),
    ("La Cucina", "Kentron", "italian_rest"),
    ("Green Bean Coffee", "Arabkir", "coffee_house"),
    ("Saryan Eatery", "Kentron", "restaurant"),
    ("GastroHouse", "Ajapnyak", "gastropub"),
]

rest_rows = []
for i, (name, loc, rtype) in enumerate(restaurant_info, start=1):
    rest_rows.append({
        "restaurant_id": i,
        "name": name,
        "location": loc,
        "type": rtype,
        "avg_customer_count": np.random.randint(60, 350),
        "rating": round(np.clip(np.random.normal(4.3, 0.25), 3.4, 4.9), 2),
        "owner_contact": f"+374-{np.random.randint(10,99)}-{np.random.randint(100000,999999)}"
    })

dim_restaurant = pd.DataFrame(rest_rows)
dim_restaurant.to_csv("data/dim_restaurant.csv", index=False)

# --------------------------------
# 7. dim_menu_item (40 restaurants × 30–40 items)
# --------------------------------

# Menu templates (extracted from Gallia, Afro Lab, De Angelo)
menu_bank = [
    ("Espresso", "Coffee", 800, 1800),
    ("Macchiato", "Coffee", 1000, 1800),
    ("Cappuccino", "Coffee", 1200, 2500),
    ("Latte", "Coffee", 1300, 2600),
    ("Flat White", "Coffee", 1400, 2700),
    ("Cold Brew", "Coffee", 1500, 3000),
    ("Raf", "Coffee", 1700, 3200),
    ("Matcha Latte", "Tea & Matcha", 1500, 3500),
    ("Black Tea", "Tea & Matcha", 600, 1500),
    ("Herbal Tea", "Tea & Matcha", 800, 2000),
    ("Omelet / Scramble", "Breakfast", 1800, 2500),
    ("Eggs Benedict", "Breakfast", 3200, 4200),
    ("Salmon Croissant", "Breakfast", 3000, 3800),
    ("Ricotta Croissant", "Breakfast", 2500, 3100),
    ("Guacamole Toast", "Breakfast", 4000, 4600),
    ("Caprese Croissant", "Breakfast", 2900, 3500),
    ("Cheesecake", "Desserts", 2500, 3500),
    ("Chocolate Mousse", "Desserts", 2400, 3000),
    ("Tarte Tatin", "Desserts", 2700, 3200),
    ("Brownie", "Desserts", 1500, 2500),
    ("Margarita Pizza", "Pizza", 3800, 4500),
    ("Parma Pizza", "Pizza", 4500, 5500),
    ("Ventricina Pizza", "Pizza", 4000, 5000),
    ("Quattro Formaggi", "Pizza", 4500, 5600),
    ("Chicken Pasta", "Main Dishes", 4500, 9000),
    ("Beef Steak", "Main Dishes", 10000, 20000),
    ("Salmon Steak", "Main Dishes", 8000, 15000),
    ("Chicken Caesar", "Salads", 3500, 5500),
    ("Greek Salad", "Salads", 2500, 4500),
    ("Aperol Spritz", "Cocktails", 3500, 5500),
    ("Mojito", "Cocktails", 3500, 5500),
    ("Fresh Orange Juice", "Soft Drinks", 2000, 2500),
    ("Mineral Water", "Soft Drinks", 500, 1000),
    ("Hummus Plate", "Appetizers", 2500, 4000),
    ("Bruschetta", "Appetizers", 2500, 3500),
    ("Club Sandwich", "Sandwiches", 3000, 4500),
    ("Chicken Sandwich", "Sandwiches", 3000, 4500),
]

menu_rows = []
pid = 1

for _, r in dim_restaurant.iterrows():
    n_items = np.random.randint(30, 41)
    chosen_items = np.random.choice(len(menu_bank), size=n_items, replace=True)

    for idx in chosen_items:
        name, cat_name, pmin, pmax = menu_bank[idx]
        base_price = float(np.random.uniform(pmin, pmax))
        base_price = round(base_price / 100) * 100

        cost = base_price * np.random.uniform(0.40, 0.50)
        cost = round(cost / 100) * 100


        menu_rows.append({
            "product_id": pid,
            "restaurant_id": r["restaurant_id"],
            "product_name": name,
            "category_id": cat_map[cat_name],
            "base_price": round(base_price, 1),
            "cost": round(cost, 1),
            "portion_size": np.random.choice(["200ml", "250ml", "300ml", "350ml", "400g", "250g"]),
            "available": True
        })
        pid += 1

dim_menu_item = pd.DataFrame(menu_rows)
dim_menu_item.to_csv("data/dim_menu_item.csv", index=False)

# --------------------------------
# 8. dim_customer (5000 customers)
# --------------------------------
genders = ["Male", "Female", "Not observed"]
age_groups = ["0-17","18-24","25-34","35-44","45-54","55+"]

cust_rows = []
for cid in range(1, 5001):
    segment = np.random.choice(["low","medium","high"], p=[0.5,0.35,0.15])

    if segment == "high":
        freq = np.random.randint(16,36)
        spend = np.random.randint(5000, 12000)
    elif segment == "medium":
        freq = np.random.randint(5,16)
        spend = np.random.randint(4000,9000)
    else:
        freq = np.random.randint(1,5)
        spend = np.random.randint(2000,5000)

    cust_rows.append({
        "customer_id": cid,
        "gender": np.random.choice(genders),
        "age_group": np.random.choice(age_groups),
        "avg_spending": spend,
        "visit_frequency": freq
    })

dim_customer = pd.DataFrame(cust_rows)
dim_customer.to_csv("data/dim_customer.csv", index=False)

# --------------------------------
# 9. fact_sales (daily sales per restaurant × product)
# --------------------------------

sales_start = pd.Timestamp("2023-01-01")
sales_end = pd.Timestamp("2025-12-31")
sales_dates = pd.date_range(sales_start, sales_end, freq="D")

cat_demands = {
    "Coffee": (15, 50),
    "Tea & Matcha": (7, 20),
    "Breakfast": (5, 25),
    "Pizza": (8, 20),
    "Main Dishes": (4, 15),
    "Salads": (3, 12),
    "Desserts": (5, 18),
    "Cocktails": (3, 10),
    "Soft Drinks": (5, 30),
    "Appetizers": (3, 10),
    "Sandwiches": (4, 12),
}

prod_meta = dim_menu_item.merge(dim_category, on="category_id")

# Create customer probability weights based on visit frequency
# High-frequency customers more likely to appear in sales
customer_weights = dim_customer["visit_frequency"].values
customer_weights = customer_weights / customer_weights.sum()
customer_ids = dim_customer["customer_id"].values

sales_rows = []
sid = 1

for _, p in prod_meta.iterrows():
    cat = p["category_name"]
    base_price = p["base_price"]

    low, high = cat_demands[cat]
    base_lambda = np.random.uniform(low, high)

    for d in sales_dates:
        # weekday effects
        dow = d.weekday()
        if dow >= 5: wd_factor = 1.3
        elif dow <= 1: wd_factor = 0.9
        else: wd_factor = 1.0

        # seasonal effects
        m = d.month
        if cat in ["Coffee","Tea & Matcha","Desserts","Breakfast"]:
            season_factor = 1.2 if m in [12,1,2] else (0.9 if m in [6,7,8] else 1.0)
        elif cat in ["Cocktails","Salads","Soft Drinks"]:
            season_factor = 1.3 if m in [6,7,8] else 0.9
        else:
            season_factor = 1.0

        lam = base_lambda * wd_factor * season_factor
        units = np.random.poisson(lam)

        if units <= 0:
            continue

        # price dynamics
        if np.random.rand() < 0.1:
            price_factor = np.random.uniform(0.8, 0.95)
        else:
            price_factor = np.random.uniform(0.98, 1.02)

        price_sold = base_price * price_factor
        price_sold = round(price_sold / 100) * 100
        price_sold = max(price_sold, p["cost"])

        revenue = round(price_sold * units, 1)

        # Assign customer_id weighted by visit frequency
        assigned_customer_id = np.random.choice(customer_ids, p=customer_weights)

        sales_rows.append({
            "sale_id": sid,
            "product_id": p["product_id"],
            "restaurant_id": p["restaurant_id"],
            "customer_id": assigned_customer_id,
            "date": d,
            "units_sold": units,
            "price_sold": price_sold,
            "revenue": revenue
        })
        sid += 1

fact_sales = pd.DataFrame(sales_rows)
fact_sales.to_csv("data/fact_sales.csv", index=False)

print("✔ ALL DATA GENERATED SUCCESSFULLY IN /data FOLDER!")
