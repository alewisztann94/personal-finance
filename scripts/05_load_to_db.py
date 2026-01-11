"""
Database Loading Script
Loads categorized transaction data into SQLite database for analysis
"""

import pandas as pd
import sqlite3
from pathlib import Path
import sys


def load_to_database(data_dir="synthetic"):
    """
    Load categorized transactions into SQLite database

    Args:
        data_dir: Either "real" or "synthetic" (default: "synthetic" for safety)

    Returns:
        True on success, None on failure
    """
    try:
        # Define file paths
        input_file = Path(f"data/processed/{data_dir}/all_transactions_categorized.csv")
        db_file = Path(f"data/{data_dir}_finance.db")

        # Create data directory if needed
        db_file.parent.mkdir(parents=True, exist_ok=True)

        print(f"Processing {data_dir.upper()} data")
        print(f"Loading data from {input_file}...")

        # Load CSV data
        if not input_file.exists():
            print(f"Error: Input file not found: {input_file}")
            return None

        df = pd.read_csv(input_file)
        df['date'] = pd.to_datetime(df['date'])
        csv_row_count = len(df)
        csv_amount_total = df['amount'].sum()

        print(f"Loaded {csv_row_count} rows from CSV")

        # Connect to SQLite database
        print(f"\nConnecting to database: {db_file}")
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Drop table if exists for clean reruns
        cursor.execute("DROP TABLE IF EXISTS transactions")

        # Create transactions table with explicit schema
        cursor.execute("""
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                transaction_type TEXT NOT NULL,
                source TEXT NOT NULL,
                category TEXT
            )
        """)

        # Note: Indexes omitted - table is small enough (~500 rows) that full scans
        # are faster than index lookups. Add indexes if dataset grows to 10k+ rows.

        print("Created transactions table")

        # Load data using pandas to_sql
        df.to_sql('transactions', conn, if_exists='append', index=False)

        conn.commit()

        # Validation checks
        print("\n" + "="*60)
        print("VALIDATION CHECKS")
        print("="*60)

        # Row count validation
        cursor.execute("SELECT COUNT(*) FROM transactions")
        db_row_count = cursor.fetchone()[0]

        if db_row_count == csv_row_count:
            print(f"\nRow count: {db_row_count} rows ✓")
        else:
            print(f"\nRow count MISMATCH: CSV={csv_row_count}, DB={db_row_count} ✗")
            conn.close()
            return None

        # Amount total validation
        cursor.execute("SELECT SUM(amount) FROM transactions")
        db_amount_total = cursor.fetchone()[0]

        # Use approximate comparison for floating point
        if abs(db_amount_total - csv_amount_total) < 0.01:
            print(f"Amount totals match: ${db_amount_total:,.2f} ✓")
        else:
            print(f"Amount totals MISMATCH: CSV=${csv_amount_total:,.2f}, DB=${db_amount_total:,.2f} ✗")
            conn.close()
            return None

        # Sample category breakdown
        print("\n" + "-"*60)
        print("CATEGORY BREAKDOWN")
        print("-"*60)

        cursor.execute("""
            SELECT
                category,
                COUNT(*) as transaction_count,
                SUM(amount) as total_amount
            FROM transactions
            GROUP BY category
            ORDER BY total_amount ASC
        """)

        for row in cursor.fetchall():
            category, count, total = row
            print(f"  {category:<25} {count:>4} transactions  ${total:>12,.2f}")

        # Date range check
        cursor.execute("SELECT MIN(date), MAX(date) FROM transactions")
        min_date, max_date = cursor.fetchone()
        print(f"\nDate range: {min_date} to {max_date}")

        conn.close()

        print("\n" + "="*60)
        print(f"Database saved to: {db_file}")
        print("Database loading completed successfully!")
        print("="*60)

        return True

    except pd.errors.ParserError as e:
        print(f"Error parsing CSV file: {e}")
        return None

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return None

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Get data_dir from command line argument, default to "synthetic"
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "synthetic"
    if data_dir not in ["real", "synthetic"]:
        print(f"Error: data_dir must be 'real' or 'synthetic', got '{data_dir}'")
        sys.exit(1)
    result = load_to_database(data_dir)
    sys.exit(0 if result else 1)
