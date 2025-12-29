# Quick Start Guide

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Create `.env` file:
```
GOOGLE_API_KEY=your_api_key_here
```

Get key from: https://makersuite.google.com/app/apikey

## Run

```bash
python app.py
```

Or use: `run_scheduler.bat`

Open: **http://localhost:7860**

## Usage

### 1. Load Data
- Dashboard tab → Upload Excel or download sample template
- Click "Load Data"

### 2. View Timeline
- God View Matrix tab → See visual 72-month timeline
- Review capacity heatmap

### 3. Check Bottlenecks
- Bottleneck Warnings tab → See 12-month forecast
- Review critical issues (🔴) and warnings (🟡)

### 4. Generate Schedule
- AI Scheduler tab → Set time limit → Click "Generate"
- Download Excel + PDF audit report

### 5. Manage Interns
- Intern Management tab → Add/delete/view residents

## Excel Format

| Month    | Intern 1    | Intern 2    |
|----------|-------------|-------------|
| 2023-01  | Orientation | Orientation |
| 2023-02  | Maternity   | Maternity   |
| 2023-03  | HRP A       | HRP B       |

Add metadata at bottom (rows 82-84):
- Start Date: 2023-01-01
- Model: A or B
- Department: A or B

## Troubleshooting

**Import errors:**
```bash
pip install -r requirements.txt
```

**Plots not showing:**
```bash
pip install plotly kaleido reportlab
```

**API key error:**
- App works without it, just no AI suggestions
- Create `.env` file with GOOGLE_API_KEY

## Next Steps

1. Load sample data and test
2. Generate your first schedule
3. Review validation reports
4. Export PDF for audit

For details: See ARCHITECTURE.md and DEPLOYMENT.md
