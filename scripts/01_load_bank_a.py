"""
Bank_A Transaction Data Processing Script
Loads raw Bank_A CSV data, cleans it, and saves to processed folder
"""

import pandas as pd
from pathlib import Path
import glob
import sys

def load_and_process_bank_a(data_dir="synthetic"):
    """
    Load and process Bank_A transaction data

    Args:
        data_dir: Either "real" or "synthetic" (default: "synthetic" for safety)
    """
    try:
        # Define file paths based on data_dir
        input_pattern = f"data/raw/{data_dir}/Bank_A*.csv"
        output_file = Path(f"data/processed/{data_dir}/bank_a_clean.csv")

        # Create output directory if it doesn't exist
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Find all Bank_A CSV files
        bank_a_files = glob.glob(input_pattern)

        if not bank_a_files:
            print(f"Error: No CSV files found matching pattern '{input_pattern}'")
            return None

        print(f"Processing {data_dir.upper()} data")
        print(f"Found {len(bank_a_files)} Bank_A file(s):")
        for file in bank_a_files:
            print(f"  - {file}")

        # Load all Bank_A CSV files
        all_data = []
        for file in bank_a_files:
            print(f"\nLoading data from {file}...")
            df = pd.read_csv(
                file,
                header=None,
                names=["date", "amount", "description"]
            )
            all_data.append(df)
            print(f"  Loaded {len(df)} rows")

        # Combine all data
        bank_a_df = pd.concat(all_data, ignore_index=True)
        print(f"\nTotal rows loaded: {len(bank_a_df)}")

        # Parse dates from DD/MM/YYYY format to datetime
        bank_a_df["date"] = pd.to_datetime(bank_a_df["date"], format="%d/%m/%Y")

        # Convert amounts to float (handle commas and quotes)
        bank_a_df["amount"] = bank_a_df["amount"].astype(str).str.replace(',', '').astype(float)

        # Uppercase and trim descriptions
        bank_a_df["description"] = bank_a_df["description"].str.strip().str.upper()

        # Flag positive amounts as 'income', negative as 'expense'
        bank_a_df["transaction_type"] = bank_a_df["amount"].apply(
            lambda x: "income" if x > 0 else "expense"
        )

        # Add source column
        bank_a_df["source"] = "Bank_A"

        # Reorder columns
        bank_a_df = bank_a_df[["date", "amount", "description", "transaction_type", "source"]]

        # Remove duplicates (in case same transaction appears in multiple files)
        original_count = len(bank_a_df)
        bank_a_df = bank_a_df.drop_duplicates(
            subset=["date", "amount", "description"],
            keep="first"
        )
        duplicates_removed = original_count - len(bank_a_df)

        if duplicates_removed > 0:
            print(f"\nRemoved {duplicates_removed} duplicate transactions")

        # Filter to date range: 2024-01-01 to 2025-12-31
        start_date = pd.Timestamp("2024-01-01")
        end_date = pd.Timestamp("2025-12-31")
        before_filter = len(bank_a_df)
        bank_a_df = bank_a_df[(bank_a_df["date"] >= start_date) & (bank_a_df["date"] <= end_date)]
        filtered_out = before_filter - len(bank_a_df)
        if filtered_out > 0:
            print(f"Filtered out {filtered_out} transactions outside 2024-01-01 to 2025-12-31")

        # Save to processed folder
        bank_a_df.to_csv(output_file, index=False)
        print(f"\nData saved to {output_file}")

        # Print summary statistics
        print("\n" + "="*60)
        print("SUMMARY STATISTICS")
        print("="*60)

        # Date range
        date_min = bank_a_df["date"].min()
        date_max = bank_a_df["date"].max()
        print(f"\nDate Range: {date_min.strftime('%d/%m/%Y')} to {date_max.strftime('%d/%m/%Y')}")

        # Transaction counts
        total_transactions = len(bank_a_df)
        income_count = len(bank_a_df[bank_a_df["transaction_type"] == "income"])
        expense_count = len(bank_a_df[bank_a_df["transaction_type"] == "expense"])

        print(f"\nTransaction Counts:")
        print(f"  Total:    {total_transactions:>6}")
        print(f"  Income:   {income_count:>6}")
        print(f"  Expense:  {expense_count:>6}")

        # Totals
        total_income = bank_a_df[bank_a_df["transaction_type"] == "income"]["amount"].sum()
        total_expense = bank_a_df[bank_a_df["transaction_type"] == "expense"]["amount"].sum()
        net_total = bank_a_df["amount"].sum()

        print(f"\nTransaction Totals:")
        print(f"  Total Income:  ${total_income:>12,.2f}")
        print(f"  Total Expense: ${total_expense:>12,.2f}")
        print(f"  Net Total:     ${net_total:>12,.2f}")

        print("\n" + "="*60)
        print("Processing completed successfully!")
        print("="*60)

        return bank_a_df

    except FileNotFoundError:
        print(f"Error: Input files not found.")
        print(f"Please ensure Bank_A CSV files exist in data/raw/{data_dir}/")
        return None

    except pd.errors.ParserError as e:
        print(f"Error parsing CSV file: {e}")
        return None

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

if __name__ == "__main__":
    # Get data_dir from command line argument, default to "synthetic"
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "synthetic"
    if data_dir not in ["real", "synthetic"]:
        print(f"Error: data_dir must be 'real' or 'synthetic', got '{data_dir}'")
        sys.exit(1)
    df = load_and_process_bank_a(data_dir)
