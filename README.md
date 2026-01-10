I've placed all of my thoughts as I progressed through this project in NOTES.md. 

Claude generated:
# Personal Finance Tracker

## Overview
Automated pipeline to track and categorize personal spending across multiple bank accounts.

## Technical Approach

**Data Loading & Cleaning:**
- Python scripts load raw CSVs from ANZ and Bankwest
- AI-assisted categorization of merchant names using pattern matching
- Handled edge cases: credit card payments (positive amounts), case sensitivity

**Why AI-assisted?**
Manual categorization of 500+ merchant names is tedious busywork. 
I used AI to generate the categorization logic, then validated and tested the output.
This represents real-world development practice - using tools efficiently to ship faster.

## What I Learned
- Pandas for data cleaning and transformation
- SQLite for data storage
- SQL for analysis and budgeting
- Git workflow for version control
- Trade-offs between manual work vs. automatio