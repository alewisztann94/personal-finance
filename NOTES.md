# Personal Finance Project Notes

## My writing (Used claude to format for github without changing wording):

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

## 09/01/26

i decided to lean in to the power of claude code, a few interesting things to note:

### Architectural Decision

do we load anz/bankwest data individually then categorise per bank? or do we load both datasets, combine them, then run the categorisation on the combined set.

advantages of individual are: we can isolate transactions at a bank level.

what's the point of this project though, we want an overview of what our overall expenses and income is, and how we are spending. in that case it's better to combine, we don't need granularity at the individual bank level.

### Bug Discovery

I also noticed that we weren't appropriately categorizing some transfers as my real income was far too high. I wish it was that high but I knew something was up.

By simply mentioning to Claude Code that my annual salary is x and that the figures are off based on the date range, the LLM was able to notice that we are mapping 'IBP Payments' to 'BP' (transport) instead of transfers.

### Scope for improvement in the future:
1. Better prompting
2. Make usage of hooks and context management

---

## 09/01/26 - Code Review

Decided to code review and then assess what claude had to say about my relative understanding / questions about decisions.

> `--` are answers from claude code

### Script 1: `01_load_anz.py`

input pattern is a string, we use glob to search through directory to find all anz csv files.

if we don't find any print an error and exit the script by returning None.

print name of all csv files found by glob.

parse through the csv files and turn each one into a df. store the dataframes in an array, and print the row length of each dataframe.

Interesting - we are working with the assumption that all anz csv files contain the same column structure.

combine the dataframes using pd.concat

we convert dates to datetime, I believe the reason is because datetime format allows time series analysis.

convert amounts to floats to avoid weird rounding and well... money is to two decimal points.

we normalise the descriptions by getting rid of whitespaces. i'm not 100% sure if it removes leading and trailing. strings are all converted to uppercase.

> -- removes leading + trailing. leaves middle whitespace.

we add a new column transaction type that uses the amount to determine if it's income or an expense. i'm not confident with this syntax but logically looks fine. income if amount is above zero else it's negative and an expense.

we have a remove duplicates script that i'm unsure of the need. actually we don't want to double up on transactions so fair enough. we might have overlapping input csvs. i'm okay with this.

we then have a bunch of aggregates and summary statistics to validate what we've processed.

the end is a series of smart error handling in case of a corrupted file path, or csv file, or just anything else i guess. what results in an Exception exactly? I recall seeing it in error handling quite often.

> -- exception is a catch all for errors (network issues, permission errors, memory errors, etc. safety net)

### Script 2: `02_load_bankwest.py`

similar to script 1. originally script 1 did not have the ability to process multiple files, but bankwest load script had this functionality. prompted claude to add functionality to script 1 which was done.

loading steps are identical with the exception of read csv which doesn't specifically name headers. this is because the bankwest csv has a header row.
am assuming default parameters for read_csv will automatically include the first row as a header which is why claude left it.
probably more robust to have first row as headers so it is robust to changes to column structure changes. depends on data source of course.

I recall claude had to parse through a few times to recognise that debits were already negative. being specific in prompting how to treat data values would improve performance and save time.

perhaps thinking or planning mode could help here?

> -- yes it would

how would we include hooks into this project?

> -- `.claude/hooks.json` -> used to run linters (parses through file without running to look for dodgy syntax, tests/validations pre/post tool usage. gone through this in the claude code in action course)

handling credit and debit column looks syntactically heavy but we essentially just collapse the debit and credit columns into the amount column.

we are combining the datasets (anz + bankwest) hence why we have to do it.

normalizing description column by stripping whitespaces from narration column and converting to uppercase. same as script 1.

after this the process is pretty much the same as script 1. columns are all converted to the same name as the anz data.

### Script 3: `03_combine.py`

define paths to cleaned files and output file

loading data seems fine -> I am unsure about the else clause for loading the data. why are we declaring

```python
anz_df = pd.DataFrame(columns=["date", "amount", "description", "transaction_type", "source"])
```

when the file is not found? same with the bankwest load.

> -- this is done because concat wont work without two dataframes. therefore we declare an empty one so the concat works.

concatenating the dataframes seems fine. ignore index means that we don't add an id column I believe.

explain the reset_index on line 50 please.

> -- we do this because sorting throws the indexes out of line. we renumber the indexes and drop the index column.

explain the #transaction counts by source section. in particular why do we use the <12 and >6:

