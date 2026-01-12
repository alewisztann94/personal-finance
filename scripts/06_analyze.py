"""
Transaction Analysis Script
SQL queries for financial analysis and insights
"""

import sqlite3
import pandas as pd
from pathlib import Path
import sys


def get_connection(data_dir="synthetic"):
    """Get database connection"""
    db_file = Path(f"data/{data_dir}_finance.db")
    if not db_file.exists():
        print(f"Error: Database not found: {db_file}")
        print("Run the pipeline first: python scripts/run_pipeline.py")
        return None
    return sqlite3.connect(db_file)


def monthly_spend_by_category(conn):
    """
    Get monthly spend by category with percentage breakdown
    Excludes transfers and income for expense analysis
    """
    query = """
    WITH monthly_category AS (
        SELECT
            strftime('%Y-%m', date) as month,
            category,
            SUM(amount) as category_total
        FROM transactions
        WHERE transaction_type = 'expense'
          AND category NOT IN ('Transfer', 'Income')
        GROUP BY 1, 2
    ),
    monthly_totals AS (
        SELECT
            strftime('%Y-%m', date) as month,
            SUM(amount) as month_total
        FROM transactions
        WHERE transaction_type = 'expense'
          AND category NOT IN ('Transfer', 'Income')
        GROUP BY 1
    )
    SELECT
        mc.month,
        mc.category,
        mc.category_total,
        mt.month_total,
        ROUND(mc.category_total / mt.month_total * 100, 1) as pct_of_monthly_spend
    FROM monthly_category mc
    JOIN monthly_totals mt ON mc.month = mt.month
    ORDER BY mc.month DESC, mc.category_total ASC
    """
    return pd.read_sql_query(query, conn)


def month_over_month_trends(conn):
    """
    Get month-over-month spending trends with percentage change
    Uses LAG to compare to previous month
    """
    query = """
    WITH monthly_totals AS (
        SELECT
            strftime('%Y-%m', date) as month,
            SUM(CASE WHEN transaction_type = 'expense' AND category NOT IN ('Transfer')
                THEN ABS(amount) ELSE 0 END) as total_expenses,
            SUM(CASE WHEN transaction_type = 'income' AND category NOT IN ('Transfer')
                THEN amount ELSE 0 END) as total_income
        FROM transactions
        GROUP BY 1
    ),
    with_lag AS (
        SELECT
            month,
            total_expenses,
            total_income,
            LAG(total_expenses) OVER (ORDER BY month) as prev_month_expenses,
            LAG(total_income) OVER (ORDER BY month) as prev_month_income
        FROM monthly_totals
    )
    SELECT
        month,
        total_expenses,
        total_income,
        prev_month_expenses,
        CASE
            WHEN prev_month_expenses > 0
            THEN ROUND((total_expenses - prev_month_expenses) / prev_month_expenses * 100, 1)
            ELSE NULL
        END as expense_change_pct,
        total_income - total_expenses as net_savings
    FROM with_lag
    ORDER BY month DESC
    """
    return pd.read_sql_query(query, conn)


def savings_rate(conn):
    """
    Calculate savings rate: (income - expenses) / income * 100
    Monthly and overall average
    """
    query = """
    WITH monthly_summary AS (
        SELECT
            strftime('%Y-%m', date) as month,
            SUM(CASE WHEN transaction_type = 'income' AND category NOT IN ('Transfer')
                THEN amount ELSE 0 END) as income,
            SUM(CASE WHEN transaction_type = 'expense' AND category NOT IN ('Transfer')
                THEN ABS(amount) ELSE 0 END) as expenses
        FROM transactions
        GROUP BY 1
    )
    SELECT
        month,
        income,
        expenses,
        income - expenses as savings,
        CASE
            WHEN income > 0
            THEN ROUND((income - expenses) / income * 100, 1)
            ELSE NULL
        END as savings_rate_pct
    FROM monthly_summary
    WHERE income > 0
    ORDER BY month DESC
    """
    return pd.read_sql_query(query, conn)


def top_merchants_by_category(conn, limit=5):
    """
    Get top merchants (by total spend) within each category
    """
    query = f"""
    WITH ranked_merchants AS (
        SELECT
            category,
            description as merchant,
            COUNT(*) as transaction_count,
            SUM(amount) as total_amount,
            ROW_NUMBER() OVER (PARTITION BY category ORDER BY SUM(amount) ASC) as rank
        FROM transactions
        WHERE transaction_type = 'expense'
          AND category NOT IN ('Transfer', 'Income', 'Uncategorized')
        GROUP BY category, description
    )
    SELECT
        category,
        merchant,
        transaction_count,
        total_amount
    FROM ranked_merchants
    WHERE rank <= {limit}
    ORDER BY category, total_amount ASC
    """
    return pd.read_sql_query(query, conn)


