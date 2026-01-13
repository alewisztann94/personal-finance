# Personal Finance Project Notes

## Table of Contents

- [Introduction](#introduction)
- [09/01/26 - Getting Started](#090126---getting-started)
- [09/01/26 - Code Review](#090126---code-review)
- [10/01/26 - Pipeline Deep Dive](#100126---pipeline-deep-dive)
- [11/01/26 - SQL Analysis](#110126---sql-analysis)
- [12/01/26 - Dashboard Development](#120126---dashboard-development)
- [13/01/26 - UV and Dependency Management](#130126---uv-and-dependency-management)

---

## Introduction

After letting Claude essentially write and orchestrate the entire first project (perth-real_estate), I decided to try a more educational approach without leveraging Claude writing everything for me.

Personal finance budgeting is relatively straightforward - we chuck all our downloaded data into a dataframe and then have to categorise them all, however that requires alot of parsing through strings.

Claude recommended transformations in Python, but knowing that I have to learn ELT and dbt for a more modern approach to the analytics stack, I figured this might be a good chance for me to try categorisation using dbt as opposed to throwing a whole bunch of mapped strings into a python dictionary and looping transaction descriptions through it.

Well. Claude told me to do both so I'll do the Python approach and then I'll refactor this as a dbt project.

### Update 30 minutes later: I got bored slogging through syntax/manual categorization and had a change of heart.

> originally i had an existential crisis and started talking to claude and telling it to not suggest me code and for me to write everything by scratch. I got through the data load googling ancient reddit posts, disabling VS code autocomplete (with the use of AI), and then once I was manually categorizing manual transactions I realized something: I absolutely do not want to do this, and I am going to leverage AI, and as long as I can catch things that are wrong and have a read of the code and ask it the right things, I am going to continue leveraging it to build. I don't have to be a 10x AI engineer who knows absolutely everything about programming, I am an analytics engineer and I'm going to spend my time learning architectural things and figuring out how to use AI effectively and through practical use, figure out it's potential flaws and downsides.
>
> In the past I would get bogged down in the syntax, why would I do that now when I can get AI to do it for me?
>
> we will see if this goes disastrously for me but for now I'm throwing caution to the wind I think.

---

## 09/01/26 - Getting Started

I decided to lean in to the power of claude code, a few interesting things to note:

### Architectural Decision

Do we load anz/bankwest data individually then categorise per bank? Or do we load both datasets, combine them, then run the categorisation on the combined set.

Advantages of individual are: we can isolate transactions at a bank level.

What's the point of this project though, we want an overview of what our overall expenses and income is, and how we are spending. In that case it's better to combine, we don't need granularity at the individual bank level.

### Bug Discovery

I also noticed that we weren't appropriately categorizing some transfers as my real income was far too high. I wish it was that high but I knew something was up.

By simply mentioning to Claude Code that my annual salary is x and that the figures are off based on the date range, the LLM was able to notice that we are mapping 'IBP Payments' to 'BP' (transport) instead of transfers.

### Scope for Improvement

1. Better prompting
2. Make usage of hooks and context management

---

## 09/01/26 - Code Review

Decided to code review and then assess what claude had to say about my relative understanding / questions about decisions.

> `--` are answers from claude code

### Script 1: `01_load_anz.py`

Input pattern is a string, we use glob to search through directory to find all anz csv files.

If we don't find any print an error and exit the script by returning `None`.

Print name of all csv files found by glob.

Parse through the csv files and turn each one into a df. Store the dataframes in an array, and print the row length of each dataframe.

Interesting - we are working with the assumption that all anz csv files contain the same column structure.

Combine the dataframes using `pd.concat`.

We convert dates to datetime, I believe the reason is because datetime format allows time series analysis.

Convert amounts to floats to avoid weird rounding and well... money is to two decimal points.

We normalise the descriptions by getting rid of whitespaces. I'm not 100% sure if it removes leading and trailing. Strings are all converted to uppercase.

> -- removes leading + trailing. leaves middle whitespace.

We add a new column `transaction_type` that uses the amount to determine if it's income or an expense. I'm not confident with this syntax but logically looks fine. Income if amount is above zero else it's negative and an expense.

We have a remove duplicates script that I'm unsure of the need. Actually we don't want to double up on transactions so fair enough. We might have overlapping input csvs. I'm okay with this.

We then have a bunch of aggregates and summary statistics to validate what we've processed.

The end is a series of smart error handling in case of a corrupted file path, or csv file, or just anything else I guess. What results in an `Exception` exactly? I recall seeing it in error handling quite often.

> -- exception is a catch all for errors (network issues, permission errors, memory errors, etc. safety net)

### Script 2: `02_load_bankwest.py`

Similar to script 1. Originally script 1 did not have the ability to process multiple files, but bankwest load script had this functionality. Prompted claude to add functionality to script 1 which was done.

Loading steps are identical with the exception of `read_csv` which doesn't specifically name headers. This is because the bankwest csv has a header row. Am assuming default parameters for `read_csv` will automatically include the first row as a header which is why claude left it. Probably more robust to have first row as headers so it is robust to changes to column structure changes. Depends on data source of course.

I recall claude had to parse through a few times to recognise that debits were already negative. Being specific in prompting how to treat data values would improve performance and save time.

Perhaps thinking or planning mode could help here?

> -- yes it would

How would we include hooks into this project?

> -- `.claude/hooks.json` -> used to run linters (parses through file without running to look for dodgy syntax, tests/validations pre/post tool usage. gone through this in the claude code in action course)

Handling credit and debit column looks syntactically heavy but we essentially just collapse the debit and credit columns into the amount column.

We are combining the datasets (anz + bankwest) hence why we have to do it.

Normalizing description column by stripping whitespaces from narration column and converting to uppercase. Same as script 1.

After this the process is pretty much the same as script 1. Columns are all converted to the same name as the anz data.

### Script 3: `03_combine.py`

Define paths to cleaned files and output file.

Loading data seems fine -> I am unsure about the else clause for loading the data. Why are we declaring:

```python
anz_df = pd.DataFrame(columns=["date", "amount", "description", "transaction_type", "source"])
```

when the file is not found? Same with the bankwest load.

> -- this is done because concat wont work without two dataframes. therefore we declare an empty one so the concat works.

Concatenating the dataframes seems fine. `ignore_index` means that we don't add an id column I believe.

Explain the `reset_index` on line 50 please.

> -- we do this because sorting throws the indexes out of line. we renumber the indexes and drop the index column.

Explain the `#transaction counts by source` section. In particular why do we use the `<12` and `>6`:

```python
print(f"  {source:<12} {count:>6} transactions")
print(f"  {'Total':<12} {len(combined_df):>6} transactions")
```

> -- these numbers in f strings are just used to format.
> - `<12` = left-align in a 12-character-wide field
> - `>6` = right-align in a 6-character-wide field

I also noticed that we return the df at the end and this behaviour is the same for scripts 1 and 2. May I ask if this is standard? Do we need to return something because in the scripts we have already saved the csv. Do we return the df to successfully exit a script?

> -- Allows interactive use (you can capture it: `df = load_and_process_anz()`)
> Enables chaining scripts together
> Useful for testing/debugging
> Doesn't hurt anything - the CSV is already saved

### Script 4: `04_categorize.py`

We load the combined dataframe of all transactions. I notice we are converting the date to datetime even though in our previous processing we have done that. When we save a csv is it saved in string format so we have to convert back to datetime everytime we load into a dataframe?

> -- ye it's stored as a string

We load the rules which is a csv of name, category.

We then parse through each row of the transaction df ensuring case insensitivity by converting descriptions to uppercase.

Okay yeah so it's a nested loop. We match to the first match found which means we need to place the transfer categories at the top of the categories csv.

Explain line 48, the `_` placeholder, what's it's role? What does it represent?

> -- `_` means "I don't care about this value".
> ```python
> for _, rule in rules_df.iterrows():
> ```
> `iterrows()` returns (index, row), but we don't need the index, so we use `_` to ignore it.

In terms of runtime complexity I noticed that we would run through every single pattern for transactions of type income. Would we not reduce the computational load by only iterating through transactions of type expenses? We don't need to map income types because I only have salary.

> -- whoops. forgot about how we had an issue earlier where we were assigning transfers as income. we need to parse through the income to label them correctly as transfers hence why we don't ignore the 'income' labelled transactions.

Everything after this seems fine. We save the categorized csv with categories assigned then print summary stats.

---

## 10/01/26 - Pipeline Deep Dive

Luckily I checked the synthetic data generation script -> kept my bsb and acc number in the generated data.

Gotta be careful!

### Pipeline Script: `run_pipeline.py`

Haven't had much experience with this so worth going over with chat gpt.

```python
sys.path.insert(0, str(Path(__file__).parent))
```

`__file__` is your current path. The `.parent` returns the path of your parent directory, `str()` turns it into a string because `str.path` needs a string. The `0` positions the path at index 0 in paths which prioritises it.

We run the script from `personal-finance/scripts/run_pipeline.py` -> so the parent directory is `/scripts`

`import_module()` loads the name of the python script (why do we omit the `.py`?), because each script wraps the functionality in a... function ... we use `getattr` to pull the named function of each script which successfully does the loading and processing. They all return a df on success. They also return `None` on failure... which prints an error message.

Alright well went on an interesting journey. Every python script is also a module, modules are 'run' on import - variables are defined and logic stored but not run. (`import_module`), but they don't run the processing logic which is why we grab the function and then execute it.

The `if __name__ == "__main__"` is there to avoid importing (computationally expensive potentially) unless the script is run from command line explicitly as opposed to an import.

What exactly does that mean? Will ask chat gpt to provide an example. I'm guessing load script might be imported in another script? Unsure.

> -- chat gpt wisdom
>
> You could write:
> ```python
> # 01_load_anz.py
> process_anz()
> ```
>
> But then this happens:
> ```python
> import_module("01_load_anz")  # BOOM — runs immediately
> ```
>
> Your pipeline needs:
>
> | Step | Purpose |
> |------|---------|
> | `import_module` | Load code & definitions |
> | `getattr` | Select what to run |
> | `func(data_dir)` | Actually run it |
>
> Think of a module like a toolbox.
>
> - Importing it → opening the toolbox
> - Functions → tools inside
> - Calling a function → using a tool
>
> Opening the toolbox doesn't drill the hole.

### Key Takeaway

When you are writing executables always wrap them in a function definition. Minimise expensive overheads at top level so when you import scripts you aren't running them automatically.

Allows for better testing and orchestration, can load modules then run specific scripts that are defined by functions at appropriate times.

---

## 11/01/26 - SQL Analysis

We have cleaned combined categorized data. Let's consider what questions we want answered.

### Question 1: What percentage of my monthly spend is on which category?

In SQL this would be something like:

- Get total monthly spend
- Get total monthly spend grouped by category

```sql
SELECT month(date) as mnth, category,
       SUM(amount) OVER (PARTITION BY month(date)) as ttl_mnth,
       SUM(amount) OVER (PARTITION BY month(date), category) as ttl_mnth_ctgry,
       ttl_mnth_ctgry / ttl_mnth * 100 as pct_spnd
FROM transactions;
```

Would something like that work?

> -- conceptually right, but can't reference things in select which was a question i had. better to split into CTE (common table expression) aka with statement similar to:

```sql
WITH monthly_spend AS (
    SELECT month(date) as month,
           category,
           SUM(amount) as monthly_spend_category
    FROM transactions
    GROUP BY 1, 2
),
monthly_totals AS (
    SELECT month(date) as month,
           SUM(amount) as monthly_total_spend
    FROM transactions
    GROUP BY 1
)
SELECT m.month,
       m.category,
       m.monthly_spend_category,
       mt.monthly_total_spend,
       monthly_spend_category / monthly_total_spend * 100 as pct_spend
FROM monthly_spend m
LEFT JOIN monthly_totals mt ON m.month = mt.month
```

### Question 2: How does my spending fluctuate from month to month?

Would we use a lag function? Haven't really done this much. Could of course just manually do it by looking at `monthly_totals` and perhaps calculating percentage changes from one month to the next.

### Question 3: How much money am I saving on average a month as a percentage of my income?

This would be something like `category, month, sum(amount) as income group by 1,2 where category = 'Income'` then `savings - expenses = ttl_savings / income * 100`

### Other useful metrics to track (suggested by claude)

Top merchants and top categories of spending.

That's pretty straight forward, could filter by month. Would just be:

```sql
SELECT month, category, RANK() OVER (PARTITION BY month, category ORDER BY amount)
FROM monthly_spend
```

You would want to use an intermediate staging table to get the monthly totals first.

### Script 5: `05_load_to_db.py`

In script 5 explain why you created three indexes. Is creating additional indexes necessary? We already have primary key id. I learnt that making multiple indexes are often unnecessary.

For the sample category breakdown, are we finding the total number of transactions and total amount per category across the entire date range?

### Script 6: `06_analyze.py`

Why `strftime('%Y-%m', date) as month`? It's because we want to not pull months from other years too right? But how does it work.

> -- converts to "2025-01" so we group the months specific to a year. don't want jan from 2024 and 2025 counted for example.

When we create `with_lag` we have `ORDER BY month ASC` so that `LAG` gets the previous rows data which makes sense.

In the final select we order `month DESC`. Why do we order by `DESC` instead of `ASC` there?

Is it because we want to show the last three months further ahead in the script? The script I am referencing is here: `for month in df['month'].unique()[:3]`. Could you explain that line please.

> -- `.unique()` returns distinct values in an array and yeah the desc is to get the last 3 months.

With ranked merchants why the choice of `ROW_NUMBER()` over `RANK()`?

> -- row_number doesn't tie (which i know) but due to limit we want exactly 5. fair enough.

`avg_savings_rate = df['savings_rate_pct'].mean()` is placed outside the for loop to do an average across all rows of that column. Is my understanding correct.

Explain defining `current_category = None`. What's the purpose of assigning that to `None`? Do we not have a unique category for each row based on the SQL query in `top_merchants_by_category`?

> -- This is for grouping output display. The query returns rows like:
>
> ```
> Food, Coles, 15, -450
> Food, Woolworths, 12, -380
> Transport, Shell, 8, -200
> Transport, BP, 6, -150
> ```
>
> Output becomes:
>
> ```
> Food:
>   Coles         15x  $-450.00
>   Woolworths    12x  $-380.00
>
> Transport:
>   Shell          8x  $-200.00
>   BP             6x  $-150.00
> ```

---

## 12/01/26 - Dashboard Development

### Synthetic Data Issues

The synthetic data generator is quite unrealistic, it ramped up the overall income to 530k in just over a year, also there are times when data points generated are in consecutive days.

Would need to explicitly prompt claude to pay income on a fortnightly basis.

Also should have omitted the start of jan, it's throwing the monthly totals off because I didn't include a full month of transactions.

The real data source allows better clarity and makes more sense.

### Dashboard Changes

- **Income vs Expenses Over Time:** Turned this into a stacked bar chart
- **Savings Rate by Month:** Omit January 2026 to avoid skewing the saving rates
- **Category Payments:** Categorise payments to "Kok Eng" under housing
- **Spending by Category UX:**
  - Remove "Spending Breakdown - 2026-01" header
  - Have the Category Spending Over Time chart underneath the "Select Month" drop down
  - Change the colour of the Dining Out variable so it's easier to differentiate from Uncategorized
  - Change the legend header from "variable" to "category"
- **Top Merchants by Category:**
  - Order the most expensive merchants at the top of the visualization
  - Instead of 'x' on the outside of the bars, change it to 'transactions'
- **Category Summary:** Rank the min and max transactions by absolute value

### Bug Fixes and Data Cleaning

"Kok Eng" wasn't being categorized because start of Tx is "To Phone" which was being picked up by "Pho" in the Dining Out category. Moved Transfers and Housing to top of categories list for precedence.

Going to assess why my expenses seem to be incorrect. 10k Jan 2025 can't be right.

Give me the breakdown for real expenses in January 2025. It seems unnaturally high and I want to audit this. Everything checks out on audit.

To make things cleaner I'm going to remove January 26 transactions so we have a clean view per month. Parse through our real data sources and ensure we only have transactions from 01-01-2024 to 31-12-25.

### Dashboard Improvements

For the Overview of `app.py` turn Latest Month Expenses into Average Monthly Expenses and Latest Month Income into Average Monthly Income.

Anonymize the name of my banks in the scripts. Probably overkill but we want to minimize any potential personally identifiable information.

Well previous git activity identifies ANZ and bankwest which is just a lesson to think carefully and plan prior to building. I could force push to rewrite. Will leave it as is.

### Future Improvements

One thing is clear as I clean up and expand the category list - we need a better matching algorithm that reduces error. Perhaps matching on only above a certain number of matching characters, prioritizing exact matches. Potential privacy concerns here with more precise categories.

Also travel expenses are lumped in with entertainment.

### Pro Tip

You can make changes to `app.py` and streamlit will serve the changes as you're developing.

---

## 13/01/26 - UV and Dependency Management

Wanted to mess around with playwright-mcp after seeing it's usage in the claude code in action course. This resulted in a lot of frustration dealing with claude code VS extensions inability to recognise virtual environments.

It is easy enough to activate the virtual environment and simply use claude code CLI however stumbled onto uv and think it's a better way, especially if there comes a time when I want AI to just execute commands and am not sure what process is spinning up the LLM.

Including a hook before running any `python` or `pip` command will ensure we are always using `uv add` or `uv run`.

This actually can't be done unfortunately, "Ah, great clarification! You want to prevent Claude Code from executing python or pip install in real-time, not just block git commits.
Unfortunately, there's no native "Claude Code execution hook" system."

### AI Tool Observations

I also noted chat gpt's advice for uv commands was poor. They were most likely using a mixture of sources to predict which sentence to write and getting confused because of the context.

They recommended `uv pip install` which simply installed packages to the conda environment. Once I pushed back on many things and referenced the docs is when it began to spit out the right answers.

It's the same thing, AI is a powerful tool, but garbage in = garbage out. When prompting and there is access to an arcane but extremely dependable source of documentation, I think this is one of it's key strengths.

### Prompting Best Practice

Will need to be more careful with prompting:

> "Use the official documentation located at this url: _____ to plan our approach to doing x,y,z with an output that includes _____. Ultrathink."

Prompts like that will most likely provide far better results.
