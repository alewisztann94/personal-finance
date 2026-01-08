"""
Bankwest Transaction Data Processing Script
Loads raw Bankwest CSV data, cleans it, and saves to processed folder
"""

import pandas as pd
from pathlib import Path
import glob

def load_and_process_bankwest():
    """
    Load and process Bankwest transaction data
    """
    try:
        # Define file paths
        input_pattern = "data/raw/bankwest/*.csv"
        output_file = Path("data/processed/bankwest_clean.csv")

        # Create output directory if it doesn't exist
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Find all Bankwest CSV files
        bankwest_files = glob.glob(input_pattern)

        if not bankwest_files:
            print(f"Error: No CSV files found matching pattern '{input_pattern}'")
            return None

        print(f"Found {len(bankwest_files)} Bankwest file(s):")
        for file in bankwest_files:
            print(f"  - {file}")

        # Load all Bankwest CSV files
        all_data = []
        for file in bankwest_files:
            print(f"\nLoading data from {file}...")
            df = pd.read_csv(file)
            all_data.append(df)
            print(f"  Loaded {len(df)} rows")

        # Combine all data
        bankwest_df = pd.concat(all_data, ignore_index=True)
        print(f"\nTotal rows loaded: {len(bankwest_df)}")

        # Parse dates from DD/MM/YYYY format to datetime
        bankwest_df["Transaction Date"] = pd.to_datetime(
            bankwest_df["Transaction Date"],
            format="%d/%m/%Y"
        )

        # Create amount column by combining Debit and Credit
        # Debit = money out (negative), Credit = money in (positive)
        bankwest_df["amount"] = 0.0

        # Handle Debit column (expenses)
        bankwest_df.loc[bankwest_df["Debit"].notna(), "amount"] = (
            -bankwest_df.loc[bankwest_df["Debit"].notna(), "Debit"]
        )

        # Handle Credit column (income)
        bankwest_df.loc[bankwest_df["Credit"].notna(), "amount"] = (
            bankwest_df.loc[bankwest_df["Credit"].notna(), "Credit"]
        )

        # Uppercase and trim descriptions (use Narration field)
        bankwest_df["description"] = (
            bankwest_df["Narration"]
            .str.strip()
            .str.upper()
        )

        # Flag positive amounts as 'income', negative as 'expense'
        bankwest_df["transaction_type"] = bankwest_df["amount"].apply(
            lambda x: "income" if x > 0 else "expense"
        )

        # Add source column
        bankwest_df["source"] = "Bankwest"

        # Rename Transaction Date to date for consistency
        bankwest_df = bankwest_df.rename(columns={"Transaction Date": "date"})

        # Select and reorder columns to match ANZ format
        bankwest_df = bankwest_df[[
            "date",
            "amount",
            "description",
            "transaction_type",
            "source"
        ]]

        # Remove duplicates (in case same transaction appears in multiple files)
        original_count = len(bankwest_df)
        bankwest_df = bankwest_df.drop_duplicates(
            subset=["date", "amount", "description"],
            keep="first"
        )
        duplicates_removed = original_count - len(bankwest_df)

        if duplicates_removed > 0:
            print(f"\nRemoved {duplicates_removed} duplicate transactions")

        # Save to processed folder
        bankwest_df.to_csv(output_file, index=False)
        print(f"\nData saved to {output_file}")

        # Print summary statistics
        print("\n" + "="*60)
        print("SUMMARY STATISTICS")
        print("="*60)

        # Date range
        date_min = bankwest_df["date"].min()
        date_max = bankwest_df["date"].max()
        print(f"\nDate Range: {date_min.strftime('%d/%m/%Y')} to {date_max.strftime('%d/%m/%Y')}")

        # Transaction counts
        total_transactions = len(bankwest_df)
        income_count = len(bankwest_df[bankwest_df["transaction_type"] == "income"])
        expense_count = len(bankwest_df[bankwest_df["transaction_type"] == "expense"])

        print(f"\nTransaction Counts:")
        print(f"  Total:    {total_transactions:>6}")
        print(f"  Income:   {income_count:>6}")
        print(f"  Expense:  {expense_count:>6}")

        # Totals
        total_income = bankwest_df[bankwest_df["transaction_type"] == "income"]["amount"].sum()
        total_expense = bankwest_df[bankwest_df["transaction_type"] == "expense"]["amount"].sum()
        net_total = bankwest_df["amount"].sum()

        print(f"\nTransaction Totals:")
        print(f"  Total Income:  ${total_income:>12,.2f}")
        print(f"  Total Expense: ${total_expense:>12,.2f}")
        print(f"  Net Total:     ${net_total:>12,.2f}")

        print("\n" + "="*60)
        print("Processing completed successfully!")
        print("="*60)

        return bankwest_df

    except FileNotFoundError:
        print(f"Error: Input files not found.")
        print("Please ensure Bankwest CSV files exist in data/raw/bankwest/")
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
    df = load_and_process_bankwest()
