"""
Bank_B Transaction Data Processing Script
Loads raw Bank_B CSV data, cleans it, and saves to processed folder
"""

import pandas as pd
from pathlib import Path
import glob
import sys
import os

def get_data_root():
    return Path(os.environ.get("PF_DATA_ROOT", "data"))

def load_and_process_bank_b(data_dir="synthetic"):
    """
    Load and process Bank_B transaction data

    Args:
        data_dir: Either "real" or "synthetic" (default: "synthetic" for safety)
    """
    try:
        # Define file paths based on data_dir
        data_root = get_data_root()
        input_pattern = str(data_root / "raw" / data_dir / "bank_b*.csv")
        output_file = data_root / "processed" / data_dir / "bank_b_clean.csv"

        # Create output directory if it doesn't exist
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Find all Bank_B CSV files
        bank_b_files = glob.glob(input_pattern)

        if not bank_b_files:
            print(f"Error: No CSV files found matching pattern '{input_pattern}'")
            return None

        print(f"Processing {data_dir.upper()} data")
        print(f"Found {len(bank_b_files)} Bank_B file(s):")
        for file in bank_b_files:
            print(f"  - {file}")

        # Load all Bank_B CSV files
        all_data = []
        for file in bank_b_files:
            print(f"\nLoading data from {file}...")
            df = pd.read_csv(file)
            all_data.append(df)
            print(f"  Loaded {len(df)} rows")

        # Combine all data
        bank_b_df = pd.concat(all_data, ignore_index=True)
        print(f"\nTotal rows loaded: {len(bank_b_df)}")

        # Parse dates from DD/MM/YYYY format to datetime
        bank_b_df["Transaction Date"] = pd.to_datetime(
            bank_b_df["Transaction Date"],
            format="%d/%m/%Y"
        )

        # Create amount column by combining Debit and Credit
        # Debit values are already negative in the CSV, Credit values are positive
        bank_b_df["amount"] = 0.0

        # Handle Debit column (expenses) - already negative, so just copy
        bank_b_df.loc[bank_b_df["Debit"].notna(), "amount"] = (
            bank_b_df.loc[bank_b_df["Debit"].notna(), "Debit"]
        )

        # Handle Credit column (income) - already positive, so just copy
        bank_b_df.loc[bank_b_df["Credit"].notna(), "amount"] = (
            bank_b_df.loc[bank_b_df["Credit"].notna(), "Credit"]
        )

        # Uppercase and trim descriptions (use Narration field)
        bank_b_df["description"] = (
            bank_b_df["Narration"]
            .str.strip()
            .str.upper()
        )

        # Flag positive amounts as 'income', negative as 'expense'
        bank_b_df["transaction_type"] = bank_b_df["amount"].apply(
            lambda x: "income" if x > 0 else "expense"
        )

        # Add source column
        bank_b_df["source"] = "Bank_B"

        # Rename Transaction Date to date for consistency
        bank_b_df = bank_b_df.rename(columns={"Transaction Date": "date"})

        # Select and reorder columns to match ANZ format
        bank_b_df = bank_b_df[[
            "date",
            "amount",
            "description",
            "transaction_type",
            "source"
        ]]

        # Remove duplicates (in case same transaction appears in multiple files)
        original_count = len(bank_b_df)
        bank_b_df = bank_b_df.drop_duplicates(
            subset=["date", "amount", "description"],
            keep="first"
        )
        duplicates_removed = original_count - len(bank_b_df)

        if duplicates_removed > 0:
            print(f"\nRemoved {duplicates_removed} duplicate transactions")

        # Filter to date range: 2024-01-01 to 2025-12-31
        start_date = pd.Timestamp("2024-01-01")
        end_date = pd.Timestamp("2025-12-31")
        before_filter = len(bank_b_df)
        bank_b_df = bank_b_df[(bank_b_df["date"] >= start_date) & (bank_b_df["date"] <= end_date)]
        filtered_out = before_filter - len(bank_b_df)
        if filtered_out > 0:
            print(f"Filtered out {filtered_out} transactions outside 2024-01-01 to 2025-12-31")

        # Save to processed folder
        bank_b_df.to_csv(output_file, index=False)
        print(f"\nData saved to {output_file}")

        # Print summary statistics
        print("\n" + "="*60)
        print("SUMMARY STATISTICS")
        print("="*60)

        # Date range
        date_min = bank_b_df["date"].min()
        date_max = bank_b_df["date"].max()
        print(f"\nDate Range: {date_min.strftime('%d/%m/%Y')} to {date_max.strftime('%d/%m/%Y')}")

        # Transaction counts
        total_transactions = len(bank_b_df)
        income_count = len(bank_b_df[bank_b_df["transaction_type"] == "income"])
        expense_count = len(bank_b_df[bank_b_df["transaction_type"] == "expense"])

        print(f"\nTransaction Counts:")
        print(f"  Total:    {total_transactions:>6}")
        print(f"  Income:   {income_count:>6}")
        print(f"  Expense:  {expense_count:>6}")

        # Totals
        total_income = bank_b_df[bank_b_df["transaction_type"] == "income"]["amount"].sum()
        total_expense = bank_b_df[bank_b_df["transaction_type"] == "expense"]["amount"].sum()
        net_total = bank_b_df["amount"].sum()

        print(f"\nTransaction Totals:")
        print(f"  Total Income:  ${total_income:>12,.2f}")
        print(f"  Total Expense: ${total_expense:>12,.2f}")
        print(f"  Net Total:     ${net_total:>12,.2f}")

        print("\n" + "="*60)
        print("Processing completed successfully!")
        print("="*60)

        return bank_b_df

    except FileNotFoundError:
        print(f"Error: Input files not found.")
        print(f"Please ensure Bank_B CSV files exist in {get_data_root() / 'raw' / data_dir}/")
        return None

    except pd.errors.ParserError as e:
        print(f"Error parsing CSV file: {e}")
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
    df = load_and_process_bank_b(data_dir)
