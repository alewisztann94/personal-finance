"""
ANZ Transaction Data Processing Script
Loads raw ANZ CSV data, cleans it, and saves to processed folder
"""

import pandas as pd
from pathlib import Path
import glob

def load_and_process_anz():
    """
    Load and process ANZ transaction data
    """
    try:
        # Define file paths
        input_pattern = "data/raw/anz/*.csv"
        output_file = Path("data/processed/anz_clean.csv")

        # Create output directory if it doesn't exist
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Find all ANZ CSV files
        anz_files = glob.glob(input_pattern)

        if not anz_files:
            print(f"Error: No CSV files found matching pattern '{input_pattern}'")
            return None

        print(f"Found {len(anz_files)} ANZ file(s):")
        for file in anz_files:
            print(f"  - {file}")

        # Load all ANZ CSV files
        all_data = []
        for file in anz_files:
            print(f"\nLoading data from {file}...")
            df = pd.read_csv(
                file,
                header=None,
                names=["date", "amount", "description"]
            )
            all_data.append(df)
            print(f"  Loaded {len(df)} rows")

        # Combine all data
        anz_df = pd.concat(all_data, ignore_index=True)
        print(f"\nTotal rows loaded: {len(anz_df)}")

        # Parse dates from DD/MM/YYYY format to datetime
        anz_df["date"] = pd.to_datetime(anz_df["date"], format="%d/%m/%Y")

        # Convert amounts to float (handle commas and quotes)
        anz_df["amount"] = anz_df["amount"].astype(str).str.replace(',', '').astype(float)

        # Uppercase and trim descriptions
        anz_df["description"] = anz_df["description"].str.strip().str.upper()

        # Flag positive amounts as 'income', negative as 'expense'
        anz_df["transaction_type"] = anz_df["amount"].apply(
            lambda x: "income" if x > 0 else "expense"
        )

        # Add source column
        anz_df["source"] = "ANZ"

        # Reorder columns
        anz_df = anz_df[["date", "amount", "description", "transaction_type", "source"]]

        # Remove duplicates (in case same transaction appears in multiple files)
        original_count = len(anz_df)
        anz_df = anz_df.drop_duplicates(
            subset=["date", "amount", "description"],
            keep="first"
        )
        duplicates_removed = original_count - len(anz_df)

        if duplicates_removed > 0:
            print(f"\nRemoved {duplicates_removed} duplicate transactions")

        # Save to processed folder
        anz_df.to_csv(output_file, index=False)
        print(f"\nData saved to {output_file}")

        # Print summary statistics
        print("\n" + "="*60)
        print("SUMMARY STATISTICS")
        print("="*60)

        # Date range
        date_min = anz_df["date"].min()
        date_max = anz_df["date"].max()
        print(f"\nDate Range: {date_min.strftime('%d/%m/%Y')} to {date_max.strftime('%d/%m/%Y')}")

        # Transaction counts
        total_transactions = len(anz_df)
        income_count = len(anz_df[anz_df["transaction_type"] == "income"])
        expense_count = len(anz_df[anz_df["transaction_type"] == "expense"])

        print(f"\nTransaction Counts:")
        print(f"  Total:    {total_transactions:>6}")
        print(f"  Income:   {income_count:>6}")
        print(f"  Expense:  {expense_count:>6}")

        # Totals
        total_income = anz_df[anz_df["transaction_type"] == "income"]["amount"].sum()
        total_expense = anz_df[anz_df["transaction_type"] == "expense"]["amount"].sum()
        net_total = anz_df["amount"].sum()

        print(f"\nTransaction Totals:")
        print(f"  Total Income:  ${total_income:>12,.2f}")
        print(f"  Total Expense: ${total_expense:>12,.2f}")
        print(f"  Net Total:     ${net_total:>12,.2f}")

        print("\n" + "="*60)
        print("Processing completed successfully!")
        print("="*60)

        return anz_df

    except FileNotFoundError:
        print(f"Error: Input files not found.")
        print("Please ensure ANZ CSV files exist in data/raw/anz/")
        return None

    except pd.errors.ParserError as e:
        print(f"Error parsing CSV file: {e}")
        return None

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

if __name__ == "__main__":
    df = load_and_process_anz()
