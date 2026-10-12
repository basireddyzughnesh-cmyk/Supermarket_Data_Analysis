import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
from pathlib import Path

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="Supermarket Sales Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────

st.markdown(
    """
    <style>
        .metric-card {
            background: #f7f8fa;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            padding: 16px 20px;
            text-align: center;
        }

        .metric-label {
            font-size: 13px;
            color: #57606a;
            font-weight: 500;
            margin-bottom: 4px;
        }

        .metric-value {
            font-size: 26px;
            font-weight: 700;
            color: #1f2328;
        }

        .section-header {
            font-size: 18px;
            font-weight: 700;
            color: #1f2328;
            border-left: 4px solid #3b82d4;
            padding-left: 10px;
            margin: 20px 0 10px 0;
        }

        .insight-box {
            background: #f0f6ff;
            border: 1px solid #bfdbfe;
            border-radius: 8px;
            padding: 14px 18px;
            margin: 8px 0;
            font-size: 14px;
            color: #1e3a5f;
        }

        .warning-box {
            background: #fff8f0;
            border: 1px solid #fcd9a8;
            border-radius: 8px;
            padding: 14px 18px;
            margin: 8px 0;
            font-size: 14px;
            color: #7c3d12;
        }

        .success-box {
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            border-radius: 8px;
            padding: 14px 18px;
            margin: 8px 0;
            font-size: 14px;
            color: #14532d;
        }

        div[data-testid="stDataFrame"] {
            border-radius: 8px;
            overflow: hidden;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# 1. LOAD DATA
# ─────────────────────────────────────────────

@st.cache_data
def load_data():

    file_path = (
        Path(__file__).resolve().parent
        / "data"
        / "raw"
        / "supermarket_sales_500_rows.csv.xlsx"
    )

    df = pd.read_excel(
        file_path,
        sheet_name="Table 1",
        header=0,
    )

    # ─────────────────────────────────────────
    # NORMALIZE COLUMN NAMES
    # ─────────────────────────────────────────

    def norm_col(name):
        return (
            " ".join(
                str(name)
                .strip()
                .lower()
                .replace("_", " ")
                .split()
            )
        )

    aliases = {
        "Invoice ID": [
            "invoice id",
            "invoiceid",
            "invoice",
        ],
        "Date": [
            "date",
            "sales date",
            "transaction date",
        ],
        "Branch": [
            "branch",
            "store",
            "store branch",
        ],
        "City": [
            "city",
            "location",
            "town",
        ],
        "Customer Type": [
            "customer type",
            "customer_type",
            "customer",
        ],
        "Gender": [
            "gender",
            "sex",
        ],
        "Product": [
            "product",
            "product name",
            "product_name",
            "product line",
            "product_line",
        ],
        "Category": [
            "category",
            "product category",
            "product_category",
        ],
        "Quantity": [
            "quantity",
            "qty",
        ],
        "Unit Price": [
            "unit price",
            "unitprice",
            "price",
        ],
        "Payment": [
            "payment",
            "payment method",
            "payment_method",
        ],
        "Rating": [
            "rating",
            "customer rating",
            "customer_rating",
        ],
        "Sales": [
            "sales",
            "total",
            "revenue",
        ],
    }

    expected = list(aliases.keys())

    # ─────────────────────────────────────────
    # DETECT MALFORMED HEADER
    # ─────────────────────────────────────────

    raw_headers = [
        str(c)
        .replace("\r", "")
        .replace("\n", "\n")
        .strip()
        for c in df.columns
    ]

    header_text = " ".join(raw_headers)

    malformed = (
        "INV0001" in header_text
        and "INV0002" in header_text
        and "INV0003" in header_text
    )

    if malformed:

        def values_for(target, text):

            text = (
                str(text)
                .replace("\r", "")
                .replace("\n", "\n")
            )

            if target == "Invoice ID":
                return re.findall(
                    r"INV\d+",
                    text,
                    re.I
                )[:3]

            if target == "Date":
                return re.findall(
                    r"\d{4}-\d{2}-\d{2}",
                    text
                )[:3]

            if target == "Branch":
                return re.findall(
                    r"\b[A-Z]\b",
                    text
                )[:3]

            if target == "City":
                return re.findall(
                    r"Jaipur|Mumbai|Delhi|Chennai|Hyderabad|Bangalore|Kolkata|Pune",
                    text,
                    re.I
                )[:3]

            if target == "Customer Type":
                return re.findall(
                    r"Member|Normal",
                    text,
                    re.I
                )[:3]

            if target == "Gender":
                return re.findall(
                    r"Male|Female",
                    text,
                    re.I
                )[:3]

            if target == "Product":
                return re.findall(
                    r"Milk|Rice|Apples|Soap|Shampoo|Bread|Juice|Biscuits|Eggs|Chicken|Meat|Coffee|Tea",
                    text,
                    re.I
                )[:3]

            if target == "Category":
                return re.findall(
                    r"Personal Care|Dairy|Grocery|Fruits|Vegetables|Beverages|Bakery",
                    text,
                    re.I
                )[:3]

            if target == "Quantity":
                return re.findall(
                    r"\b\d+(?:\.\d+)?\b",
                    text
                )[:3]

            if target == "Unit Price":
                return re.findall(
                    r"\b\d+(?:\.\d+)?\b",
                    text
                )[:3]

            if target == "Payment":
                return re.findall(
                    r"Net Banking|Credit Card|Debit Card|UPI|Cash|Card",
                    text,
                    re.I
                )[:3]

            if target == "Rating":
                return re.findall(
                    r"\b\d+\.\d+\b",
                    text
                )[:3]

            if target == "Sales":
                return re.findall(
                    r"\b\d+(?:\.\d+)?\b",
                    text
                )[:3]

            return []

        # ─────────────────────────────────────
        # EXTRACT EMBEDDED VALUES
        # ─────────────────────────────────────

        embedded = {}

        for target in expected:

            aliases_for_target = aliases[target]

            raw = next(
                (
                    h
                    for h in raw_headers
                    if any(
                        norm_col(h).startswith(norm_col(a))
                        for a in aliases_for_target
                    )
                ),
                "",
            )

            embedded[target] = values_for(
                target,
                raw
            )

        # ─────────────────────────────────────
        # RECONSTRUCT FIRST 3 ROWS
        # ─────────────────────────────────────

        if all(
            len(embedded[c]) == 3
            for c in expected
        ):

            first_three = pd.DataFrame(
                embedded,
                columns=expected
            )

            remaining = df.copy()

            if len(remaining.columns) == len(expected):

                remaining.columns = expected

                remaining = remaining[expected]

                df = pd.concat(
                    [
                        first_three,
                        remaining
                    ],
                    ignore_index=True
                )

    # ─────────────────────────────────────────
    # CLEAN FINAL COLUMN NAMES
    # ─────────────────────────────────────────

    df.columns = [
        str(c)
        .replace("\r", "")
        .replace("\n", " ")
        .strip()
        for c in df.columns
    ]

    df.columns = (
        pd.Index(df.columns)
        .str.replace(
            r"\s+",
            " ",
            regex=True
        )
        .str.strip()
    )

    # ─────────────────────────────────────────
    # RENAME COLUMNS USING ALIASES
    # ─────────────────────────────────────────

    normalized = {
        norm_col(c): c
        for c in df.columns
    }

    rename_map = {}

    for target, choices in aliases.items():

        if target in df.columns:
            continue

        for choice in choices:

            key = norm_col(choice)

            if key in normalized:

                rename_map[
                    normalized[key]
                ] = target

                break

    if rename_map:
        df.rename(
            columns=rename_map,
            inplace=True
        )

    # ─────────────────────────────────────────
    # REMOVE EMPTY ROWS
    # ─────────────────────────────────────────

    df.dropna(
        how="all",
        inplace=True
    )

    df.reset_index(
        drop=True,
        inplace=True
    )

    # ─────────────────────────────────────────
    # REQUIRED COLUMNS
    # ─────────────────────────────────────────

    required = [
        "Date",
        "Quantity",
        "Unit Price",
        "Rating",
        "Sales",
        "Category",
        "Product",
        "Branch",
        "Gender",
        "Customer Type",
        "Payment",
    ]

    missing_required = [
        c
        for c in required
        if c not in df.columns
    ]

    if missing_required:

        raise ValueError(
            "Required column(s) missing: "
            + ", ".join(missing_required)
            + "\n\nAvailable columns: "
            + ", ".join(
                map(str, df.columns)
            )
        )

    # ─────────────────────────────────────────
    # OPTIONAL COLUMNS
    # ─────────────────────────────────────────

    if "Invoice ID" not in df.columns:

        st.warning(
            "⚠️ Invoice ID column was not found. "
            "Invoice-ID duplicate checking will be skipped."
        )

    if "City" not in df.columns:

        st.warning(
            "⚠️ City column was not found. "
            "City filters/analysis will be skipped."
        )

    # ─────────────────────────────────────────
    # DATA TYPES
    # ─────────────────────────────────────────

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce"
    )

    for col in [
        "Quantity",
        "Unit Price",
        "Rating",
        "Sales",
    ]:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    # ─────────────────────────────────────────
    # SALES CALCULATION
    # ─────────────────────────────────────────

    df["Sales_Original"] = df["Sales"]

    df["Sales_Calc"] = (
        df["Quantity"]
        * df["Unit Price"]
    )

    df["Sales"] = df["Sales_Calc"]

    # ─────────────────────────────────────────
    # DATE FEATURES
    # ─────────────────────────────────────────

    df["Month"] = (
        df["Date"]
        .dt.to_period("M")
        .astype(str)
    )

    df["Month_dt"] = (
        df["Date"]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    df["Week"] = (
        df["Date"]
        .dt.isocalendar()
        .week
        .astype("Int64")
    )

    return df


# LOAD DATA
df = load_data()

# ─────────────────────────────────────────────
# 2. DATA QUALITY CHECK
# ─────────────────────────────────────────────

def quality_report(df):

    report = {}

    report["total_rows"] = len(df)

    report["missing"] = df.isnull().sum()

    if len(df) > 0:

        report["missing_pct"] = (
            df.isnull().sum()
            / len(df)
            * 100
        ).round(2)

    else:

        report["missing_pct"] = pd.Series(
            0,
            index=df.columns
        )

    # Invoice ID duplicate check
    invoice_col = next(
        (
            c
            for c in df.columns
            if str(c)
            .strip()
            .lower()
            .replace("_", " ")
            == "invoice id"
        ),
        None
    )

    if invoice_col is not None:

        report["duplicates"] = (
            df.duplicated(
                subset=invoice_col,
                keep=False
            ).sum()
        )

    else:

        report["duplicates"] = None

    report["negative_qty"] = (
        df["Quantity"] < 0
    ).sum()

    report["negative_price"] = (
        df["Unit Price"] < 0
    ).sum()

    report["zero_sales"] = (
        df["Sales"] == 0
    ).sum()

    diff = (
        df["Sales_Calc"]
        - df["Sales_Original"]
    ).abs()

    report["sales_mismatch"] = (
        diff > 0.05
    ).sum()

    report["date_nulls"] = (
        df["Date"].isnull()
    ).sum()

    return report


qr = quality_report(df)

# ─────────────────────────────────────────────
# SIDEBAR – FILTERS
# ─────────────────────────────────────────────

with st.sidebar:

    st.image(
        "https://img.icons8.com/color/96/000000/shopping-cart.png",
        width=64
    )

    st.title("🛒 Filters")

    st.markdown("---")

    city_available = "City" in df.columns

    # City filter
    if city_available:

        all_cities = sorted(
            df["City"]
            .dropna()
            .astype(str)
            .unique()
        )

        sel_cities = st.multiselect(
            "City",
            all_cities,
            default=all_cities
        )

    else:

        all_cities = []

        sel_cities = []

        st.caption(
            "ℹ️ City filter unavailable: "
            "City column not present in source data."
        )

    # Category
    all_cats = sorted(
        df["Category"]
        .dropna()
        .unique()
    )

    sel_cats = st.multiselect(
        "Category",
        all_cats,
        default=all_cats
    )

    # Gender
    all_genders = sorted(
        df["Gender"]
        .dropna()
        .unique()
    )

    sel_genders = st.multiselect(
        "Gender",
        all_genders,
        default=all_genders
    )

    # Customer type
    all_cust = sorted(
        df["Customer Type"]
        .dropna()
        .unique()
    )

    sel_cust = st.multiselect(
        "Customer Type",
        all_cust,
        default=all_cust
    )

    # Payment
    all_pay = sorted(
        df["Payment"]
        .dropna()
        .unique()
    )

    sel_pay = st.multiselect(
        "Payment Method",
        all_pay,
        default=all_pay
    )

    # Date
    valid_dates = df["Date"].dropna()

    if not valid_dates.empty:

        date_min = valid_dates.min().date()
        date_max = valid_dates.max().date()

        date_range = st.date_input(
            "Date Range",
            value=(date_min, date_max),
            min_value=date_min,
            max_value=date_max
        )

    else:

        date_range = ()

    st.markdown("---")

    st.caption(
        "Data: supermarket_sales_500_rows.csv.xlsx"
    )

# ─────────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────────

mask = (
    (
        df["City"].isin(sel_cities)
        if city_available
        else True
    )
    &
    df["Category"].isin(sel_cats)
    &
    df["Gender"].isin(sel_genders)
    &
    df["Customer Type"].isin(sel_cust)
    &
    df["Payment"].isin(sel_pay)
)

if len(date_range) == 2:

    mask &= (
        df["Date"].dt.date
        >= date_range[0]
    ) & (
        df["Date"].dt.date
        <= date_range[1]
    )

fdf = df[mask].copy()

if fdf.empty:

    st.warning(
        "⚠️ No transactions match the selected filters. "
        "Clear or widen the filters to continue."
    )

    st.stop()

# ─────────────────────────────────────────────
# MAIN TITLE
# ─────────────────────────────────────────────

st.title(
    "🛒 Supermarket Sales Dashboard"
)

if len(date_range) == 2:

    st.caption(
        f"Showing **{len(fdf):,}** of "
        f"**{len(df):,}** transactions · "
        f"Date range: {date_range[0]} → "
        f"{date_range[1]}"
    )

else:

    st.caption(
        f"Showing **{len(fdf):,}** of "
        f"**{len(df):,}** transactions"
    )

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────

tabs = st.tabs(
    [
        "📊 Overview",
        "🔍 Data Quality",
        "📦 Category & Product",
        "🏙️ City & Branch",
        "👥 Customer Insights",
        "💳 Payment Analysis",
        "📈 Trends",
        "💡 Business Decisions",
        "📋 Raw Data",
    ]
)

COLORS = px.colors.qualitative.Set2

# ═══════════════════════════════════════════════
# TAB 1 – OVERVIEW
# ═══════════════════════════════════════════════

with tabs[0]:

    st.markdown(
        '<div class="section-header">Key Metrics</div>',
        unsafe_allow_html=True
    )

    total_sales = fdf["Sales"].sum()
    total_txn = len(fdf)
    avg_txn = fdf["Sales"].mean()
    avg_rating = fdf["Rating"].mean()
    total_qty = fdf["Quantity"].sum()
    avg_unit = fdf["Unit Price"].mean()

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    metrics = [
        (
            c1,
            "Total Sales",
            total_sales,
            "₹{:,.0f}"
        ),
        (
            c2,
            "Transactions",
            total_txn,
            "{:,}"
        ),
        (
            c3,
            "Avg Transaction",
            avg_txn,
            "₹{:,.2f}"
        ),
        (
            c4,
            "Avg Rating",
            avg_rating,
            "{:.2f} ⭐"
        ),
        (
            c5,
            "Units Sold",
            total_qty,
            "{:,.0f}"
        ),
        (
            c6,
            "Avg Unit Price",
            avg_unit,
            "₹{:,.2f}"
        ),
    ]

    for col, label, value, fmt in metrics:

        col.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">
                    {label}
                </div>
                <div class="metric-value">
                    {fmt.format(value)}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")

    col_l, col_r = st.columns(2)

    # Category sales
    with col_l:

        st.markdown(
            '<div class="section-header">'
            'Sales by Category'
            '</div>',
            unsafe_allow_html=True
        )

        cat_sales = (
            fdf.groupby("Category")["Sales"]
            .sum()
            .sort_values(ascending=True)
        )

        fig = px.bar(
            cat_sales,
            x=cat_sales.values,
            y=cat_sales.index,
            orientation="h",
            color=cat_sales.index,
            color_discrete_sequence=COLORS,
            labels={
                "x": "Total Sales (₹)",
                "y": ""
            },
            text=cat_sales.values
        )

        fig.update_traces(
            texttemplate="₹%{text:,.0f}",
            textposition="outside"
        )

        fig.update_layout(
            showlegend=False,
            height=380,
            margin=dict(
                l=10,
                r=20,
                t=10,
                b=10
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # City sales
    with col_r:

        st.markdown(
            '<div class="section-header">'
            'Sales by City'
            '</div>',
            unsafe_allow_html=True
        )

        if city_available:

            city_sales = (
                fdf.groupby("City")["Sales"]
                .sum()
                .sort_values(
                    ascending=False
                )
            )

            fig2 = px.pie(
                values=city_sales.values,
                names=city_sales.index,
                color_discrete_sequence=COLORS,
                hole=0.4
            )

            fig2.update_traces(
                textinfo="label+percent",
                textfont_size=13
            )

            fig2.update_layout(
                height=380,
                margin=dict(
                    l=10,
                    r=10,
                    t=10,
                    b=10
                )
            )

            st.plotly_chart(
                fig2,
                use_container_width=True
            )

        else:

            st.info(
                "City analysis is unavailable "
                "because the source data has no City column."
            )

# ═══════════════════════════════════════════════
# TAB 2 – DATA QUALITY
# ═══════════════════════════════════════════════

with tabs[1]:

    st.markdown(
        '<div class="section-header">'
        'Data Quality Report'
        '</div>',
        unsafe_allow_html=True
    )

    q1, q2, q3, q4 = st.columns(4)

    q1.metric(
        "Total Rows",
        f"{qr['total_rows']:,}"
    )

    q2.metric(
        "Duplicate Invoice IDs",
        (
            "N/A"
            if qr["duplicates"] is None
            else f"{qr['duplicates']:,}"
        ),
        delta=(
            "ℹ️ skipped"
            if qr["duplicates"] is None
            else (
                "⚠️ needs review"
                if qr["duplicates"] > 0
                else "✅ None"
            )
        )
    )

    q3.metric(
        "Negative Quantities",
        f"{qr['negative_qty']:,}",
        delta=(
            "⚠️ check data"
            if qr["negative_qty"] > 0
            else "✅ None"
        )
    )

    q4.metric(
        "Sales Calculation Mismatches",
        f"{qr['sales_mismatch']:,}",
        delta=(
            "recalculated"
            if qr["sales_mismatch"] > 0
            else "✅ Consistent"
        )
    )

    st.markdown(
        "#### Missing Values per Column"
    )

    miss_df = pd.DataFrame(
        {
            "Column": qr["missing"].index,
            "Missing Count": qr["missing"].values,
            "Missing %": qr["missing_pct"].values,
        }
    ).reset_index(drop=True)

    if miss_df["Missing Count"].sum() == 0:

        st.markdown(
            '<div class="success-box">'
            '✅ No missing values detected across all columns.'
            '</div>',
            unsafe_allow_html=True
        )

    else:

        st.dataframe(
            miss_df[
                miss_df["Missing Count"] > 0
            ],
            use_container_width=True
        )

    # Sales check
    st.markdown(
        "#### Sales Recalculation Check "
        "(Quantity × Unit Price)"
    )

    comp_cols = [
        "Quantity",
        "Unit Price",
        "Sales_Original",
        "Sales_Calc",
    ]

    if "Invoice ID" in df.columns:

        comp_cols.insert(
            0,
            "Invoice ID"
        )

    comp_df = df[comp_cols].copy()

    comp_df["Difference"] = (
        comp_df["Sales_Calc"]
        - comp_df["Sales_Original"]
    ).round(2)

    comp_df["Match"] = (
        comp_df["Difference"].abs()
        < 0.05
    )

    match_pct = (
        comp_df["Match"].mean()
        * 100
    )

    st.progress(
        int(match_pct),
        text=(
            f"{match_pct:.1f}% of rows match "
            "Qty × Unit Price within ₹0.05"
        )
    )

    if qr["sales_mismatch"] > 0:

        st.markdown(
            '<div class="warning-box">'
            '⚠️ Some rows had Sales ≠ Quantity × Unit Price. '
            'The <b>Sales</b> column has been '
            '<b>recalculated</b> as Quantity × Unit Price '
            'throughout this dashboard.'
            '</div>',
            unsafe_allow_html=True
        )

        st.dataframe(
            comp_df[
                ~comp_df["Match"]
            ]
            .drop(columns=["Match"])
            .head(20),
            use_container_width=True
        )

    else:

        st.markdown(
            '<div class="success-box">'
            '✅ All Sales values match Quantity × Unit Price exactly.'
            '</div>',
            unsafe_allow_html=True
        )

    # Data types
    st.markdown(
        "#### Data Types Summary"
    )

    dtype_df = pd.DataFrame(
        {
            "Column": df.columns,
            "Dtype": df.dtypes.values.astype(str),
            "Non-Null Count": df.notnull().sum().values,
            "Sample Value": [
                (
                    str(
                        df[c]
                        .dropna()
                        .iloc[0]
                    )
                    if df[c].dropna().shape[0] > 0
                    else "—"
                )
                for c in df.columns
            ],
        }
    )

    st.dataframe(
        dtype_df,
        use_container_width=True
    )

# ═══════════════════════════════════════════════
# TAB 3 – CATEGORY & PRODUCT
# ═══════════════════════════════════════════════

with tabs[2]:

    st.markdown(
        '<div class="section-header">'
        'Category Summary'
        '</div>',
        unsafe_allow_html=True
    )

    cat_summary = (
        fdf.groupby("Category")
        .agg(
            Transactions=("Sales", "size"),
            Total_Sales=("Sales", "sum"),
            Avg_Sales=("Sales", "mean"),
            Total_Qty=("Quantity", "sum"),
            Avg_Rating=("Rating", "mean"),
        )
        .round(2)
        .sort_values(
            "Total_Sales",
            ascending=False
        )
        .reset_index()
    )

    cat_summary.columns = [
        "Category",
        "Transactions",
        "Total Sales (₹)",
        "Avg Sale (₹)",
        "Units Sold",
        "Avg Rating",
    ]

    cat_summary["Total Sales (₹)"] = (
        cat_summary["Total Sales (₹)"]
        .map("₹{:,.2f}".format)
    )

    cat_summary["Avg Sale (₹)"] = (
        cat_summary["Avg Sale (₹)"]
        .map("₹{:,.2f}".format)
    )

    st.dataframe(
        cat_summary,
        use_container_width=True,
        hide_index=True
    )

    col_a, col_b = st.columns(2)

    with col_a:

        st.markdown(
            '<div class="section-header">'
            'Total Sales by Category'
            '</div>',
            unsafe_allow_html=True
        )

        raw_cat = (
            fdf.groupby("Category")["Sales"]
            .sum()
            .sort_values(
                ascending=False
            )
            .reset_index()
        )

        fig = px.bar(
            raw_cat,
            x="Category",
            y="Sales",
            color="Category",
            color_discrete_sequence=COLORS,
            text="Sales"
        )

        fig.update_traces(
            texttemplate="₹%{text:,.0f}",
            textposition="outside"
        )

        fig.update_layout(
            showlegend=False,
            yaxis_title="Total Sales (₹)",
            height=380,
            margin=dict(t=10)
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with col_b:

        st.markdown(
            '<div class="section-header">'
            'Average Rating by Category'
            '</div>',
            unsafe_allow_html=True
        )

        raw_rating = (
            fdf.groupby("Category")["Rating"]
            .mean()
            .sort_values(
                ascending=False
            )
            .reset_index()
        )

        fig2 = px.bar(
            raw_rating,
            x="Category",
            y="Rating",
            color="Category",
            color_discrete_sequence=COLORS,
            text="Rating"
        )

        fig2.update_traces(
            texttemplate="%{text:.2f}",
            textposition="outside"
        )

        fig2.update_layout(
            showlegend=False,
            yaxis_title="Avg Rating",
            yaxis_range=[0, 5.5],
            height=380,
            margin=dict(t=10)
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

    # Top products
    st.markdown(
        '<div class="section-header">'
        'Top 15 Products by Revenue'
        '</div>',
        unsafe_allow_html=True
    )

    top_prod = (
        fdf.groupby("Product")["Sales"]
        .sum()
        .sort_values(
            ascending=False
        )
        .head(15)
        .reset_index()
    )

    fig3 = px.bar(
        top_prod,
        x="Sales",
        y="Product",
        orientation="h",
        color="Sales",
        color_continuous_scale="Blues",
        text="Sales"
    )

    fig3.update_traces(
        texttemplate="₹%{text:,.0f}",
        textposition="outside"
    )

    fig3.update_layout(
        showlegend=False,
        height=480,
        xaxis_title="Total Sales (₹)",
        yaxis_title="",
        margin=dict(
            l=10,
            r=20,
            t=10,
            b=10
        )
    )

    st.plotly_chart(
        fig3,
        use_container_width=True
    )

# ═══════════════════════════════════════════════
# TAB 4 – CITY & BRANCH
# ═══════════════════════════════════════════════

with tabs[3]:

    if not city_available:

        st.info(
            "🏙️ City & Branch analysis is unavailable "
            "because the source data does not contain "
            "a City column."
        )

    else:

        col_l, col_r = st.columns(2)

        # City performance
        with col_l:

            st.markdown(
                '<div class="section-header">'
                'City Performance'
                '</div>',
                unsafe_allow_html=True
            )

            city_sum = (
                fdf.groupby("City")
                .agg(
                    Transactions=("Sales", "size"),
                    Total_Sales=("Sales", "sum"),
                    Avg_Sale=("Sales", "mean"),
                    Avg_Rating=("Rating", "mean"),
                )
                .round(2)
                .sort_values(
                    "Total_Sales",
                    ascending=False
                )
                .reset_index()
            )

            city_sum["Total_Sales_fmt"] = (
                city_sum["Total_Sales"]
                .map("₹{:,.0f}".format)
            )

            city_sum["Avg_Sale_fmt"] = (
                city_sum["Avg_Sale"]
                .map("₹{:,.2f}".format)
            )

            city_sum["Avg_Rating"] = (
                city_sum["Avg_Rating"]
                .round(2)
            )

            st.dataframe(
                city_sum[
                    [
                        "City",
                        "Transactions",
                        "Total_Sales_fmt",
                        "Avg_Sale_fmt",
                        "Avg_Rating",
                    ]
                ].rename(
                    columns={
                        "Total_Sales_fmt":
                            "Total Sales",
                        "Avg_Sale_fmt":
                            "Avg Sale",
                        "Avg_Rating":
                            "Avg Rating",
                    }
                ),
                use_container_width=True,
                hide_index=True
            )

            fig = px.bar(
                city_sum,
                x="City",
                y="Total_Sales",
                color="City",
                color_discrete_sequence=COLORS,
                text="Total_Sales_fmt"
            )

            fig.update_traces(
                textposition="outside"
            )

            fig.update_layout(
                showlegend=False,
                yaxis_title="Total Sales (₹)",
                height=320,
                margin=dict(t=10)
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        # Branch performance
        with col_r:

            st.markdown(
                '<div class="section-header">'
                'Branch Performance'
                '</div>',
                unsafe_allow_html=True
            )

            branch_sum = (
                fdf.groupby("Branch")
                .agg(
                    Transactions=("Sales", "size"),
                    Total_Sales=("Sales", "sum"),
                    Avg_Rating=("Rating", "mean"),
                )
                .round(2)
                .sort_values(
                    "Total_Sales",
                    ascending=False
                )
                .reset_index()
            )

            branch_sum["Total_Sales_fmt"] = (
                branch_sum["Total_Sales"]
                .map("₹{:,.0f}".format)
            )

            st.dataframe(
                branch_sum[
                    [
                        "Branch",
                        "Transactions",
                        "Total_Sales_fmt",
                        "Avg_Rating",
                    ]
                ].rename(
                    columns={
                        "Total_Sales_fmt":
                            "Total Sales",
                        "Avg_Rating":
                            "Avg Rating",
                    }
                ),
                use_container_width=True,
                hide_index=True
            )

            fig2 = px.pie(
                branch_sum,
                values="Total_Sales",
                names="Branch",
                color_discrete_sequence=COLORS,
                hole=0.35
            )

            fig2.update_traces(
                textinfo="label+percent+value",
                texttemplate=(
                    "Branch %{label}<br>"
                    "%{percent}<br>"
                    "₹%{value:,.0f}"
                )
            )

            fig2.update_layout(
                height=320,
                margin=dict(
                    l=10,
                    r=10,
                    t=10,
                    b=10
                )
            )

            st.plotly_chart(
                fig2,
                use_container_width=True
            )

        # Category by city
        st.markdown(
            '<div class="section-header">'
            'Category Sales Breakdown by City'
            '</div>',
            unsafe_allow_html=True
        )

        city_cat = (
            fdf.groupby(
                ["City", "Category"]
            )["Sales"]
            .sum()
            .reset_index()
        )

        fig3 = px.bar(
            city_cat,
            x="City",
            y="Sales",
            color="Category",
            barmode="group",
            color_discrete_sequence=COLORS,
            labels={
                "Sales": "Total Sales (₹)"
            }
        )

        fig3.update_layout(
            height=400,
            margin=dict(t=10)
        )

        st.plotly_chart(
            fig3,
            use_container_width=True
        )

# ═══════════════════════════════════════════════
# TAB 5 – CUSTOMER INSIGHTS
# ═══════════════════════════════════════════════

with tabs[4]:

    col_a, col_b = st.columns(2)

    # Customer type vs gender
    with col_a:

        st.markdown(
            '<div class="section-header">'
            'Customer Type vs Gender'
            '</div>',
            unsafe_allow_html=True
        )

        cust_gender = (
            fdf.groupby(
                ["Customer Type", "Gender"]
            )["Sales"]
            .sum()
            .reset_index()
        )

        fig = px.bar(
            cust_gender,
            x="Customer Type",
            y="Sales",
            color="Gender",
            barmode="group",
            color_discrete_sequence=COLORS,
            text="Sales",
            labels={
                "Sales": "Total Sales (₹)"
            }
        )

        fig.update_traces(
            texttemplate="₹%{text:,.0f}",
            textposition="outside"
        )

        fig.update_layout(
            height=360,
            margin=dict(t=10)
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # Average spend
    with col_b:

        st.markdown(
            '<div class="section-header">'
            'Avg Spend per Transaction'
            '</div>',
            unsafe_allow_html=True
        )

        cust_avg = (
            fdf.groupby(
                ["Customer Type", "Gender"]
            )["Sales"]
            .mean()
            .reset_index()
        )

        fig2 = px.bar(
            cust_avg,
            x="Customer Type",
            y="Sales",
            color="Gender",
            barmode="group",
            color_discrete_sequence=COLORS,
            text="Sales",
            labels={
                "Sales": "Avg Sale (₹)"
            }
        )

        fig2.update_traces(
            texttemplate="₹%{text:,.2f}",
            textposition="outside"
        )

        fig2.update_layout(
            height=360,
            margin=dict(t=10)
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

    # Rating distribution
    st.markdown(
        '<div class="section-header">'
        'Rating Distribution'
        '</div>',
        unsafe_allow_html=True
    )

    fig3 = px.histogram(
        fdf,
        x="Rating",
        color="Customer Type",
        nbins=20,
        barmode="overlay",
        opacity=0.75,
        color_discrete_sequence=COLORS,
        labels={
            "Rating": "Rating",
            "count": "Count"
        }
    )

    fig3.update_layout(
        height=320,
        margin=dict(t=10)
    )

    st.plotly_chart(
        fig3,
        use_container_width=True
    )

    # Segments
    st.markdown(
        '<div class="section-header">'
        'Top Spending Customer Segments'
        '</div>',
        unsafe_allow_html=True
    )

    segment_cols = [
        "Customer Type",
        "Gender"
    ]

    if city_available:

        segment_cols.insert(
            0,
            "City"
        )

    seg = (
        fdf.groupby(segment_cols)
        .agg(
            Transactions=("Sales", "size"),
            Total_Sales=("Sales", "sum"),
            Avg_Sale=("Sales", "mean"),
            Avg_Rating=("Rating", "mean"),
        )
        .round(2)
        .sort_values(
            "Total_Sales",
            ascending=False
        )
        .reset_index()
    )

    seg["Total_Sales"] = (
        seg["Total_Sales"]
        .map("₹{:,.2f}".format)
    )

    seg["Avg_Sale"] = (
        seg["Avg_Sale"]
        .map("₹{:,.2f}".format)
    )

    st.dataframe(
        seg.rename(
            columns={
                "Total_Sales":
                    "Total Sales",
                "Avg_Sale":
                    "Avg Sale",
                "Avg_Rating":
                    "Avg Rating",
            }
        ),
        use_container_width=True,
        hide_index=True
    )

# ═══════════════════════════════════════════════
# TAB 6 – PAYMENT ANALYSIS
# ═══════════════════════════════════════════════

with tabs[5]:

    col_a, col_b = st.columns(2)

    # Payment count
    with col_a:

        st.markdown(
            '<div class="section-header">'
            'Transaction Count by Payment Method'
            '</div>',
            unsafe_allow_html=True
        )

        pay_cnt = (
            fdf["Payment"]
            .value_counts()
            .reset_index()
        )

        pay_cnt.columns = [
            "Payment",
            "Count"
        ]

        fig = px.pie(
            pay_cnt,
            values="Count",
            names="Payment",
            color_discrete_sequence=COLORS,
            hole=0.4
        )

        fig.update_traces(
            textinfo="label+percent+value"
        )

        fig.update_layout(
            height=360,
            margin=dict(
                l=10,
                r=10,
                t=10,
                b=10
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # Payment sales
    with col_b:

        st.markdown(
            '<div class="section-header">'
            'Total Sales by Payment Method'
            '</div>',
            unsafe_allow_html=True
        )

        pay_sales = (
            fdf.groupby("Payment")["Sales"]
            .sum()
            .sort_values(
                ascending=False
            )
            .reset_index()
        )

        fig2 = px.bar(
            pay_sales,
            x="Payment",
            y="Sales",
            color="Payment",
            color_discrete_sequence=COLORS,
            text="Sales"
        )

        fig2.update_traces(
            texttemplate="₹%{text:,.0f}",
            textposition="outside"
        )

        fig2.update_layout(
            showlegend=False,
            yaxis_title="Total Sales (₹)",
            height=360,
            margin=dict(t=10)
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

    # Payment by city
    if city_available:

        st.markdown(
            '<div class="section-header">'
            'Payment Preference by City'
            '</div>',
            unsafe_allow_html=True
        )

        pay_city = (
            fdf.groupby(
                ["City", "Payment"]
            )["Sales"]
            .sum()
            .reset_index()
        )

        fig3 = px.bar(
            pay_city,
            x="City",
            y="Sales",
            color="Payment",
            barmode="stack",
            color_discrete_sequence=COLORS,
            labels={
                "Sales": "Total Sales (₹)"
            }
        )

        fig3.update_layout(
            height=380,
            margin=dict(t=10)
        )

        st.plotly_chart(
            fig3,
            use_container_width=True
        )

# ═══════════════════════════════════════════════
# TAB 7 – TRENDS
# ═══════════════════════════════════════════════

with tabs[6]:

    st.markdown(
        '<div class="section-header">'
        'Monthly Sales Trend'
        '</div>',
        unsafe_allow_html=True
    )

    monthly = (
        fdf.groupby("Month_dt")
        .agg(
            Total_Sales=("Sales", "sum"),
            Transactions=("Sales", "size")
        )
        .reset_index()
        .sort_values("Month_dt")
    )

    monthly["Month_str"] = (
        monthly["Month_dt"]
        .dt.strftime("%b %Y")
    )

    fig = make_subplots(
        specs=[
            [{"secondary_y": True}]
        ]
    )

    fig.add_trace(
        go.Bar(
            x=monthly["Month_str"],
            y=monthly["Total_Sales"],
            name="Total Sales (₹)",
            marker_color="#3b82d4",
            text=monthly["Total_Sales"],
            texttemplate="₹%{text:,.0f}",
            textposition="outside"
        ),
        secondary_y=False
    )

    fig.add_trace(
        go.Scatter(
            x=monthly["Month_str"],
            y=monthly["Transactions"],
            name="Transactions",
            mode="lines+markers",
            line=dict(
                color="#7c5cd8",
                width=2
            ),
            marker=dict(size=6)
        ),
        secondary_y=True
    )

    fig.update_yaxes(
        title_text="Total Sales (₹)",
        secondary_y=False
    )

    fig.update_yaxes(
        title_text="# Transactions",
        secondary_y=True
    )

    fig.update_layout(
        height=400,
        legend=dict(
            orientation="h",
            y=1.1
        ),
        margin=dict(t=30)
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    col_a, col_b = st.columns(2)

    # Day of week
    with col_a:

        st.markdown(
            '<div class="section-header">'
            'Sales by Day of Week'
            '</div>',
            unsafe_allow_html=True
        )

        dow = fdf.copy()

        dow["DayOfWeek"] = (
            dow["Date"]
            .dt.day_name()
        )

        order = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday"
        ]

        dow_agg = (
            dow.groupby("DayOfWeek")["Sales"]
            .sum()
            .reindex(order)
            .reset_index()
        )

        fig2 = px.bar(
            dow_agg,
            x="DayOfWeek",
            y="Sales",
            color="DayOfWeek",
            color_discrete_sequence=COLORS,
            text="Sales"
        )

        fig2.update_traces(
            texttemplate="₹%{text:,.0f}",
            textposition="outside"
        )

        fig2.update_layout(
            showlegend=False,
            height=340,
            yaxis_title="Total Sales (₹)",
            margin=dict(t=10)
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

    # Monthly average
    with col_b:

        st.markdown(
            '<div class="section-header">'
            'Monthly Avg Transaction Value'
            '</div>',
            unsafe_allow_html=True
        )

        monthly_avg = (
            fdf.groupby("Month_dt")["Sales"]
            .mean()
            .reset_index()
            .sort_values("Month_dt")
        )

        monthly_avg["Month_str"] = (
            monthly_avg["Month_dt"]
            .dt.strftime("%b %Y")
        )

        fig3 = px.line(
            monthly_avg,
            x="Month_str",
            y="Sales",
            markers=True,
            color_discrete_sequence=["#3b82d4"],
            labels={
                "Sales":
                    "Avg Transaction (₹)",
                "Month_str":
                    ""
            }
        )

        fig3.update_layout(
            height=340,
            margin=dict(t=10)
        )

        st.plotly_chart(
            fig3,
            use_container_width=True
        )

    # Category over time
    st.markdown(
        '<div class="section-header">'
        'Category Sales Over Time (Monthly)'
        '</div>',
        unsafe_allow_html=True
    )

    cat_monthly = (
        fdf.groupby(
            ["Month_dt", "Category"]
        )["Sales"]
        .sum()
        .reset_index()
        .sort_values("Month_dt")
    )

    cat_monthly["Month_str"] = (
        cat_monthly["Month_dt"]
        .dt.strftime("%b %Y")
    )

    fig4 = px.line(
        cat_monthly,
        x="Month_str",
        y="Sales",
        color="Category",
        markers=True,
        color_discrete_sequence=COLORS,
        labels={
            "Sales":
                "Total Sales (₹)",
            "Month_str":
                ""
        }
    )

    fig4.update_layout(
        height=400,
        margin=dict(t=10),
        legend=dict(
            orientation="h",
            y=1.1
        )
    )

    st.plotly_chart(
        fig4,
        use_container_width=True
    )

# ═══════════════════════════════════════════════
# TAB 8 – BUSINESS DECISIONS
# ═══════════════════════════════════════════════

with tabs[7]:

    st.markdown(
        '<div class="section-header">'
        'Data-Driven Business Insights'
        '</div>',
        unsafe_allow_html=True
    )

    # ─────────────────────────────────────────
    # COMPUTE INSIGHTS
    # ─────────────────────────────────────────

    top_cat = (
        fdf.groupby("Category")["Sales"]
        .sum()
        .idxmax()
    )

    top_city = (
        fdf.groupby("City")["Sales"]
        .sum()
        .idxmax()
        if city_available and not fdf.empty
        else None
    )

    top_prod = (
        fdf.groupby("Product")["Sales"]
        .sum()
        .idxmax()
    )

    top_pay = (
        fdf["Payment"]
        .value_counts()
        .idxmax()
    )

    top_pay_rev = (
        fdf.groupby("Payment")["Sales"]
        .sum()
        .idxmax()
    )

    low_rating = (
        fdf.groupby("Category")["Rating"]
        .mean()
        .idxmin()
    )

    low_rating_v = (
        fdf.groupby("Category")["Rating"]
        .mean()
        .min()
    )

    best_month = (
        fdf.groupby("Month_dt")["Sales"]
        .sum()
        .idxmax()
        .strftime("%B %Y")
    )

    member_df = fdf[
        fdf["Customer Type"] == "Member"
    ]

    normal_df = fdf[
        fdf["Customer Type"] == "Normal"
    ]

    member_avg = (
        member_df["Sales"].mean()
        if not member_df.empty
        else 0
    )

    normal_avg = (
        normal_df["Sales"].mean()
        if not normal_df.empty
        else 0
    )

    top_branch = (
        fdf.groupby("Branch")["Sales"]
        .sum()
        .idxmax()
    )

    low_branch = (
        fdf.groupby("Branch")["Sales"]
        .sum()
        .idxmin()
    )

    # ─────────────────────────────────────────
    # INSIGHTS
    # ─────────────────────────────────────────

    insights = [

        (
            "🏆",
            "Top Revenue Category",
            f"""
            <b>{top_cat}</b> generates the highest total
            revenue. Consider expanding the product line
            in this category and negotiating better supplier
            rates to improve margins.
            """
        ),

        (
            "🏙️",
            "Strongest Market",
            (
                f"""
                <b>{top_city}</b> is the highest-revenue city.
                Prioritise inventory allocation and promotional
                budgets here. Consider opening an additional
                branch if space permits.
                """
                if top_city is not None
                else
                """
                City-level revenue analysis is unavailable
                because the source data has no City column.
                """
            )
        ),

        (
            "🥇",
            "Star Product",
            f"""
            <b>{top_prod}</b> is the single best-selling
            product. Ensure it is always in stock, feature
            it prominently, and consider bundling it with
            slower-moving SKUs.
            """
        ),

        (
            "💳",
            "Payment Preference",
            f"""
            <b>{top_pay}</b> is the most-used payment method
            by transaction count, while
            <b>{top_pay_rev}</b> drives the most revenue.
            Offer cashback or loyalty points on both to
            encourage repeat purchases.
            """
        ),

        (
            "⭐",
            "Low-Rated Category",
            f"""
            <b>{low_rating}</b> has the lowest average
            customer rating ({low_rating_v:.2f}/5).
            Investigate product quality, pricing, or
            freshness. Consider reviewing underperforming
            SKUs in this category.
            """
        ),

        (
            "📅",
            "Peak Month",
            f"""
            <b>{best_month}</b> recorded the highest monthly
            sales. Plan promotional campaigns and extra
            staffing 2–3 weeks before peak months to
            maximise throughput.
            """
        ),

        (
            "👤",
            "Member vs Normal Customer",
            f"""
            Member customers spend
            <b>₹{member_avg:,.2f}</b> on average per
            transaction vs
            <b>₹{normal_avg:,.2f}</b> for Normal customers.
            """
            + (
                " Members spend more — scale the loyalty programme."
                if member_avg > normal_avg
                else
                " Normal customers spend more — convert them to members with a sign-up incentive."
            )
        ),

        (
            "🌿",
            "Branch Optimisation",
            f"""
            Branch <b>{top_branch}</b> leads in revenue.
            Branch <b>{low_branch}</b> is the weakest —
            conduct a root-cause analysis involving staffing,
            location, and product mix.
            """
        ),

        (
            "📦",
            "Quantity vs Price Opportunity",
            """
            Products with high unit prices but low quantities
            sold may respond well to bundle deals. Products
            with low prices but high quantities can be targeted
            with upsell strategies.
            """
        ),

        (
            "📢",
            "Gender-Targeted Marketing",
            """
            Review the Gender breakdown in the Customer
            Insights tab. If one gender significantly
            outspends the other in a category, design
            targeted campaigns for the underperforming
            demographic.
            """
        ),
    ]

    # ─────────────────────────────────────────
    # DISPLAY INSIGHTS
    # ─────────────────────────────────────────

    for icon, title, body in insights:

        st.markdown(
            f"""
            <div class="insight-box">
                <b>{icon} {title}</b><br>
                {body}
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")

    # ─────────────────────────────────────────
    # PRIORITY ACTION MATRIX
    # ─────────────────────────────────────────

    st.markdown(
        '<div class="section-header">'
        'Priority Action Matrix'
        '</div>',
        unsafe_allow_html=True
    )

    top_city_action = (
        f"Invest in {top_city} branch expansion"
        if top_city is not None
        else
        "Improve city-level data collection"
    )

    actions = pd.DataFrame(
        {
            "Priority": [
                "🔴 High",
                "🔴 High",
                "🟠 Medium",
                "🟠 Medium",
                "🟡 Low",
            ],

            "Action": [
                f"Scale up {top_cat} product range",
                top_city_action,
                f"Quality improvement in {low_rating} category",
                "Convert Normal customers to Members",
                "Introduce bundled deals on high-price / low-qty products",
            ],

            "Expected Impact": [
                "Revenue growth +10–15%",
                "New market share in top city",
                "Rating improvement → repeat visits",
                "Higher avg basket size",
                "Increased units per transaction",
            ],

            "Timeframe": [
                "Q3 2026",
                "Q4 2026",
                "Q2 2026",
                "Q2 2026",
                "Q3 2026",
            ],
        }
    )

    st.dataframe(
        actions,
        use_container_width=True,
        hide_index=True
    )

# ═══════════════════════════════════════════════
# TAB 9 – RAW DATA
# ═══════════════════════════════════════════════

with tabs[8]:

    st.markdown(
        '<div class="section-header">'
        'Filtered Dataset'
        '</div>',
        unsafe_allow_html=True
    )

    display_cols = [
        "Date",
        "Branch",
        "Customer Type",
        "Gender",
        "Product",
        "Category",
        "Quantity",
        "Unit Price",
        "Payment",
        "Rating",
        "Sales",
    ]

    if "Invoice ID" in df.columns:

        display_cols.insert(
            0,
            "Invoice ID"
        )

    if city_available:

        display_cols.insert(
            3,
            "City"
        )

    view_df = fdf[
        display_cols
    ].copy()

    # Format date
    view_df["Date"] = (
        view_df["Date"]
        .dt.strftime("%Y-%m-%d")
    )

    # Format money
    view_df["Unit Price"] = (
        view_df["Unit Price"]
        .map("₹{:.2f}".format)
    )

    view_df["Sales"] = (
        view_df["Sales"]
        .map("₹{:.2f}".format)
    )

    # Search
    search = st.text_input(
        "🔎 Search "
        "(Invoice ID / Product / City / Category)"
    ).strip().lower()

    if search:

        mask_s = view_df.apply(
            lambda r:
                r.astype(str)
                .str.lower()
                .str.contains(
                    search,
                    regex=False
                )
                .any(),
            axis=1
        )

        view_df = view_df[
            mask_s
        ]

    st.caption(
        f"Displaying **{len(view_df):,}** rows"
    )

    st.dataframe(
        view_df.reset_index(drop=True),
        use_container_width=True,
        height=500
    )

    # Download
    csv_bytes = (
        fdf[display_cols]
        .to_csv(index=False)
        .encode("utf-8")
    )

    st.download_button(
        label="⬇️ Download filtered data as CSV",
        data=csv_bytes,
        file_name="supermarket_sales_filtered.csv",
        mime="text/csv",
    )