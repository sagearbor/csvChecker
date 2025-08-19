# Data Quality Checker

A Python project for automated data quality checks on CSV files, with a **Streamlit** frontend to make results easy to inspect.  

The tool performs:
- **Row count checks** (e.g. ensuring non‑empty files, minimum rows).
- **Data type checks** (validating column types against expected schema).
- **Value range / allowed set checks** (numeric ranges & categorical values).
- **Summary + Detailed Reporting** via Streamlit dashboard:
  - Summary section with overall validation results and quick metrics.
  - Detailed section listing problematic rows and issues.

---

## 📦 Project Structure
data_quality_checker/
│
├── src/
│ ├── init.py
│ ├── data_loader.py # CSV loader
│ ├── checks.py # Row count, type check, range/set check
│ ├── quality_pipeline.py # Orchestration of checks
│
├── tests/
│ ├── init.py
│ ├── test_data_loader.py
│ ├── test_checks.py
│ ├── test_quality_pipeline.py
│ ├── test_app.py
│
├── app.py # Streamlit UI
├── requirements.txt # Dependencies
├── developer_checklist.yaml # Task breakdown & progress
└── README.md


Collapse

Run
Save
Copy
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18

---

## 🚀 Installation

Clone the repository and set up a virtual environment:

```bash
git clone https://github.com/your-org/data_quality_checker.git
cd data_quality_checker

# Create virtual env
python -m venv venv
source venv/bin/activate  # (Linux/Mac)
venv\Scripts\activate     # (Windows)

# Install dependencies
pip install -r requirements.txt
Dependencies include:

pandas
streamlit
pytest
🛠️ Usage
Run the Streamlit app (interactive dashboard):
bash

Collapse
Save
Copy
1
streamlit run app.py
Upload a CSV file from the browser.
View Results:
Summary metrics (row count, number of issues).
Detailed problem rows displayed in a table.
(Optional) Download cleaned vs issues-only data.
🧪 Running Tests
All tests use pytest. Mock CSV files and inline DataFrames are used to allow development without real data.

bash

Collapse
Save
Copy
1
pytest -v
Test coverage includes:

CSV loading (valid & malformed files).
Row count checks.
Data type validation.
Value range/set validation.
Integration pipeline (run_quality_checks).
Streamlit app logic (mocking Streamlit API).
🧩 Example Schema & Rules
The quality checks require configuration (schema and rules). Example:

python

Collapse

Run
Save
Copy
1
2
3
4
5
6
7
8
9
10
⌄
⌄
schema = {
    "id": "int",
    "age": "int",
    "country": "str"
}

rules = {
    "age": {"min": 0, "max": 120},
    "country": {"allowed": ["USA", "CAN", "MEX"]}
}
Pass these objects to the pipeline or configure them in the app.

📋 Development Roadmap
See developer_checklist.yaml for a detailed plan, showing tasks (ToDo/InProgress/Done), parallelizable paths, and test coverage points.
