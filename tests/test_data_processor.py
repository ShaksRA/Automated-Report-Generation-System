"""
Test suite for the Automated Report Generation System.
Run: pytest tests/ -v
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.data_processor import (
    _compute_kpis,
    _regional_summary,
    _product_performance,
    _top_salespeople,
    _daily_trend,
    _category_breakdown,
    _inventory_analysis,
)


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_sales() -> pd.DataFrame:
    return pd.DataFrame({
        "order_id":     ["O1", "O2", "O3", "O4"],
        "date":         pd.to_datetime(["2024-05-01", "2024-05-02", "2024-05-03", "2024-05-04"]),
        "region":       ["North", "South", "North", "East"],
        "salesperson":  ["Alice", "Bob", "Alice", "Carol"],
        "product":      ["Prod A", "Prod B", "Prod A", "Prod C"],
        "category":     ["Electronics", "Clothing", "Electronics", "Food"],
        "quantity":     [2, 5, 3, 10],
        "unit_price":   [100.0, 50.0, 100.0, 20.0],
        "discount":     [0.0, 0.1, 0.0, 0.0],
        "gross_revenue":[200.0, 250.0, 300.0, 200.0],
        "discount_amt": [0.0, 25.0, 0.0, 0.0],
        "net_revenue":  [200.0, 225.0, 300.0, 200.0],
        "status":       ["completed", "completed", "completed", "cancelled"],
        "customer_id":  ["C1", "C2", "C1", "C3"],
        "segment":      ["Gold", "Standard", "Gold", "Premium"],
        "week":         [18, 19, 19, 19],
        "month":        [5, 5, 5, 5],
        "day_name":     ["Wednesday", "Thursday", "Friday", "Saturday"],
    })


@pytest.fixture
def sample_inventory() -> pd.DataFrame:
    return pd.DataFrame({
        "product_name":   ["Prod A", "Prod B"],
        "category":       ["Electronics", "Clothing"],
        "sku":            ["SKU-001", "SKU-002"],
        "unit_cost":      [60.0, 25.0],
        "unit_price":     [100.0, 50.0],
        "current_stock":  [30, 150],
        "reorder_level":  [50, 100],
        "supplier":       ["SupplierX", "SupplierY"],
        "last_restocked": pd.to_datetime(["2024-04-01", "2024-04-15"]),
    })


# ──────────────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────────────

class TestComputeKPIs:
    def test_returns_dataframe(self, sample_sales):
        result = _compute_kpis(sample_sales)
        assert isinstance(result, pd.DataFrame)

    def test_has_required_columns(self, sample_sales):
        result = _compute_kpis(sample_sales)
        assert "metric" in result.columns
        assert "value"  in result.columns

    def test_revenue_excludes_cancelled(self, sample_sales):
        result = _compute_kpis(sample_sales)
        rev_row = result[result["metric"] == "Total Revenue"].iloc[0]
        # Completed orders: 200 + 225 + 300 = 725
        assert "$725.00" in rev_row["value"]

    def test_order_count_excludes_cancelled(self, sample_sales):
        result = _compute_kpis(sample_sales)
        orders = result[result["metric"] == "Total Orders"].iloc[0]
        assert orders["value"] == "3"


class TestRegionalSummary:
    def test_returns_correct_regions(self, sample_sales):
        result = _regional_summary(sample_sales)
        regions = set(result["region"].tolist())
        assert "North" in regions
        assert "South" in regions

    def test_sorted_by_revenue_descending(self, sample_sales):
        result = _regional_summary(sample_sales)
        revenues = result["revenue"].tolist()
        assert revenues == sorted(revenues, reverse=True)

    def test_revenue_share_sums_to_100(self, sample_sales):
        result = _regional_summary(sample_sales)
        assert abs(result["revenue_share"].sum() - 100.0) < 0.5


class TestProductPerformance:
    def test_returns_dataframe(self, sample_sales):
        result = _product_performance(sample_sales)
        assert isinstance(result, pd.DataFrame)

    def test_margin_between_0_and_100(self, sample_sales):
        result = _product_performance(sample_sales)
        assert (result["margin_pct"] >= 0).all()
        assert (result["margin_pct"] <= 100).all()


class TestTopSalespeople:
    def test_rank_column_present(self, sample_sales):
        result = _top_salespeople(sample_sales)
        assert "rank" in result.columns

    def test_rank_starts_at_1(self, sample_sales):
        result = _top_salespeople(sample_sales)
        assert result["rank"].min() == 1

    def test_sorted_by_revenue(self, sample_sales):
        result = _top_salespeople(sample_sales)
        revenues = result["revenue"].tolist()
        assert revenues == sorted(revenues, reverse=True)


class TestDailyTrend:
    def test_cumulative_revenue_monotone(self, sample_sales):
        result = _daily_trend(sample_sales)
        cum = result["cumulative_revenue"].tolist()
        assert all(cum[i] <= cum[i + 1] for i in range(len(cum) - 1))

    def test_date_str_column_present(self, sample_sales):
        result = _daily_trend(sample_sales)
        assert "date_str" in result.columns


class TestCategoryBreakdown:
    def test_revenue_share_sums_near_100(self, sample_sales):
        result = _category_breakdown(sample_sales)
        assert abs(result["revenue_share"].sum() - 100.0) < 0.5


class TestInventoryAnalysis:
    def test_low_stock_detected(self, sample_inventory):
        result = _inventory_analysis(sample_inventory)
        # Prod A: stock 30 < reorder 50 → low
        low = result[result["product_name"] == "Prod A"].iloc[0]
        assert low["reorder_needed"] is True or low["reorder_needed"] == True

    def test_ok_stock_not_flagged(self, sample_inventory):
        result = _inventory_analysis(sample_inventory)
        ok = result[result["product_name"] == "Prod B"].iloc[0]
        assert ok["reorder_needed"] is False or ok["reorder_needed"] == False

    def test_stock_value_calculated(self, sample_inventory):
        result = _inventory_analysis(sample_inventory)
        row = result[result["product_name"] == "Prod A"].iloc[0]
        # 30 units × $60 cost = $1800
        assert row["stock_value"] == pytest.approx(1800.0)