def category_summary(conn):
    """
    Overall category summary across all time
    Min/max ranked by absolute value (largest magnitude transactions)
    """
    query = """
    WITH ranked AS (
        SELECT
            category,
            amount,
            ROW_NUMBER() OVER (PARTITION BY category ORDER BY ABS(amount) ASC) as min_rank,
            ROW_NUMBER() OVER (PARTITION BY category ORDER BY ABS(amount) DESC) as max_rank
        FROM transactions
        WHERE category NOT IN ('Transfer')
    )
    SELECT
        t.category,
        COUNT(*) as transaction_count,
        SUM(t.amount) as total_amount,
        AVG(t.amount) as avg_amount,
        (SELECT amount FROM ranked r WHERE r.category = t.category AND r.min_rank = 1) as min_amount,
        (SELECT amount FROM ranked r WHERE r.category = t.category AND r.max_rank = 1) as max_amount
    FROM transactions t
    WHERE t.category NOT IN ('Transfer')
    GROUP BY t.category
    ORDER BY total_amount ASC
    """
    return pd.read_sql_query(query, conn)


def run_analysis(data_dir="synthetic"):
    """
    Run all analysis queries and print results
    """
    conn = get_connection(data_dir)
    if conn is None:
        return None

    print("=" * 70)
    print(f"FINANCIAL ANALYSIS - {data_dir.upper()} DATA")
    print("=" * 70)

    # 1. Monthly spend by category
    print("\n" + "-" * 70)
    print("MONTHLY SPEND BY CATEGORY (% breakdown)")
    print("-" * 70)
    df = monthly_spend_by_category(conn)
    if not df.empty:
        for month in df['month'].unique()[:3]:  # Show last 3 months
            print(f"\n{month}:")
            month_data = df[df['month'] == month]
            for _, row in month_data.iterrows():
                print(f"  {row['category']:<20} ${row['category_total']:>10,.2f}  ({row['pct_of_monthly_spend']:>5.1f}%)")

    # 2. Month-over-month trends
    print("\n" + "-" * 70)
    print("MONTH-OVER-MONTH TRENDS")
    print("-" * 70)
    df = month_over_month_trends(conn)
    if not df.empty:
        print(f"\n{'Month':<10} {'Expenses':>12} {'Income':>12} {'Change %':>10} {'Net Savings':>12}")
        print("-" * 58)
        for _, row in df.head(6).iterrows():
            change = f"{row['expense_change_pct']:+.1f}%" if pd.notna(row['expense_change_pct']) else "N/A"
            print(f"{row['month']:<10} ${row['total_expenses']:>10,.2f} ${row['total_income']:>10,.2f} {change:>10} ${row['net_savings']:>10,.2f}")

    # 3. Savings rate
    print("\n" + "-" * 70)
    print("SAVINGS RATE")
    print("-" * 70)
    df = savings_rate(conn)
    if not df.empty:
        avg_savings_rate = df['savings_rate_pct'].mean()
        print(f"\nAverage savings rate: {avg_savings_rate:.1f}%")
        print(f"\n{'Month':<10} {'Income':>12} {'Expenses':>12} {'Savings':>12} {'Rate':>8}")
        print("-" * 56)
        for _, row in df.head(6).iterrows():
            rate = f"{row['savings_rate_pct']:.1f}%" if pd.notna(row['savings_rate_pct']) else "N/A"
            print(f"{row['month']:<10} ${row['income']:>10,.2f} ${row['expenses']:>10,.2f} ${row['savings']:>10,.2f} {rate:>8}")

    # 4. Top merchants by category
    print("\n" + "-" * 70)
    print("TOP MERCHANTS BY CATEGORY")
    print("-" * 70)
    df = top_merchants_by_category(conn, limit=3)
    if not df.empty:
        current_category = None
        for _, row in df.iterrows():
            if row['category'] != current_category:
                current_category = row['category']
                print(f"\n{current_category}:")
            print(f"  {row['merchant'][:35]:<35} {row['transaction_count']:>3}x  ${row['total_amount']:>10,.2f}")

    # 5. Category summary
    print("\n" + "-" * 70)
    print("CATEGORY SUMMARY (ALL TIME)")
    print("-" * 70)
    df = category_summary(conn)
    if not df.empty:
        print(f"\n{'Category':<20} {'Count':>6} {'Total':>14} {'Avg':>10}")
        print("-" * 52)
        for _, row in df.iterrows():
            print(f"{row['category']:<20} {row['transaction_count']:>6} ${row['total_amount']:>12,.2f} ${row['avg_amount']:>8,.2f}")

    conn.close()

    print("\n" + "=" * 70)
    print("Analysis complete!")
    print("=" * 70)

    return True


if __name__ == "__main__":
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "synthetic"
    if data_dir not in ["real", "synthetic"]:
        print(f"Error: data_dir must be 'real' or 'synthetic', got '{data_dir}'")
        sys.exit(1)
    result = run_analysis(data_dir)
    sys.exit(0 if result else 1)