```python
print(f"  {source:<12} {count:>6} transactions")
print(f"  {'Total':<12} {len(combined_df):>6} transactions")
```

> -- these numbers in f strings are just used to format.
> - `<12` = left-align in a 12-character-wide field
> - `>6` = right-align in a 6-character-wide field

i also noticed that we return the df at the end and this behaviour is the same for scripts 1 and 2. may i ask if this is standard? do we need to return something because in the scripts we have already saved the csv. do we return the df to successfully exit a script?

> -- Allows interactive use (you can capture it: `df = load_and_process_anz()`)
> Enables chaining scripts together
> Useful for testing/debugging
> Doesn't hurt anything - the CSV is already saved

### Script 4: `04_categorize.py`

we load the combined dataframe of all transactions. i notice we are converting the date to datetime even though in our previous processing we have done that. when we save a csv is it saved in string format so we have to convert back to datetime everytime we load into a dataframe?

> -- ye it's stored as a string

we load the rules which is a csv of name, category.

we then parse through each row of the transaction df ensuring case insensitivity by converting descriptions to uppercase.

okay yeah so it's a nested loop. we match to the first match found which means we need to place the transfer categories at the top of the categories csv.

explain line 48, the `_` placeholder, what's it's role? what does it represent?

> -- `_` means "I don't care about this value".
> ```python
> for _, rule in rules_df.iterrows():
> ```
> `iterrows()` returns (index, row), but we don't need the index, so we use `_` to ignore it.

in terms of runtime complexity i noticed that we would run through every single pattern for transactions of type income. would we not reduce the computational load by only iterating through transactions of type expenses? we don't need to map income types because i only have salary.

> -- whoops. forgot about how we had an issue earlier where we were assigning transfers as income. we need to parse through the income to label them correctly as transfers hence why we don't ignore the 'income' labelled transactions.

everything after this seems fine. we save the categorized csv with categories assigned then print summary stats.

---

## 10/01/26

luckily i checked the synthetic data generation script -> kept my bsb and acc number in the generated data.

gotta be careful!

### Pipeline Script: `run_pipeline.py`

haven't had much experience with this so worth going over with chat gpt.

```python
sys.path.insert(0, str(Path(__file__).parent))
```

`__file__` is your current path. the `.parent` returns the path of your parent directory, `str()` turns it into a string because `str.path` needs a string. the `0` positions the path at index 0 in paths which prioritises it.

we run the script from `personal-finance/scripts/run_pipeline.py` -> so the parent directory is `/scripts`

`import_module()` loads the name of the python script (why do we omit the .py?), because each script wraps the functionality in a... function ... we use `getattr` to pull the named function of each script which successfully does the loading and processing. they all return a df on success. they also return None on failure... which prints an error message.

alright well went on an interesting journey. every python script is also a module, modules are 'run' on import -variables are defined and logic stored but not run. (`import_module`), but they don't run the processing logic which is why we grab the function and then execute it.

the `if __name__ == "__main__"` is there to avoid importing (computationally expensive potentially) unless the script is run from command line explicitly as opposed to an import.

what exactly does that mean? will ask chat gpt to provide an example. i'm guessing load script might be imported in another script? unsure.

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

---

**Takeaway:** when you are writing executables always wrap them in a function definition. minimise expensive overheads at top level so when you import scripts you aren't running them automatically.

allows for better testing and orchestration, can load modules then run specific scripts that are defined by functions at appropriate times.

11/01/26

We have cleaned combined categorized data. Let's consider what questions we want answered.

What percentage of my monthly spend is on which category?
in SQL this would be something like:

get total monthly spend
get total monthly spend grouped by category


SEL month(date) as mnth, category, sum(amount) OVER (PARTITION BY month(date)) as ttl_mnth, sum(amount) OVER (PARTITION BY month(date), category) as ttl_mnth_ctgry,
ttl_mnth_ctgry / ttl_mnth * 100 as pct_spnd
FROM transactions; 

would something like that work? 
--conceptually right, but can't reference things in select which was a question i had. better to split into CTE (common table expression) aka with statement similar to:

WITH monthly_spend AS (
SEL month(date) as month
, category 
, sum(amount) as monthly_spend_category
FROM transactions
GROUP BY 1,2
) ,
monthly_totals AS (
SEL month(date) as month
, sum(amount) as monthly_total_spend
FROM transactions
GROUP BY 1
)
SEL m.month
, m.category
, m.monthly_spend_category
, mt.monthly_total_spend
, monthly_spend_category / monthly_total_spend * 100 as pct_spend
FROM monthly_spend m
LEFT JOIN monthly_totals mt
ON m.month = mt.month

