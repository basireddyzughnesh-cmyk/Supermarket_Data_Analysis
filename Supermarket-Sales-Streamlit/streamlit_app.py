"""Interactive Streamlit dashboard for supermarket sales."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from sales_dashboard.data import WORKBOOK_PATH, get_data_quality, load_sales_data

st.set_page_config(
    page_title="Supermarket sales",
    page_icon=":material/storefront:",
    layout="wide",
)

MONEY_FORMAT = "₹{:,.0f}"


@st.cache_data(show_spinner="Loading and cleaning sales data...")
def load_data(workbook_path: str) -> pd.DataFrame:
    return load_sales_data(workbook_path)


st.title("Supermarket sales")
st.caption("Explore revenue, product performance, customers, and transaction quality.")

try:
    sales = load_data(str(WORKBOOK_PATH))
except (FileNotFoundError, ValueError, OSError, KeyError) as error:
    st.error(f"Unable to load the sales workbook: {error}")
    st.stop()

if sales.empty:
    st.error("The sales workbook contains no transactions.")
    st.stop()

valid_dates = sales["Date"].dropna()
if valid_dates.empty:
    st.error("The sales workbook contains no valid transaction dates.")
    st.stop()

date_min = valid_dates.min().date()
date_max = valid_dates.max().date()

with st.sidebar:
    st.header("Filters")
    selected_dates = st.date_input(
        "Transaction dates",
        value=(date_min, date_max),
        min_value=date_min,
        max_value=date_max,
    )

    filters: dict[str, list[str]] = {}
    for column, label in (
        ("City", "City"),
        ("Branch", "Branch"),
        ("Category", "Category"),
        ("Customer Type", "Customer type"),
        ("Gender", "Gender"),
        ("Payment", "Payment method"),
    ):
        options = sorted(sales[column].dropna().astype(str).unique().tolist())
        filters[column] = st.multiselect(label, options, default=options)

filtered = sales.copy()
if len(selected_dates) == 2:
    start_date, end_date = selected_dates
    filtered = filtered.loc[
        filtered["Date"].dt.date.between(start_date, end_date)
    ]

for column, selected_values in filters.items():
    filtered = filtered.loc[filtered[column].astype(str).isin(selected_values)]

if filtered.empty:
    st.info("No transactions match these filters. Adjust the selections in the sidebar.")
    st.stop()

total_revenue = filtered["Sales"].sum()
transaction_count = len(filtered)
average_transaction = filtered["Sales"].mean()
units_sold = filtered["Quantity"].sum()

st.caption(
    f"Showing **{transaction_count:,}** of **{len(sales):,}** transactions "
    f"from **{start_date:%b %d, %Y}** to **{end_date:%b %d, %Y}**."
    if len(selected_dates) == 2
    else f"Showing **{transaction_count:,}** of **{len(sales):,}** transactions."
)

with st.container(horizontal=True):
    st.metric("Revenue", MONEY_FORMAT.format(total_revenue), border=True)
    st.metric("Transactions", f"{transaction_count:,}", border=True)
    st.metric(
        "Average transaction",
        f"₹{average_transaction:,.2f}",
        border=True,
    )
    st.metric("Units sold", f"{units_sold:,.0f}", border=True)

monthly_sales = (
    filtered.groupby("Month", as_index=False)
    .agg(Sales=("Sales", "sum"))
    .sort_values("Month")
)
category_sales = (
    filtered.groupby("Category", as_index=False)
    .agg(Sales=("Sales", "sum"))
    .sort_values("Sales", ascending=False)
)
branch_sales = (
    filtered.groupby(["City", "Branch"], as_index=False)
    .agg(Sales=("Sales", "sum"))
    .sort_values("Sales", ascending=False)
)
product_sales = (
    filtered.groupby("Product", as_index=False)
    .agg(Sales=("Sales", "sum"), Units=("Quantity", "sum"))
    .sort_values("Sales", ascending=False)
    .head(10)
)

st.subheader("Sales performance")
chart_left, chart_right = st.columns(2)

with chart_left:
    with st.container(border=True):
        st.markdown("**Monthly revenue**")
        monthly_figure = px.area(
            monthly_sales,
            x="Month",
            y="Sales",
            markers=True,
            labels={"Month": "Month", "Sales": "Revenue"},
        )
        monthly_figure.update_traces(
            line_color="#0f766e",
            fillcolor="rgba(15, 118, 110, 0.14)",
            hovertemplate="%{x|%b %Y}<br>₹%{y:,.2f}<extra></extra>",
        )
        monthly_figure.update_layout(
            height=340,
            margin=dict(l=10, r=10, t=10, b=10),
            yaxis=dict(tickprefix="₹", tickformat=",.0f", title=None),
            xaxis_title=None,
        )
        st.plotly_chart(monthly_figure, width="stretch")

with chart_right:
    with st.container(border=True):
        st.markdown("**Revenue by category**")
        category_figure = px.bar(
            category_sales,
            x="Sales",
            y="Category",
            orientation="h",
            color="Sales",
            color_continuous_scale=["#99f6e4", "#0f766e"],
            labels={"Sales": "Revenue", "Category": ""},
        )
        category_figure.update_layout(
            height=340,
            margin=dict(l=10, r=10, t=10, b=10),
            coloraxis_showscale=False,
            xaxis=dict(tickprefix="₹", tickformat=",.0f", title=None),
            yaxis={"categoryorder": "total ascending"},
        )
        st.plotly_chart(category_figure, width="stretch")

detail_left, detail_right = st.columns(2)

with detail_left:
    with st.container(border=True):
        st.markdown("**City and branch performance**")
        branch_figure = px.bar(
            branch_sales,
            x="City",
            y="Sales",
            color="Branch",
            barmode="group",
            labels={"City": "", "Sales": "Revenue", "Branch": "Branch"},
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        branch_figure.update_layout(
            height=340,
            margin=dict(l=10, r=10, t=10, b=10),
            yaxis=dict(tickprefix="₹", tickformat=",.0f", title=None),
            legend_title_text="Branch",
        )
        st.plotly_chart(branch_figure, width="stretch")

with detail_right:
    with st.container(border=True):
        st.markdown("**Top 10 products by revenue**")
        product_figure = px.bar(
            product_sales.sort_values("Sales"),
            x="Sales",
            y="Product",
            orientation="h",
            labels={"Product": "", "Sales": "Revenue"},
            color_discrete_sequence=["#0f766e"],
            hover_data={"Units": ":,.0f", "Sales": ":,.2f"},
        )
        product_figure.update_layout(
            height=340,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(tickprefix="₹", tickformat=",.0f", title=None),
        )
        st.plotly_chart(product_figure, width="stretch")

top_category = category_sales.iloc[0]["Category"]
top_product = product_sales.iloc[0]["Product"]
top_city = branch_sales.groupby("City")["Sales"].sum().idxmax()
st.subheader("Highlights")
highlight_left, highlight_middle, highlight_right = st.columns(3)
highlight_left.info(f"**Top category:** {top_category}")
highlight_middle.info(f"**Top product:** {top_product}")
highlight_right.info(f"**Top city:** {top_city}")

overview_tab, transactions_tab, quality_tab = st.tabs(
    ["Overview", "Transactions", "Data quality"]
)

with overview_tab:
    st.caption(
        "All charts and highlights update when you change the sidebar filters."
    )

with transactions_tab:
    st.subheader("Filtered transactions")
    visible_columns = [
        "Invoice ID",
        "Date",
        "City",
        "Branch",
        "Category",
        "Product",
        "Quantity",
        "Unit Price",
        "Payment",
        "Rating",
        "Sales",
    ]
    st.dataframe(
        filtered[visible_columns].sort_values("Date", ascending=False),
        hide_index=True,
        column_config={
            "Date": st.column_config.DateColumn("Date", format="MMM D, YYYY"),
            "Unit Price": st.column_config.NumberColumn("Unit price", format="₹%.2f"),
            "Sales": st.column_config.NumberColumn("Sales", format="₹%.2f"),
            "Rating": st.column_config.NumberColumn("Rating", format="%.1f / 5"),
        },
    )
    csv_data = filtered[visible_columns].to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered transactions",
        data=csv_data,
        file_name="filtered_supermarket_sales.csv",
        mime="text/csv",
        icon=":material/download:",
    )

with quality_tab:
    st.subheader("Workbook quality checks")
    quality = get_data_quality(sales)
    metric_left, metric_middle, metric_right = st.columns(3)
    metric_left.metric("Transactions loaded", f"{quality['rows']:,}")
    metric_middle.metric("Duplicate invoice rows", f"{quality['duplicate_invoices']:,}")
    metric_right.metric("Original sales mismatches", f"{quality['sales_mismatches']:,}")

    if quality["sales_mismatches"]:
        st.warning(
            "Some original sales amounts differ from quantity × unit price. "
            "The dashboard uses the recalculated amounts."
        )
    else:
        st.success("Every original sales amount matches quantity × unit price.")

    st.caption(f"Missing values: {quality['missing_values']:,}")

    mismatch_rows = sales.loc[
        (sales["Sales_Original"] - sales["Quantity"] * sales["Unit Price"]).abs()
        > 0.05,
        [
            "Invoice ID",
            "Quantity",
            "Unit Price",
            "Sales_Original",
            "Sales",
        ],
    ]
    if not mismatch_rows.empty:
        st.dataframe(mismatch_rows, hide_index=True)
