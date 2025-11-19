from __future__ import annotations

import csv
from copy import deepcopy
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data"


def _load_csv(filename: str) -> List[dict]:
    path = DATA_DIR / filename
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        return list(reader)


def _bootstrap_restaurants() -> List[dict]:
    rows = _load_csv("dim_restaurant.csv")
    restaurants = []
    for row in rows:
        restaurants.append(
            {
                "restaurant_id": int(row["restaurant_id"]),
                "name": row["name"],
                "location": row["location"],
                "venue_type": row["type"],
                "avg_customer_count": int(row["avg_customer_count"]),
                "rating": float(row["rating"]),
                "owner_contact": row["owner_contact"],
            }
        )
    return restaurants


def _bootstrap_menu_items() -> List[dict]:
    rows = _load_csv("dim_menu_item.csv")
    items = []
    for row in rows[:100]:  # limit to keep the dummy payloads small
        items.append(
            {
                "product_id": int(row["product_id"]),
                "restaurant_id": int(row["restaurant_id"]),
                "product_name": row["product_name"],
                "category_id": int(row["category_id"]),
                "base_price": float(row["base_price"]),
                "cost": float(row["cost"]),
                "portion_size": row["portion_size"],
                "available": row["available"].lower() == "true",
            }
        )
    return items


def _bootstrap_customers() -> List[dict]:
    rows = _load_csv("dim_customer.csv")
    customers = []
    for row in rows[:200]:
        customers.append(
            {
                "customer_id": int(row["customer_id"]),
                "gender": row["gender"],
                "age_group": row["age_group"],
                "avg_spending": float(row["avg_spending"]),
                "visit_frequency": int(row["visit_frequency"]),
            }
        )
    return customers


restaurants_store = _bootstrap_restaurants()
menu_items_store = _bootstrap_menu_items()
customers_store = _bootstrap_customers()


def _next_id(store: List[dict], key: str) -> int:
    if not store:
        return 1
    return max(item[key] for item in store) + 1


def _get_record_or_404(store: List[dict], key: str, value: int) -> dict:
    for record in store:
        if record[key] == value:
            return record
    raise HTTPException(status_code=404, detail=f"{key}={value} not found")


class RestaurantBase(BaseModel):
    name: str
    location: str
    venue_type: str = Field(
        description="Type of venue e.g. restaurant, coffee_house, bakery"
    )
    avg_customer_count: int = Field(ge=0)
    rating: float = Field(ge=0, le=5)
    owner_contact: str


class RestaurantCreate(RestaurantBase):
    pass


class Restaurant(RestaurantBase):
    restaurant_id: int


class MenuItemBase(BaseModel):
    restaurant_id: int = Field(ge=1)
    product_name: str
    category_id: int
    base_price: float = Field(ge=0)
    cost: float = Field(ge=0)
    portion_size: str
    available: bool = True


class MenuItemCreate(MenuItemBase):
    pass


class MenuItem(MenuItemBase):
    product_id: int


class Customer(BaseModel):
    customer_id: int
    gender: str
    age_group: str
    avg_spending: float
    visit_frequency: int


app = FastAPI(
    title="Pricing Backend — Dummy Service",
    description="FastAPI stub that serves placeholder data for Milestone 2.",
    version="0.1.0",
)


@app.get("/health")
def healthcheck() -> dict:
    return {"status": "ok"}


# --- Restaurants -----------------------------------------------------------
@app.get("/restaurants", response_model=List[Restaurant])
def list_restaurants() -> List[Restaurant]:
    return deepcopy(restaurants_store)


@app.get("/restaurants/{restaurant_id}", response_model=Restaurant)
def get_restaurant(restaurant_id: int) -> Restaurant:
    record = _get_record_or_404(restaurants_store, "restaurant_id", restaurant_id)
    return deepcopy(record)


@app.post("/restaurants", response_model=Restaurant, status_code=201)
def create_restaurant(payload: RestaurantCreate) -> Restaurant:
    new_record = payload.model_dump()
    new_record["restaurant_id"] = _next_id(restaurants_store, "restaurant_id")
    restaurants_store.append(new_record)
    return deepcopy(new_record)


@app.put("/restaurants/{restaurant_id}", response_model=Restaurant)
def update_restaurant(restaurant_id: int, payload: RestaurantCreate) -> Restaurant:
    record = _get_record_or_404(restaurants_store, "restaurant_id", restaurant_id)
    record.update(payload.model_dump())
    return deepcopy(record)


@app.delete("/restaurants/{restaurant_id}", status_code=204, response_class=Response)
def delete_restaurant(restaurant_id: int) -> Response:
    record = _get_record_or_404(restaurants_store, "restaurant_id", restaurant_id)
    restaurants_store.remove(record)
    return Response(status_code=204)


# --- Menu items ------------------------------------------------------------
@app.get("/menu-items", response_model=List[MenuItem])
def list_menu_items(
    restaurant_id: Optional[int] = None, available: Optional[bool] = None
) -> List[MenuItem]:
    items = menu_items_store
    if restaurant_id is not None:
        items = [item for item in items if item["restaurant_id"] == restaurant_id]
    if available is not None:
        items = [item for item in items if item["available"] is available]
    return deepcopy(items)


@app.get("/menu-items/{product_id}", response_model=MenuItem)
def get_menu_item(product_id: int) -> MenuItem:
    record = _get_record_or_404(menu_items_store, "product_id", product_id)
    return deepcopy(record)


@app.post("/menu-items", response_model=MenuItem, status_code=201)
def create_menu_item(payload: MenuItemCreate) -> MenuItem:
    new_record = payload.model_dump()
    new_record["product_id"] = _next_id(menu_items_store, "product_id")
    menu_items_store.append(new_record)
    return deepcopy(new_record)


@app.put("/menu-items/{product_id}", response_model=MenuItem)
def update_menu_item(product_id: int, payload: MenuItemCreate) -> MenuItem:
    record = _get_record_or_404(menu_items_store, "product_id", product_id)
    record.update(payload.model_dump())
    return deepcopy(record)


@app.delete("/menu-items/{product_id}", status_code=204, response_class=Response)
def delete_menu_item(product_id: int) -> Response:
    record = _get_record_or_404(menu_items_store, "product_id", product_id)
    menu_items_store.remove(record)
    return Response(status_code=204)


# --- Customers (read-only) -------------------------------------------------
@app.get("/customers", response_model=List[Customer])
def list_customers() -> List[Customer]:
    return deepcopy(customers_store)


@app.get("/customers/{customer_id}", response_model=Customer)
def get_customer(customer_id: int) -> Customer:
    record = _get_record_or_404(customers_store, "customer_id", customer_id)
    return deepcopy(record)


# --- Analytics placeholders -----------------------------------------------
@app.get("/analytics/historical")
def get_historical_snapshot(
    menu_item: str = "Americano", location: str = "Kentron"
) -> dict:
    return {
        "menu_item": menu_item,
        "location": location,
        "avg_price": 1800,
        "units_sold": 1200,
        "market": "Kentron",
        "season": "Winter",
        "notes": "Dummy payload – replace with DB queries",
    }


@app.get("/analytics/forecast")
def get_price_forecast(
    menu_item: str = "Americano", horizon_days: int = 30
) -> dict:
    return {
        "menu_item": menu_item,
        "recommended_price": 1900,
        "confidence": 0.78,
        "horizon_days": horizon_days,
        "notes": "Dummy payload – replace with model output",
    }

