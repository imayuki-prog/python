"""Unit tests for inventory check and alert logic (no API calls)."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from monitor import build_alert_message, check_inventory
from unittest.mock import MagicMock


def test_alert_message_zero_stock():
    items = [{"sku": "SKU-001", "quantity": 0}, {"sku": "SKU-002", "quantity": 0}]
    subject, body = build_alert_message(items, threshold=0)
    assert "在庫ゼロ" in body
    assert "SKU-001" in body
    assert "SKU-002" in body
    assert "2件ゼロ" in subject


def test_alert_message_low_stock():
    items = [{"sku": "SKU-003", "quantity": 3}]
    subject, body = build_alert_message(items, threshold=5)
    assert "在庫少" in body
    assert "SKU-003" in body


def test_alert_message_mixed():
    items = [
        {"sku": "SKU-001", "quantity": 0},
        {"sku": "SKU-002", "quantity": 2},
    ]
    subject, body = build_alert_message(items, threshold=5)
    assert "在庫ゼロ" in body
    assert "在庫少" in body


def test_check_inventory_filters_zero():
    client = MagicMock()
    client.get_all_skus.return_value = ["A", "B", "C"]
    client.get_inventory_bulk.return_value = [
        {"sku": "A", "quantity": 10},
        {"sku": "B", "quantity": 0},
        {"sku": "C", "quantity": 5},
    ]
    result = check_inventory(client, threshold=0)
    assert len(result) == 1
    assert result[0]["sku"] == "B"


def test_check_inventory_filters_low():
    client = MagicMock()
    client.get_all_skus.return_value = ["A", "B", "C"]
    client.get_inventory_bulk.return_value = [
        {"sku": "A", "quantity": 10},
        {"sku": "B", "quantity": 0},
        {"sku": "C", "quantity": 3},
    ]
    result = check_inventory(client, threshold=5)
    skus = {r["sku"] for r in result}
    assert skus == {"B", "C"}


if __name__ == "__main__":
    tests = [
        test_alert_message_zero_stock,
        test_alert_message_low_stock,
        test_alert_message_mixed,
        test_check_inventory_filters_zero,
        test_check_inventory_filters_low,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} tests passed")
