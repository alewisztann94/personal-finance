# Personal Finance Tracker

A Python pipeline to track and categorize personal spending across multiple bank accounts.

See [NOTES.md](NOTES.md) for my detailed learning notes and thought process throughout this project.

## Project Structure

```
personal-finance/
├── data/
│   ├── raw/
│   │   ├── real/              # Actual bank data (gitignored)
│   │   └── synthetic/         # Generated fake data for demo
│   ├── processed/
│   │   ├── real/              # Processed real data (gitignored)
│   │   └── synthetic/         # Processed synthetic data
│   └── category_rules.csv     # Pattern matching rules for categorization
├── scripts/
│   ├── 01_load_bank_a.py      # Load and clean Bank A transactions
│   ├── 02_load_bank_b.py      # Load and clean Bank B transactions
│   ├── 03_combine.py          # Combine data from all banks
│   ├── 04_categorize.py       # Categorize transactions using rules
│   ├── 05_load_to_db.py       # Load to SQLite database
│   ├── generate_synthetic_data.py  # Generate fake data for testing
│   └── run_pipeline.py        # Orchestrate full pipeline
└── .gitignore                 # Excludes real financial data
```

## Quick Start

```bash
# Generate synthetic data (or place your real bank CSVs in data/raw/real/)
python scripts/generate_synthetic_data.py

# Run the full pipeline
python scripts/run_pipeline.py           # Uses synthetic data by default
python scripts/run_pipeline.py real      # Process real data
```

## Pipeline Steps

| Step | Script | Description |
|------|--------|-------------|
| 1 | `01_load_bank_a.py` | Load Bank A CSV, parse dates, normalize descriptions |
| 2 | `02_load_bank_b.py` | Load Bank B CSV, combine debit/credit columns |
| 3 | `03_combine.py` | Merge both banks into single dataset |
| 4 | `04_categorize.py` | Apply category rules via pattern matching |
| 5 | `05_load_to_db.py` | Load to SQLite for SQL analysis |

## Technical Approach

**Data Loading & Cleaning:**
- Python scripts load raw CSVs from multiple bank accounts
- Each bank has different CSV formats - scripts normalize to common schema
- Dates parsed to datetime, amounts to float, descriptions uppercased

**Categorization:**
- Pattern matching against `category_rules.csv`
- First match wins - order matters (transfers before transport to catch "IB BPAY" before "BP")
- Uncategorized expenses flagged for review

**Privacy:**
- Real financial data is gitignored
- Synthetic data generator creates realistic fake transactions
- Safe to push to public GitHub

## What I Learned

- Pandas for data cleaning and transformation
- SQLite for data storage
- Python module imports and `if __name__ == "__main__"` pattern
- Pipeline orchestration using `importlib`
- Git workflow - .gitignore for sensitive data
- Trade-offs between manual work vs. AI-assisted development

