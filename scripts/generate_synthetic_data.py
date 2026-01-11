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


def generate_anz_transactions(num_transactions=300, start_date=None, end_date=None):
    """
    Generate synthetic ANZ transactions
    ANZ format: date, amount, description (no header)
    """
    if end_date is None:
        end_date = datetime.now()
    if start_date is None:
        start_date = end_date - timedelta(days=365)

    transactions = []
    categories = list(CATEGORY_WEIGHTS.keys())
    weights = list(CATEGORY_WEIGHTS.values())

    # Generate expense transactions (~85%)
    num_expenses = int(num_transactions * 0.85)
    for _ in range(num_expenses):
        category = random.choices(categories, weights=weights)[0]
        date = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
        amount = -generate_amount(category)  # Negative for expenses
        description = generate_merchant(category)
        transactions.append({
            "date": date.strftime("%d/%m/%Y"),
            "amount": f"{amount:.2f}",
            "description": description
        })

    # Generate income transactions (~15%)
    num_income = num_transactions - num_expenses
    income_sources = [
        ("SALARY EMPLOYER PTY LTD", 2500, 3500),
        ("TAX REFUND ATO", 200, 800),
        ("INTEREST PAYMENT", 5, 50),
        ("REFUND", 20, 150),
    ]

    for _ in range(num_income):
        source, min_amt, max_amt = random.choice(income_sources)
        date = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
        amount = round(random.uniform(min_amt, max_amt), 2)
        transactions.append({
            "date": date.strftime("%d/%m/%Y"),
            "amount": f"{amount:.2f}",
            "description": source
        })

    # Sort by date descending (newest first, like real ANZ exports)
    transactions.sort(key=lambda x: datetime.strptime(x["date"], "%d/%m/%Y"), reverse=True)

    return pd.DataFrame(transactions)


def generate_bankwest_transactions(num_transactions=50, start_date=None, end_date=None):
    """
    Generate synthetic Bankwest transactions
    Bankwest format: BSB Number,Account Number,Transaction Date,Narration,Cheque Number,Debit,Credit,Balance,Transaction Type
    """
    if end_date is None:
        end_date = datetime.now()
    if start_date is None:
        start_date = end_date - timedelta(days=365)

    transactions = []

    # Bankwest typically has fewer transactions (savings/salary account)
    # Generate salary deposits
    current_date = start_date
    balance = round(random.uniform(3000, 8000), 2)

    while current_date <= end_date:
        # Salary every 2 weeks
        if random.random() < 0.5:  # ~fortnightly
            salary = round(random.uniform(2400, 2600), 2)
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

        # Rent payments
        if current_date.weekday() == 0 and random.random() < 0.3:  # Some Mondays
            rent = 300.00
            balance -= rent
            transactions.append({
                "BSB Number": "000-000",
                "Account Number": "9999999",
                "Transaction Date": current_date.strftime("%d/%m/%Y"),
                "Narration": "RENT",
                "Cheque Number": "",
                "Debit": -rent,
                "Credit": "",
                "Balance": round(balance, 2),
                "Transaction Type": "WDL"
            })

        # Occasional transfers
        if random.random() < 0.05:
            transfer_amt = round(random.uniform(100, 500), 2)
            balance -= transfer_amt
            transactions.append({
                "BSB Number": "000-000",
                "Account Number": "9999999",
                "Transaction Date": current_date.strftime("%d/%m/%Y"),
                "Narration": f"IB TRANSFER TO SAVINGS",
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

    # Generate date range (1 year)
    end_date = datetime(2026, 1, 6)  # Match your real data's latest date
    start_date = end_date - timedelta(days=365)

    print("Generating synthetic transaction data...")
    print(f"Date range: {start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}")

    # Generate ANZ transactions
    print("\nGenerating ANZ transactions...")
    anz_df = generate_anz_transactions(300, start_date, end_date)
    anz_output = output_dir / "ANZ.csv"
    anz_df.to_csv(anz_output, index=False, header=False)
    print(f"  Generated {len(anz_df)} ANZ transactions")
    print(f"  Saved to {anz_output}")

    # Generate Bankwest transactions
    print("\nGenerating Bankwest transactions...")
    bankwest_df = generate_bankwest_transactions(50, start_date, end_date)
    bankwest_output = output_dir / "bankwest.csv"
    bankwest_df.to_csv(bankwest_output, index=False)
    print(f"  Generated {len(bankwest_df)} Bankwest transactions")
    print(f"  Saved to {bankwest_output}")

    print("\n" + "="*60)
    print("Synthetic data generation complete!")
    print("="*60)
    print(f"\nFiles created:")
    print(f"  - {anz_output}")
    print(f"  - {bankwest_output}")
    print(f"\nYou can now run the processing pipeline with:")
    print(f"  python scripts/01_load_anz.py synthetic")
    print(f"  python scripts/02_load_bankwest.py synthetic")
    print(f"  python scripts/03_combine.py synthetic")
    print(f"  python scripts/04_categorize.py synthetic")


if __name__ == "__main__":
    main()