How does my spending fluctuate from month to month?
would we use a lag function? haven't really done this much.
could of course just manually do it by looking at monthly_totals and perhaps calculating percentage changes from one month to the next.

How much money am I saving on average a month as a percentage of my income?
this would be something like category, month, sum(amount) as income group by 1,2 where category = 'Income' 
then savings - expenses = ttl_savings /  income * 100

other useful metrics to track suggested by claude
top merchants and top categories of spending

that's pretty straight forward, could filter by month. 
would just be:
sel month,category, RANK() OVER (partition by month, category ORDER BY amount)
from monthly_spend

you would want to use an intermediate staging table to get the monthly totals first

script 5 load to db

in script 5 explain why you created three indexes.
is creating additional indexes necessary? we already have primary key id.
i learnt that making multiple indexes are often unnecessary. 

for the sample category breakdown, are we finding the total number of transactions and total amount per category across the entire date range?

please update the readme to mimic the progress we've made since the current copy.

script 6 

why  strftime('%Y-%m', date) as month
its because we want to not pull months from other years too right? but how does it work.
-- converts to "2025-01" so we group the months specific to a year. don't want jan from 2024 and 2025 counted for example. 

when we create with_lag we have order by month asc so that LAG gets the previous rows data which makes sense.

in the final select we order month DESC. why do we order by DESC instead of ASC there?

is it because we want to show the last three months further ahead in the script?
the script i am referencing is here: for month in df['month'].unique()[:3]
could you explain that line please.  
-- .unique() returns distinct values in an array and yeah the desc is to get the last 3 months.
 
with ranked merchants why the choice of row_number() over rank()?
-- row_number doesn't tie (which i know) but due to limit we want exactly 5. fair enough. 

avg_savings_rate = df['savings_rate_pct'].mean() is placed outside the for loop to do an average across all rows of that column. is my understanding correct. 

explain defining current_category = None
what's the purpose of assigning that to None? 
do we not have a unique category for each row based on the SQL query in top_merchants_by_category?

--
This is for grouping output display. The query returns rows like:

Food, Coles, 15, -450
Food, Woolworths, 12, -380
Transport, Shell, 8, -200
Transport, BP, 6, -150

Output becomes:

Food:
  Coles         15x  $-450.00
  Woolworths    12x  $-380.00

Transport:
  Shell          8x  $-200.00
  BP             6x  $-150.00
--

12/01/26

app.py / overview

the synthetic data generator is quite unrealistic, it ramped up the overall income to 530k in just over a year, also there are times when data points generated are in consecutive days.

would need to explicitly prompt claude to pay income on a fortnightly basis.

also should have omitted the start of jan, it's throwing the monthly totals off because i didn't include a full month of transactions.

the real data source allows better clarity and makes more sense. 

changes:

income vs expenses over time: let's turn this into a stacked bar chart.

savings rate by month: let's omit January 2026 to avoid skewing the saving rates.

Categorise payments to "Kok Eng" under housing.

Clean up the UX for Spending by Category. Remove "Spending Breakdown - 2026-01" header, and have the Category Spending Over Time chart underneath the "Select Month" drop down.
Change the colour of the Dining Out variable so it's easier to differentiate from Uncategorized.

Change the legend header from "variable" to "category".

For the Top Merchants by Category visualization, order the most expensive merchants at the top of the visualization. Instead of 'x' on the outside of the bars, change it to 'transactions'.

"Kok Eng" wasn't being categorized because start of Tx is "To Phone" which was being picked up by "Pho" in the Dining Out category. Moved Transfers and Housing to top of categories list for precedence. 

Going to assess why my expenses seem to be incorrect. 10k Jan 2025 can't be right. 

Also you can make changes to app.py and streamlit will serve the changes as you're developing. 

For category summary rank the min and max transactions by absolute value. 

give me the breakdown for real expenses in January 2025. It seems unnaturally high and i want to audit this. 

everything checks out on audit. 

to make things cleaner i'm going to remove January 26 transactions so we have a clean view per month. 

parse through our real data sources and ensure we only have transactions from 01-01-2024 to 31-12-25.

For the Overview of app.py turn Latest Month Expenses into Average Monthly Expenses and Latest Month Income into Average Monthly Income. 

anonymize the name of my banks in the scripts. probably overkill but we want to minimize any potential personally identifiable information.