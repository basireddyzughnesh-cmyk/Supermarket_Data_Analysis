"""Load and clean the supermarket transaction workbook."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKBOOK_PATH = PROJECT_ROOT / "data" / "raw" / "supermarket_sales_500_rows.csv.xlsx"
SHEET_NAME = "Table 1"

COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "Invoice ID": ("invoice id", "invoiceid", "invoice"),
    "Date": ("date", "sales date", "transaction date"),
    "Branch": ("branch", "store", "store branch"),
    "City": ("city", "location", "town"),
    "Customer Type": ("customer type", "customer"),
    "Gender": ("gender", "sex"),
    "Product": ("product", "product name", "product line"),
    "Category": ("category", "product category"),
    "Quantity": ("quantity", "qty"),
    "Unit Price": ("unit price", "unitprice", "price"),
    "Payment": ("payment", "payment method"),
    "Rating": ("rating", "customer rating"),
    "Sales": ("sales", "total", "revenue"),
}

REQUIRED_COLUMNS = tuple(COLUMN_ALIASES)
NUMERIC_COLUMNS = ("Quantity", "Unit Price", "Rating", "Sales")


def _normalize(value: object) -> str:
    return " ".join(str(value).strip().lower().replace("_", " ").split())


def _map_columns(columns: pd.Index) -> dict[str, str]:
    """Map workbook headers to canonical names, preserving unknown columns."""
    mapped: dict[str, str] = {}

    for raw_column in columns:
        raw_name = str(raw_column)
        first_line = _normalize(raw_name.splitlines()[0])
        matches = [
            target
            for target, aliases in COLUMN_ALIASES.items()
            if any(
                first_line == alias or first_line.startswith(f"{alias} ")
                for alias in aliases
            )
        ]
        if len(matches) > 1:
            raise ValueError(f"Ambiguous workbook column header: {raw_name!r}.")
        mapped[raw_name] = matches[0] if matches else raw_name

    canonical_names = [
        name for name in mapped.values() if name in COLUMN_ALIASES
    ]
    duplicates = sorted(
        name for name in set(canonical_names) if canonical_names.count(name) > 1
    )
    if duplicates:
        raise ValueError(
            "Multiple workbook columns map to the same field: "
            + ", ".join(duplicates)
        )

    missing = sorted(set(REQUIRED_COLUMNS) - set(canonical_names))
    if missing:
        raise ValueError(
            "Required workbook column(s) missing: "
            + ", ".join(missing)
            + ". Available columns: "
            + ", ".join(mapped.values())
        )

    return mapped


def _extract_header_values(
    header: str, target: str, observed_values: pd.Series
) -> list[object]:
    """Read data values embedded after a field name in a workbook header."""
    if target == "Date":
        return re.findall(r"\d{4}-\d{2}-\d{2}", header)

    if target == "Invoice ID":
        return re.findall(r"\b[A-Za-z]{2,}\d+\b", header)

    if target in NUMERIC_COLUMNS:
        return re.findall(r"(?<!\w)-?\d+(?:\.\d+)?(?!\w)", header)

    vocabulary = sorted(
        {str(value) for value in observed_values.dropna().unique()},
        key=lambda value: (-len(value), value.casefold()),
    )
    if not vocabulary:
        return []

    alternatives = "|".join(re.escape(value) for value in vocabulary)
    pattern = re.compile(rf"(?<!\w)(?:{alternatives})(?!\w)", re.IGNORECASE)
    return [match.group(0) for match in pattern.finditer(header)]


def load_sales_data(workbook_path: str | Path = WORKBOOK_PATH) -> pd.DataFrame:
    """Load the workbook and return cleaned, analysis-ready transactions."""
    path = Path(workbook_path)
    if not path.is_file():
        raise FileNotFoundError(f"Sales workbook not found: {path}")

    raw = pd.read_excel(path, sheet_name=SHEET_NAME, header=0)
    column_map = _map_columns(raw.columns)

    embedded_rows: dict[str, list[object]] = {}
    for raw_column, target in column_map.items():
        embedded_rows[target] = _extract_header_values(
            str(raw_column),
            target,
            raw[raw_column].iloc[1:],
        )

    has_embedded_data = any(embedded_rows.values())
    if has_embedded_data:
        missing_embedded = [
            column
            for column in REQUIRED_COLUMNS
            if len(embedded_rows[column]) != 3
        ]
        if missing_embedded:
            raise ValueError(
                "The workbook has data embedded in its headers, but exactly "
                "three values could not be recovered for: "
                + ", ".join(missing_embedded)
            )

        restored = pd.DataFrame(
            {
                target: embedded_rows[target]
                for target in REQUIRED_COLUMNS
            }
        )
        transactions = raw.iloc[1:].rename(columns=column_map)
        transactions = pd.concat(
            [restored, transactions],
            ignore_index=True,
        )
    else:
        transactions = raw.rename(columns=column_map).copy()

    transactions = transactions.dropna(how="all").reset_index(drop=True)
    transactions["Date"] = pd.to_datetime(transactions["Date"], errors="coerce")

    for column in NUMERIC_COLUMNS:
        transactions[column] = pd.to_numeric(
            transactions[column],
            errors="coerce",
        )

    transactions["Sales_Original"] = transactions["Sales"]
    transactions["Sales"] = (
        transactions["Quantity"] * transactions["Unit Price"]
    ).round(2)
    transactions["Month"] = transactions["Date"].dt.to_period("M").dt.to_timestamp()

    return transactions


def get_data_quality(data: pd.DataFrame) -> dict[str, int | float]:
    """Summarize missing values and original-sales calculation differences."""
    original_sales = data["Sales_Original"]
    calculated_sales = data["Quantity"] * data["Unit Price"]
    difference = (original_sales - calculated_sales).abs()

    invoice_ids = data["Invoice ID"].dropna()
    duplicate_invoice_rows = int(invoice_ids.duplicated(keep=False).sum())

    return {
        "rows": len(data),
        "missing_values": int(data.isna().sum().sum()),
        "duplicate_invoices": duplicate_invoice_rows,
        "sales_mismatches": int((difference > 0.05).sum()),
        "original_sales_mismatches": float(
            difference.fillna(0).sum().round(2)
        ),
    }
