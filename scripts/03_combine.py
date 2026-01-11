"""
Transaction Data Combination Script
Combines cleaned ANZ and Bankwest transaction data into a single dataset
"""

import pandas as pd
from pathlib import Path
import sys

def combine_transactions(data_dir="synthetic"):
    """
    Combine ANZ and Bankwest transaction data

    Args:
        data_dir: Either "real" or "synthetic" (default: "synthetic" for safety)
    """
    try:
        # Define file paths based on data_dir
        anz_file = Path(f"data/processed/{data_dir}/anz_clean.csv")
        bankwest_file = Path(f"data/processed/{data_dir}/bankwest_clean.csv")
        output_file = Path(f"data/processed/{data_dir}/all_transactions_clean.csv")

        # Create output directory if it doesn't exist
        output_file.parent.mkdir(parents=True, exist_ok=True)

        print(f"Processing {data_dir.upper()} data")
        print("Loading cleaned transaction data...")

        # Load ANZ data
        if anz_file.exists():
            anz_df = pd.read_csv(anz_file)
            anz_df['date'] = pd.to_datetime(anz_df['date'])
            print(f"  ANZ: {len(anz_df)} transactions")
        else:
            print(f"  Warning: {anz_file} not found, skipping ANZ data")
            anz_df = pd.DataFrame(columns=["date", "amount", "description", "transaction_type", "source"])

        # Load Bankwest data
        if bankwest_file.exists():
            bankwest_df = pd.read_csv(bankwest_file)
            bankwest_df['date'] = pd.to_datetime(bankwest_df['date'])
            print(f"  Bankwest: {len(bankwest_df)} transactions")
        else:
            print(f"  Warning: {bankwest_file} not found, skipping Bankwest data")
            bankwest_df = pd.DataFrame(columns=["date", "amount", "description", "transaction_type", "source"])

        # Combine data
        combined_df = pd.concat([anz_df, bankwest_df], ignore_index=True)

        if len(combined_df) == 0:
            print("\nError: No transaction data found to combine")
            return None

        # Sort by date (oldest to newest)
        combined_df = combined_df.sort_values('date').reset_index(drop=True)

        # Remove duplicates across banks (in case of transfers between accounts)
        original_count = len(combined_df)
        combined_df = combined_df.drop_duplicates(
            subset=["date", "amount", "description"],
            keep="first"
        )
        duplicates_removed = original_count - len(combined_df)

        if duplicates_removed > 0:
            print(f"\nRemoved {duplicates_removed} duplicate transactions across banks")

        # Save combined data
        combined_df.to_csv(output_file, index=False)
        print(f"\nCombined data saved to {output_file}")

        # Print summary statistics
        print("\n" + "="*60)
        print("COMBINED DATASET SUMMARY")
        print("="*60)

        # Date range
        date_min = combined_df["date"].min()
        date_max = combined_df["date"].max()
        print(f"\nDate Range: {date_min.strftime('%d/%m/%Y')} to {date_max.strftime('%d/%m/%Y')}")

        # Transaction counts by source
        print(f"\nTransactions by Source:")
        for source in combined_df["source"].unique():
            count = len(combined_df[combined_df["source"] == source])
            print(f"  {source:<12} {count:>6} transactions")
        print(f"  {'Total':<12} {len(combined_df):>6} transactions")

        # Transaction counts by type
        total_transactions = len(combined_df)
        income_count = len(combined_df[combined_df["transaction_type"] == "income"])
        expense_count = len(combined_df[combined_df["transaction_type"] == "expense"])

        print(f"\nTransactions by Type:")
        print(f"  Income:   {income_count:>6}")
        print(f"  Expense:  {expense_count:>6}")

        # Totals
        total_income = combined_df[combined_df["transaction_type"] == "income"]["amount"].sum()
        total_expense = combined_df[combined_df["transaction_type"] == "expense"]["amount"].sum()
        net_total = combined_df["amount"].sum()

        print(f"\nTransaction Totals:")
        print(f"  Total Income:  ${total_income:>12,.2f}")
        print(f"  Total Expense: ${total_expense:>12,.2f}")
        print(f"  Net Total:     ${net_total:>12,.2f}")

        # Breakdown by source
        print(f"\nNet Total by Source:")
        for source in combined_df["source"].unique():
            source_total = combined_df[combined_df["source"] == source]["amount"].sum()
            print(f"  {source:<12} ${source_total:>12,.2f}")

        print("\n" + "="*60)
        print("Combination completed successfully!")
        print("="*60)

        return combined_df

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
    df = combine_transactions(data_dir)
