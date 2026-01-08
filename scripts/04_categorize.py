"""
Transaction Categorization Script
Applies category rules to combined transaction data from all banks
"""

import pandas as pd
from pathlib import Path

def categorize_transactions():
    """
    Categorize all transactions based on rules
    """
    try:
        # Define file paths
        input_file = Path("data/processed/all_transactions_clean.csv")
        rules_file = Path("data/category_rules.csv")
        output_file = Path("data/processed/all_transactions_categorized.csv")

        # Create output directory if it doesn't exist
        output_file.parent.mkdir(parents=True, exist_ok=True)

        print(f"Loading combined transactions from {input_file}...")

        # Load combined transaction data
        transactions_df = pd.read_csv(input_file)
        transactions_df['date'] = pd.to_datetime(transactions_df['date'])

        print(f"Loaded {len(transactions_df)} transactions")

        print(f"\nLoading category rules from {rules_file}...")

        # Load category rules
        rules_df = pd.read_csv(rules_file)

        print(f"Loaded {len(rules_df)} category rules")

        # Initialize category column
        transactions_df['category'] = None

        # Categorize transactions
        print("\nCategorizing transactions...")

        for idx, row in transactions_df.iterrows():
            # Check description against patterns (case insensitive)
            description_upper = str(row['description']).upper()
            matched = False

            for _, rule in rules_df.iterrows():
                pattern = str(rule['pattern']).upper()
                if pattern in description_upper:
                    transactions_df.at[idx, 'category'] = rule['category']
                    matched = True
                    break  # First match wins

            # If no pattern matched, use default categories
            if not matched:
                if row['transaction_type'] == 'income':
                    transactions_df.at[idx, 'category'] = 'Income'
                else:
                    transactions_df.at[idx, 'category'] = 'Uncategorized'

        # Save categorized data
        transactions_df.to_csv(output_file, index=False)
        print(f"\nCategorized data saved to {output_file}")

        # Print summary statistics
        print("\n" + "="*60)
        print("CATEGORIZATION SUMMARY")
        print("="*60)

        total_transactions = len(transactions_df)
        categorized_count = len(transactions_df[transactions_df['category'] != 'Uncategorized'])
        uncategorized_count = len(transactions_df[transactions_df['category'] == 'Uncategorized'])

        print(f"\nTotal Transactions: {total_transactions}")
        print(f"Categorized:        {categorized_count} ({categorized_count/total_transactions*100:.1f}%)")
        print(f"Uncategorized:      {uncategorized_count} ({uncategorized_count/total_transactions*100:.1f}%)")

        # Breakdown by category
        print("\n" + "-"*60)
        print("BREAKDOWN BY CATEGORY")
        print("-"*60)

        category_counts = transactions_df['category'].value_counts().sort_values(ascending=False)

        for category, count in category_counts.items():
            total_amount = transactions_df[transactions_df['category'] == category]['amount'].sum()
            print(f"{category:<25} {count:>5} transactions  ${total_amount:>12,.2f}")

        # Income/Expense totals (excluding transfers)
        print("\n" + "-"*60)
        print("INCOME & EXPENSE TOTALS (excluding Transfers)")
        print("-"*60)

        non_transfer = transactions_df[transactions_df['category'] != 'Transfer']
        real_income = non_transfer[non_transfer['transaction_type'] == 'income']['amount'].sum()
        real_expense = non_transfer[non_transfer['transaction_type'] == 'expense']['amount'].sum()
        real_net = non_transfer['amount'].sum()

        print(f"Real Income:  ${real_income:>12,.2f}")
        print(f"Real Expense: ${real_expense:>12,.2f}")
        print(f"Net Total:    ${real_net:>12,.2f}")

        # Top 10 uncategorized merchants
        print("\n" + "-"*60)
        print("TOP 10 UNCATEGORIZED MERCHANTS")
        print("-"*60)

        uncategorized = transactions_df[transactions_df['category'] == 'Uncategorized']

        if len(uncategorized) > 0:
            # Count occurrences of each unique description
            uncategorized_merchants = uncategorized['description'].value_counts().head(10)

            for idx, (merchant, count) in enumerate(uncategorized_merchants.items(), 1):
                total = uncategorized[uncategorized['description'] == merchant]['amount'].sum()
                print(f"{idx:>2}. {merchant:<40} {count:>3}x  ${total:>10,.2f}")
        else:
            print("No uncategorized transactions!")

        # Categorization rate by source
        print("\n" + "-"*60)
        print("CATEGORIZATION RATE BY SOURCE")
        print("-"*60)

        for source in transactions_df['source'].unique():
            source_df = transactions_df[transactions_df['source'] == source]
            source_categorized = len(source_df[source_df['category'] != 'Uncategorized'])
            source_total = len(source_df)
            rate = (source_categorized / source_total * 100) if source_total > 0 else 0
            print(f"{source:<12} {source_categorized:>4}/{source_total:<4} ({rate:.1f}%)")

        print("\n" + "="*60)
        print("Categorization completed successfully!")
        print("="*60)

        return transactions_df

    except FileNotFoundError as e:
        print(f"Error: Required file not found - {e}")
        print("Please ensure both the combined data and category rules files exist.")
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
    df = categorize_transactions()
