"""
Core data processing engine.
Loads raw CSV exports, cleans, validates, and computes KPIs.
"""
import logging
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
import numpy as np

from src.config import RAW_DATA_DIR, PROCESSED_DIR, DATE_FORMAT

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def load_and_process_all() -> Dict[str, pd.DataFrame]:
    """
    Entry point: load every raw source, clean it, return processed frames.
    Returns a dict keyed by logical name.
    """
    logger.info("Starting data load & processing pipeline…")
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    sales     = _load_sales()
    customers = _load_customers()
    inventory = _load_inventory()

    sales = _enrich_sales(sales, customers)

    kpis         = _compute_kpis(sales)
    regional     = _regional_summary(sales)
    product_perf = _product_performance(sales)
    top_sales    = _top_salespeople(sales)
    daily_trend  = _daily_trend(sales)
    category     = _category_breakdown(sales)
    inventory_kpi = _inventory_analysis(inventory)

    # Persist cleaned data
    sales.to_csv(PROCESSED_DIR / "sales_clean.csv", index=False)
    logger.info("Processed data written to %s", PROCESSED_DIR)

    return {
        "sales":         sales,
        "customers":     customers,
        "inventory":     inventory,
        "kpis":          kpis,
        "regional":      regional,
        "product_perf":  product_perf,
        "top_sales":     top_sales,
        "daily_trend":   daily_trend,
        "category":      category,
        "inventory_kpi": inventory_kpi,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Loaders
# ─────────────────────────────────────────────────────────────────────────────

def _load_sales() -> pd.DataFrame:
    path = RAW_DATA_DIR / "sales_data.csv"
    logger.info("Loading sales data from %s", path)
    df = pd.read_csv(path, parse_dates=["date"])

    # Clean
    df.columns = df.columns.str.strip().str.lower()
    df = df.dropna(subset=["order_id", "date", "unit_price", "quantity"])
    df["quantity"]   = pd.to_numeric(df["quantity"],   errors="coerce").fillna(0).astype(int)
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce").fillna(0.0)
    df["discount"]   = pd.to_numeric(df["discount"],   errors="coerce").fillna(0.0)

    # Derived columns
    df["gross_revenue"] = df["quantity"] * df["unit_price"]
    df["discount_amt"]  = df["gross_revenue"] * df["discount"]
    df["net_revenue"]   = df["gross_revenue"] - df["discount_amt"]
    df["week"]          = df["date"].dt.isocalendar().week.astype(int)
    df["month"]         = df["date"].dt.month
    df["day_name"]      = df["date"].dt.day_name()

    logger.info("Sales data loaded: %d rows", len(df))
    return df


def _load_customers() -> pd.DataFrame:
    path = RAW_DATA_DIR / "customers.csv"
    logger.info("Loading customer data from %s", path)
    df = pd.read_csv(path, parse_dates=["join_date"])
    df.columns = df.columns.str.strip().str.lower()
    return df


def _load_inventory() -> pd.DataFrame:
    path = RAW_DATA_DIR / "inventory.csv"
    logger.info("Loading inventory data from %s", path)
    df = pd.read_csv(path, parse_dates=["last_restocked"])
    df.columns = df.columns.str.strip().str.lower()
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Enrichment
# ─────────────────────────────────────────────────────────────────────────────

def _enrich_sales(sales: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    merged = sales.merge(
        customers[["customer_id", "segment", "name"]],
        on="customer_id",
        how="left",
    )
    merged["segment"] = merged["segment"].fillna("Unknown")
    return merged


# ─────────────────────────────────────────────────────────────────────────────
# KPI Computations
# ─────────────────────────────────────────────────────────────────────────────

def _compute_kpis(df: pd.DataFrame) -> pd.DataFrame:
    completed = df[df["status"] == "completed"]

    total_revenue    = completed["net_revenue"].sum()
    total_orders     = len(completed)
    avg_order_value  = completed["net_revenue"].mean() if total_orders else 0
    total_units      = completed["quantity"].sum()
    unique_customers = completed["customer_id"].nunique()
    conversion_rate  = (len(completed) / len(df) * 100) if len(df) else 0
    total_discount   = completed["discount_amt"].sum()
    discount_pct     = (total_discount / completed["gross_revenue"].sum() * 100) if completed["gross_revenue"].sum() else 0

    kpis = pd.DataFrame([
        {"metric": "Total Revenue",       "value": f"${total_revenue:,.2f}",      "raw": total_revenue},
        {"metric": "Total Orders",         "value": str(total_orders),             "raw": total_orders},
        {"metric": "Avg Order Value",      "value": f"${avg_order_value:,.2f}",    "raw": avg_order_value},
        {"metric": "Units Sold",           "value": str(total_units),              "raw": total_units},
        {"metric": "Unique Customers",     "value": str(unique_customers),         "raw": unique_customers},
        {"metric": "Order Completion Rate","value": f"{conversion_rate:.1f}%",     "raw": conversion_rate},
        {"metric": "Total Discounts Given","value": f"${total_discount:,.2f}",     "raw": total_discount},
        {"metric": "Avg Discount Rate",    "value": f"{discount_pct:.1f}%",        "raw": discount_pct},
    ])
    return kpis


def _regional_summary(df: pd.DataFrame) -> pd.DataFrame:
    completed = df[df["status"] == "completed"]
    grp = (
        completed.groupby("region")
        .agg(
            orders=("order_id", "count"),
            revenue=("net_revenue", "sum"),
            units=("quantity", "sum"),
            customers=("customer_id", "nunique"),
        )
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    grp["avg_order_value"] = grp["revenue"] / grp["orders"]
    grp["revenue_share"]   = (grp["revenue"] / grp["revenue"].sum() * 100).round(1)
    return grp


def _product_performance(df: pd.DataFrame) -> pd.DataFrame:
    completed = df[df["status"] == "completed"]
    grp = (
        completed.groupby("product")
        .agg(
            orders=("order_id", "count"),
            units=("quantity", "sum"),
            gross_revenue=("gross_revenue", "sum"),
            net_revenue=("net_revenue", "sum"),
            avg_discount=("discount", "mean"),
        )
        .reset_index()
        .sort_values("net_revenue", ascending=False)
    )
    grp["margin_pct"] = ((grp["net_revenue"] / grp["gross_revenue"]) * 100).round(1)
    return grp


def _top_salespeople(df: pd.DataFrame) -> pd.DataFrame:
    completed = df[df["status"] == "completed"]
    grp = (
        completed.groupby("salesperson")
        .agg(
            orders=("order_id", "count"),
            revenue=("net_revenue", "sum"),
            units=("quantity", "sum"),
            customers=("customer_id", "nunique"),
        )
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    grp["rank"] = range(1, len(grp) + 1)
    grp["revenue_per_order"] = (grp["revenue"] / grp["orders"]).round(2)
    return grp[["rank", "salesperson", "orders", "revenue", "units", "customers", "revenue_per_order"]]


def _daily_trend(df: pd.DataFrame) -> pd.DataFrame:
    completed = df[df["status"] == "completed"]
    grp = (
        completed.groupby("date")
        .agg(
            orders=("order_id", "count"),
            revenue=("net_revenue", "sum"),
            units=("quantity", "sum"),
        )
        .reset_index()
        .sort_values("date")
    )
    grp["cumulative_revenue"] = grp["revenue"].cumsum()
    grp["date_str"] = grp["date"].dt.strftime(DATE_FORMAT)
    return grp


def _category_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    completed = df[df["status"] == "completed"]
    grp = (
        completed.groupby("category")
        .agg(
            orders=("order_id", "count"),
            revenue=("net_revenue", "sum"),
            units=("quantity", "sum"),
        )
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    grp["revenue_share"] = (grp["revenue"] / grp["revenue"].sum() * 100).round(1)
    return grp


def _inventory_analysis(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["stock_value"]      = df["current_stock"] * df["unit_cost"]
    df["reorder_needed"]   = df["current_stock"] <= df["reorder_level"]
    df["stock_status"]     = df.apply(
        lambda r: "⚠ Low Stock" if r["reorder_needed"] else "✓ OK", axis=1
    )
    df["potential_revenue"] = df["current_stock"] * df["unit_price"]
    return df.sort_values("current_stock")
