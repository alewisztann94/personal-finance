"""
Personal Finance Dashboard
Streamlit app for visualizing spending and savings metrics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sqlite3

# Import analysis module (using importlib to handle numeric prefix in filename)
import importlib.util
spec = importlib.util.spec_from_file_location("analyze", Path(__file__).parent / "scripts" / "06_analyze.py")
analyze = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analyze)

# Page config
st.set_page_config(
    page_title="Personal Finance Dashboard",
    page_icon="💰",
    layout="wide"
)

# Sidebar for data selection
st.sidebar.title("Settings")
data_dir = st.sidebar.selectbox(
    "Data Source",
    ["synthetic", "real"],
    help="Select which dataset to analyze"
)

# Check if database exists
db_file = Path(f"data/{data_dir}_finance.db")
if not db_file.exists():
    st.error(f"Database not found: {db_file}")
    st.info("Run the pipeline first: `python scripts/run_pipeline.py`")
    st.stop()

# Get database connection
conn = analyze.get_connection(data_dir)

# Title
st.title("Personal Finance Dashboard")
st.caption(f"Analyzing {data_dir} data")

# Overview metrics
st.header("Overview")

trends_df = analyze.month_over_month_trends(conn)
if not trends_df.empty:
    latest = trends_df.iloc[0]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Latest Month Expenses",
            f"${latest['total_expenses']:,.2f}",
            f"{latest['expense_change_pct']:+.1f}%" if pd.notna(latest['expense_change_pct']) else None
        )

    with col2:
        st.metric(
            "Latest Month Income",
            f"${latest['total_income']:,.2f}"
        )

    with col3:
        st.metric(
            "Net Savings",
            f"${latest['net_savings']:,.2f}"
        )

    savings_df = analyze.savings_rate(conn)
    if not savings_df.empty:
        avg_rate = savings_df['savings_rate_pct'].mean()
        with col4:
            st.metric(
                "Avg Savings Rate",
                f"{avg_rate:.1f}%"
            )

# Monthly spending trends
st.header("Monthly Spending Trends")

col1, col2 = st.columns(2)

with col1:
    # Line chart of expenses vs income over time
    if not trends_df.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trends_df['month'],
            y=trends_df['total_expenses'],
            name='Expenses',
            line=dict(color='red')
        ))
        fig.add_trace(go.Scatter(
            x=trends_df['month'],
            y=trends_df['total_income'],
            name='Income',
            line=dict(color='green')
        ))
        fig.update_layout(
            title="Income vs Expenses Over Time",
            xaxis_title="Month",
            yaxis_title="Amount ($)",
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)

with col2:
    # Savings rate over time
    if not savings_df.empty:
        fig = px.bar(
            savings_df,
            x='month',
            y='savings_rate_pct',
            title="Savings Rate by Month",
            labels={'savings_rate_pct': 'Savings Rate (%)', 'month': 'Month'},
            color='savings_rate_pct',
            color_continuous_scale=['red', 'yellow', 'green']
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

# Category breakdown
st.header("Spending by Category")

category_df = analyze.monthly_spend_by_category(conn)

col1, col2 = st.columns(2)

with col1:
    # Select month for pie chart
    if not category_df.empty:
        months = category_df['month'].unique()
        selected_month = st.selectbox("Select Month", months)

        month_data = category_df[category_df['month'] == selected_month]

        fig = px.pie(
            month_data,
            values='category_total',
            names='category',
            title=f"Spending Breakdown - {selected_month}",
            hole=0.4
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

with col2:
    # Category totals over time (stacked bar)
    if not category_df.empty:
        # Pivot for stacked bar
        pivot_df = category_df.pivot(index='month', columns='category', values='category_total').fillna(0)
        pivot_df = pivot_df.abs()  # Make positive for visualization

        fig = px.bar(
            pivot_df.reset_index(),
            x='month',
            y=pivot_df.columns.tolist(),
            title="Category Spending Over Time",
            labels={'value': 'Amount ($)', 'month': 'Month'},
            barmode='stack'
        )
        st.plotly_chart(fig, use_container_width=True)

# Top merchants
st.header("Top Merchants by Category")

merchants_df = analyze.top_merchants_by_category(conn, limit=5)

if not merchants_df.empty:
    # Select category
    categories = merchants_df['category'].unique()
    selected_category = st.selectbox("Select Category", categories)

    cat_merchants = merchants_df[merchants_df['category'] == selected_category]

    fig = px.bar(
        cat_merchants,
        x='total_amount',
        y='merchant',
        orientation='h',
        title=f"Top Merchants - {selected_category}",
        labels={'total_amount': 'Total Spent ($)', 'merchant': 'Merchant'},
        text='transaction_count'
    )
    fig.update_traces(texttemplate='%{text}x', textposition='outside')
    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig, use_container_width=True)

# Category summary table
st.header("Category Summary")

summary_df = analyze.category_summary(conn)
if not summary_df.empty:
    # Format for display
    display_df = summary_df.copy()
    display_df['total_amount'] = display_df['total_amount'].apply(lambda x: f"${x:,.2f}")
    display_df['avg_amount'] = display_df['avg_amount'].apply(lambda x: f"${x:,.2f}")
    display_df['min_amount'] = display_df['min_amount'].apply(lambda x: f"${x:,.2f}")
    display_df['max_amount'] = display_df['max_amount'].apply(lambda x: f"${x:,.2f}")

    display_df.columns = ['Category', 'Count', 'Total', 'Average', 'Min', 'Max']
    st.dataframe(display_df, use_container_width=True, hide_index=True)

# Raw data explorer
with st.expander("Raw Data Explorer"):
    query = st.text_area(
        "Custom SQL Query",
        value="SELECT * FROM transactions LIMIT 10",
        help="Write your own SQL to explore the data"
    )
    if st.button("Run Query"):
        try:
            result = pd.read_sql_query(query, conn)
            st.dataframe(result, use_container_width=True)
        except Exception as e:
            st.error(f"Query error: {e}")

# Close connection
conn.close()

# Footer
st.markdown("---")
st.caption("Built with Streamlit | Data processed with Python & SQLite")
