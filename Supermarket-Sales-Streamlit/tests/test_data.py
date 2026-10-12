"""Tests for loading and cleaning the supermarket sales workbook."""

import unittest

from sales_dashboard.data import WORKBOOK_PATH, get_data_quality, load_sales_data


class SalesDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sales = load_sales_data(WORKBOOK_PATH)

    def test_restores_all_499_transactions_and_discards_broken_header(self) -> None:
        self.assertEqual(len(self.sales), 499)
        self.assertEqual(
            self.sales["Invoice ID"].head(3).tolist(),
            ["INV0001", "INV0002", "INV0003"],
        )
        self.assertTrue(self.sales["Invoice ID"].str.fullmatch(r"INV\d+").all())

    def test_recalculates_sales_from_quantity_and_unit_price(self) -> None:
        expected_sales = (self.sales["Quantity"] * self.sales["Unit Price"]).round(2)
        difference = (self.sales["Sales"] - expected_sales).abs()
        self.assertTrue((difference < 0.01).all())

    def test_dates_and_analysis_fields_are_available(self) -> None:
        self.assertTrue(self.sales["Date"].notna().all())
        self.assertTrue(self.sales["Month"].notna().all())
        for column in ("City", "Branch", "Category", "Product", "Payment"):
            with self.subTest(column=column):
                self.assertTrue(self.sales[column].notna().all())

    def test_quality_summary_counts_loaded_rows(self) -> None:
        quality = get_data_quality(self.sales)
        self.assertEqual(quality["rows"], 499)
        self.assertIn("sales_mismatches", quality)
        self.assertIn("missing_values", quality)


if __name__ == "__main__":
    unittest.main()
