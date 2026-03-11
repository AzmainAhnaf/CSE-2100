# CF Analyzer — Desktop App

A modern desktop app to analyze your Codeforces competitive programming performance.

## Setup

1. **Install Python 3.9+** from https://python.org

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app:**
   ```bash
   python main.py
   ```

## Project Structure

```
cf-analyzer/
├── main.py          ← UI (CustomTkinter)
├── backend.py       ← Codeforces API logic
├── requirements.txt ← Dependencies
└── README.md
```

## How It Works

1. Enter a Codeforces handle and click **Analyze →**
2. The app fetches your last 800 submissions via the CF API
3. It also pulls 10 similar-rated users to find trending topics
4. Results are categorized into:
   - **Strong Zone** — topics where you ace ≥75% of problems (min 10 attempts)
   - **Mid Zone** — topics where you're getting there
   - **Weak Zone** — topics where you fail ≥60% of problems (min 10 attempts)
