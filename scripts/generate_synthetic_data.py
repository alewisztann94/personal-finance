"""
Synthetic Transaction Data Generator
Generates realistic fake transaction data matching real patterns for safe GitHub sharing
"""

import pandas as pd
import random
from datetime import datetime, timedelta
from pathlib import Path

# Realistic merchant patterns by category
MERCHANTS = {
    "Groceries": [
        ("WOOLWORTHS", ["PERTH", "SUBIACO", "FREMANTLE", "JOONDALUP"]),
        ("COLES", ["PERTH", "NEDLANDS", "CLAREMONT", "COTTESLOE"]),
        ("ALDI", ["PERTH", "MORLEY", "CANNINGTON", "MIDLAND"]),
        ("IGA", ["SUBIACO", "LEEDERVILLE", "MOUNT LAWLEY"]),
        ("FARMER JACKS", ["SUBIACO", "FLOREAT", "WEMBLEY"]),
    ],
    "Dining Out": [
        ("MCDONALD'S", ["PERTH", "NORTHBRIDGE", "FREMANTLE"]),
        ("KFC", ["PERTH", "CAROUSEL", "INNALOO"]),
        ("GUZMAN Y GOMEZ", ["PERTH", "SUBIACO", "FREMANTLE"]),
        ("NANDO'S", ["PERTH", "JOONDALUP", "ROCKINGHAM"]),
        ("SUBWAY", ["PERTH", "CITY", "NORTHBRIDGE"]),
        ("HUNGRY JACK'S", ["PERTH", "MIDLAND", "CANNINGTON"]),
        ("THE COFFEE CLUB", ["PERTH", "GARDEN CITY", "CAROUSEL"]),
        ("DOME CAFE", ["SUBIACO", "COTTESLOE", "FREMANTLE"]),
        ("VARSITY BAR", ["NORTHBRIDGE", "FREMANTLE"]),
    ],
    "Transport": [
        ("BP", ["PERTH", "SUBIACO", "FREMANTLE", "NEDLANDS"]),
        ("AMPOL", ["PERTH", "WEST PERTH", "CLAREMONT"]),
        ("SHELL", ["PERTH", "MORLEY", "CANNINGTON"]),
        ("CALTEX", ["PERTH", "VICTORIA PARK", "SOUTH PERTH"]),
        ("UBER", ["SYDNEY"]),
        ("TRANSPERTH", ["PERTH"]),
    ],
    "Entertainment": [
        ("NETFLIX", ["SYDNEY"]),
        ("SPOTIFY", ["SYDNEY"]),
        ("STEAM PURCHASE", ["SYDNEY"]),
        ("APPLE.COM/BILL", ["SYDNEY"]),
        ("READING CINEMAS", ["BELMONT", "PERTH"]),
    ],
    "Utilities": [
        ("SYNERGY", ["PERTH"]),
        ("WATER CORPORATION", ["PERTH"]),
        ("IINET LTD", ["SYDNEY"]),
        ("TELSTRA", ["PERTH"]),
    ],
    "Insurance": [
        ("HBF HEALTH LIMITED", ["PERTH"]),
        ("RAC INSURANCE", ["PERTH"]),
    ],
    "Online Shopping": [
        ("AMAZON", ["SYDNEY"]),
        ("EBAY", ["SYDNEY"]),
        ("ALIEXPRESS", ["NORTH SYDNEY"]),
    ],
    "Retail": [
        ("KMART", ["PERTH", "CAROUSEL", "GARDEN CITY"]),
        ("TARGET", ["PERTH", "MORLEY", "INNALOO"]),
        ("BIG W", ["PERTH", "CANNINGTON", "JOONDALUP"]),
        ("BUNNINGS", ["INNALOO", "CANNINGTON", "OSBORNE PARK"]),
    ],
    "Health & Pharmacy": [
        ("CHEMIST WAREHOUSE", ["PERTH", "SUBIACO", "FREMANTLE"]),
        ("PRICELINE PHARMACY", ["PERTH", "GARDEN CITY"]),
        ("TERRY WHITE CHEMMART", ["SUBIACO", "CLAREMONT"]),
    ],
}

# Amount ranges by category (min, max)
AMOUNT_RANGES = {
    "Groceries": (25, 180),
    "Dining Out": (8, 75),
    "Transport": (30, 120),
    "Entertainment": (5, 25),
    "Utilities": (50, 250),
    "Insurance": (40, 120),
    "Online Shopping": (15, 200),
    "Retail": (20, 150),
    "Health & Pharmacy": (10, 80),
}

# Category weights (how often each category appears)
CATEGORY_WEIGHTS = {
    "Groceries": 25,
    "Dining Out": 20,
    "Transport": 15,
    "Entertainment": 8,
    "Utilities": 5,
    "Insurance": 3,
    "Online Shopping": 10,
    "Retail": 8,
    "Health & Pharmacy": 6,
}


def generate_merchant(category):
    """Generate a realistic merchant name for a category"""
    merchants = MERCHANTS.get(category, [("UNKNOWN MERCHANT", ["PERTH"])])
    merchant, locations = random.choice(merchants)
    location = random.choice(locations)
    return f"{merchant} {location}".upper()


def generate_amount(category):
    """Generate a realistic amount for a category"""
    min_amt, max_amt = AMOUNT_RANGES.get(category, (10, 100))
    # Use a slightly skewed distribution (more smaller purchases)
    amount = random.triangular(min_amt, max_amt, min_amt + (max_amt - min_amt) * 0.3)
    return round(amount, 2)


