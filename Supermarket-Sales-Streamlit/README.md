# Supermarket sales dashboard

A standalone Streamlit app for exploring supermarket transactions. Filter
sales by date, city, branch, product category, customer type, gender, and
payment method. View revenue and customer metrics, compare products and
branches, check data quality, and download the filtered transactions.

## Project structure

```text
.
├── data/
│   └── raw/
│       └── supermarket_sales_500_rows.csv.xlsx
├── sales_dashboard/
│   └── data.py
├── tests/
│   └── test_data.py
├── streamlit_app.py
├── requirements.txt
├── .gitignore
└── README.md
```

The data-cleaning code lives outside the Streamlit entry point so it can be
tested and maintained independently of the interface.

## Requirements

- Python 3.11 or newer
- Dependencies listed in `requirements.txt`

## Set up on Windows

Open PowerShell in the project folder and run:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run the dashboard

From the project folder:

```powershell
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

Streamlit will print a local address (usually `http://localhost:8501`) to open
in your browser.

## Run the tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Data notes

The included Excel workbook has a `Table 1` sheet. It appears to have 497 data
rows, but its first row repeats broken column headers rather than containing a
transaction. Three additional transactions are embedded in the column headers.
The app excludes the malformed row and restores the embedded records, giving
499 transactions in total. Sales are recalculated from quantity multiplied by
unit price; the original workbook values remain available in the data-quality
view.

Keep the workbook in `data/raw/`. The loader resolves its path relative to the
project, so the app can be started from any working directory.

## GitHub

To publish this as its own GitHub project, create an empty repository, then run:

```powershell
git init -b main
git add .
git commit -m "Create supermarket sales dashboard"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

Check the dataset's redistribution terms before making a public repository.
