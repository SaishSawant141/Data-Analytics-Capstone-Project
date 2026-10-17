# Mamaearth Returns & Growth Intelligence Pipeline

This project analyzes Mamaearth's orders data in three parts: 
1. Creating a relational store for order data using SQL
2. A clean analysis layer that finds and quantifies the real patterns, cleaning and exploratory data analysis with visualizations using Python.
3. An AI-generated narrative the regional ops and finance heads can act on without reading a notebook, generated from the resulting metrics.

## Before you begin

Run every command below in **PowerShell from the project root** (the directory containing `README.md`). The Python scripts use paths relative to this directory.

Install Python 3, create a virtual environment, and install the project dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Part 1 requires MySQL Server and the MySQL command-line client to be installed and running as a Windows service. 
Check that PowerShell can find the client:

```powershell
mysql --version
```

## Part 1 — SQL Relational Layer & Reporting

### Create the database

From the project root, create the project database. Replace `root` with your MySQL user if needed. `-p` prompts for the password without putting it in the command or shell history:

```powershell
mysql -u root -p -e "CREATE DATABASE mamaearth_analysis;"
```

### Create tables, load data, and run reports

Start the MySQL client connected to the new database:

```powershell
mysql -u root -p mamaearth_analysis
```

At the `mysql>` prompt, run these commands in order. Start the client from the project root so the source paths resolve:

```sql
SOURCE sql/schema.sql;
SOURCE sql/seed_data.sql;
SOURCE sql/reports.sql;
```

The schema.sql creates the three tables customers, products, and orders, the seed_data.sql script inserts the data into their respective table, and the reports.sql script runs the Part 1 queries. 
Run all three files once in this order against a fresh database. To repeat Part 1, create another empty database and load the files there. Type `exit` at the MySQL prompt to disconnect.

This is the database connection configuration for Part 1: MySQL reads the host, port, user, and database from the command-line options and prompts for the password.
The current Python analysis and narrative scripts do **not** connect to MySQL; they read and write CSV/JSON files, so there is no MySQL `.env` setting or Python database driver used by those scripts.

The results are documented in comments in `sql/reports.sql` for comparison. 

## Part 2 — Python/Pandas Data Wrangling & EDA

Run the cleaning/EDA script first, followed by the visualization script:

```powershell
python analysis\clean_and_eda.py
python analysis\visualize.py
```

`clean_and_eda.py` reads the source CSVs in `data/`, standardizes payment method names, removes duplicate orders, fills missing discount and rating values, calculates the metrics, and writes the cleaned/merged data to `data/orders_clean_merged.csv`. At the end of this script (the end of Part 2's analysis), it writes the reproducible metrics to `narrator/findings.json`.
`visualize.py` reads that cleaned CSV and writes `visualizations/return_rate_by_payment.png` and `visualizations/monthly_revenue_trend.png`.

These values are calculated from the provided CSV files whenever you run the script. The findings.json file is used as input for Part 3. Run Part 2 first to generate updated findings, so Part 3 uses the latest results instead of the existing findings.json file.

## Part 3 — GenAI-Powered Insight Narrator

Run the narrative script from the project root:

```powershell
python narrator\generate_narrative.py
```

It reads `narrator/findings.json` and prints a JSON result containing the narrative and token count (or an error). It also prints a check for five important figures: cleaned revenue `97358.3`, COD return rate `44.4`, highest risk segment return rate `54.5`, duplicate reconciliation difference `2501.9`, and peak-month revenue `20318.9`.

### Online narrative with Gemini

Set `GEMINI_API_KEY` in the current PowerShell session before running the script. Replace the placeholder with your Gemini API key; do not commit or share the key:

```powershell
$env:GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
python narrator\generate_narrative.py
```

The script also loads variables from a `.env` file in the project root. You may put `GEMINI_API_KEY=your-key` in that file instead of setting the PowerShell variable. The Gemini SDK must be installed for this option. The model defaults to `gemini-3.5-flash-lite`; optionally set `GEMINI_MODEL` to use another compatible model. With a key configured, the script sends the findings to Gemini. API, SDK, or request errors are reported in the result.

### Offline narrative with no key

No Gemini key or SDK is needed for offline generation. The script automatically uses its deterministic offline formatter when `GEMINI_API_KEY` is empty or unset. Since a project-root `.env` file is loaded automatically, make sure it does not contain a key when you want the offline path. To explicitly select offline mode for the current PowerShell session (including when `.env` contains a key), set the environment variable to an empty value:

```powershell
$env:GEMINI_API_KEY = ""
python narrator\generate_narrative.py
```

The offline narrative is assembled from the same `findings.json` values and prints the same five accuracy checks.