def generate_bank_a_transactions(start_date, end_date):
    """
    Generate synthetic Bank_A transactions with realistic spacing
    Bank_A format: date, amount, description (no header)
    """
    transactions = []
    categories = list(CATEGORY_WEIGHTS.keys())
    weights = list(CATEGORY_WEIGHTS.values())

    current_date = start_date

    while current_date <= end_date:
        # Generate 0-3 transactions per day, weighted toward weekends
        is_weekend = current_date.weekday() >= 5
        num_today = random.choices([0, 1, 2, 3], weights=[30, 45, 20, 5] if not is_weekend else [20, 35, 30, 15])[0]

        for _ in range(num_today):
            category = random.choices(categories, weights=weights)[0]
            amount = -generate_amount(category)  # Negative for expenses
            description = generate_merchant(category)
            transactions.append({
                "date": current_date.strftime("%d/%m/%Y"),
                "amount": f"{amount:.2f}",
                "description": description
            })

        # Move to next day (min 1 day between transaction batches)
        current_date += timedelta(days=1)

    # Sort by date descending (newest first, like real exports)
    transactions.sort(key=lambda x: datetime.strptime(x["date"], "%d/%m/%Y"), reverse=True)

    return pd.DataFrame(transactions)


def generate_bank_b_transactions(start_date, end_date):
    """
    Generate synthetic Bank_B transactions with fortnightly salary
    Bank_B format: BSB Number,Account Number,Transaction Date,Narration,Cheque Number,Debit,Credit,Balance,Transaction Type
    """
    transactions = []

    # $75,000/year = $2,885 per fortnight (before tax ~$2,400 net)
    base_salary = 2885
    salary_variation = 0.05  # ±5%

    # Start balance
    balance = round(random.uniform(5000, 10000), 2)

    # First payday - find first Thursday after start_date
    current_date = start_date
    while current_date.weekday() != 3:  # Thursday
        current_date += timedelta(days=1)
    next_payday = current_date

    current_date = start_date

    while current_date <= end_date:
        # Salary every 14 days on Thursday
        if current_date == next_payday:
            salary = round(base_salary * random.uniform(1 - salary_variation, 1 + salary_variation), 2)
            balance += salary
            transactions.append({
                "BSB Number": "000-000",
                "Account Number": "9999999",
                "Transaction Date": current_date.strftime("%d/%m/%Y"),
                "Narration": "SALARY EMPLOYER PAYROLL",
                "Cheque Number": "",
                "Debit": "",
                "Credit": salary,
                "Balance": round(balance, 2),
                "Transaction Type": "PAY"
            })
            next_payday = current_date + timedelta(days=14)

        # Rent payments - every Monday
        if current_date.weekday() == 0:
            rent = 350.00
            balance -= rent
            transactions.append({
                "BSB Number": "000-000",
                "Account Number": "9999999",
                "Transaction Date": current_date.strftime("%d/%m/%Y"),
                "Narration": "RENT PAYMENT",
                "Cheque Number": "",
                "Debit": -rent,
                "Credit": "",
                "Balance": round(balance, 2),
                "Transaction Type": "WDL"
            })

        # Monthly bills (utilities) - around 15th of month
        if current_date.day == 15:
            bill_amt = round(random.uniform(80, 200), 2)
            balance -= bill_amt
            transactions.append({
                "BSB Number": "000-000",
                "Account Number": "9999999",
                "Transaction Date": current_date.strftime("%d/%m/%Y"),
                "Narration": "SYNERGY ELECTRICITY",
                "Cheque Number": "",
                "Debit": -bill_amt,
                "Credit": "",
                "Balance": round(balance, 2),
                "Transaction Type": "WDL"
            })

        # Occasional transfers to savings (1-2 per month)
        if current_date.day in [5, 20] and random.random() < 0.7:
            transfer_amt = round(random.uniform(200, 600), 2)
            balance -= transfer_amt
            transactions.append({
                "BSB Number": "000-000",
                "Account Number": "9999999",
                "Transaction Date": current_date.strftime("%d/%m/%Y"),
                "Narration": "IB TRANSFER TO SAVINGS",
                "Cheque Number": "",
                "Debit": -transfer_amt,
                "Credit": "",
                "Balance": round(balance, 2),
                "Transaction Type": "TFD"
            })

        current_date += timedelta(days=1)

    # Sort by date descending
    transactions.sort(
        key=lambda x: datetime.strptime(x["Transaction Date"], "%d/%m/%Y"),
        reverse=True
    )

    return pd.DataFrame(transactions)


def main():
    """Generate synthetic data and save to files"""
    output_dir = Path("data/raw/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Full 12 months of 2025 only
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 12, 31)

    print("Generating synthetic transaction data...")
    print(f"Date range: {start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}")

    # Generate Bank_A transactions
    print("\nGenerating Bank_A transactions...")
    bank_a_df = generate_bank_a_transactions(start_date, end_date)
    bank_a_output = output_dir / "Bank_A.csv"
    bank_a_df.to_csv(bank_a_output, index=False, header=False)
    print(f"  Generated {len(bank_a_df)} Bank_A transactions")
    print(f"  Saved to {bank_a_output}")

    # Generate Bank_B transactions
    print("\nGenerating Bank_B transactions...")
    bank_b_df = generate_bank_b_transactions(start_date, end_date)
    bank_b_output = output_dir / "Bank_B.csv"
    bank_b_df.to_csv(bank_b_output, index=False)
    print(f"  Generated {len(bank_b_df)} Bank_B transactions")
    print(f"  Saved to {bank_b_output}")

    print("\n" + "="*60)
    print("Synthetic data generation complete!")
    print("="*60)
    print(f"\nFiles created:")
    print(f"  - {bank_a_output}")
    print(f"  - {bank_b_output}")
    print(f"\nYou can now run the processing pipeline with:")
    print(f"  python scripts/run_pipeline.py synthetic")


if __name__ == "__main__":
    main()
