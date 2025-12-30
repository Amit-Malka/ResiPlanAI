# ResiPlanAI - Residency Program Agent

AI-powered scheduling system for Obstetrics & Gynecology residency programs.

## Features

- **Automated Scheduling**: OR-Tools constraint solver generates 72/66-month compliant schedules
- **God View Matrix**: Interactive visual timeline showing all resident schedules
- **Bottleneck Warnings**: 12-month capacity forecast with predictive alerts
- **PDF Audit Export**: Regulatory-compliant reports ready for submission
- **Management Dashboard**: Add, delete, view residents and track capacity
- **AI Validation**: Google Generative AI provides suggestions for constraint violations
- **Excel Editing**: Direct in-browser editing of schedules (Streamlit)
- **Hebrew Translation**: Automatic translation of Hebrew names and stations
- **AI Copilot**: Context-aware chat assistant for scheduling advice (NEW)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up Google API key (optional)
echo GOOGLE_API_KEY=your_key_here > .env
```

### UI Options

**Option 1: Streamlit Dashboard (Recommended)**
```bash
# Modern, professional dashboard with interactive editing
streamlit run dashboard.py
# Or use: run_dashboard.bat
```
Open: http://localhost:8501

**Option 2: Gradio Interface (Classic)**
```bash
# Simple, fast interface
python app.py
# Or use: run.bat
```
Open: http://localhost:7860

See **STREAMLIT_GUIDE.md** for detailed dashboard features.

## Project Structure

```
ResiPlanAI/
├── app.py                  # Gradio application launcher
├── dashboard.py            # Streamlit dashboard (NEW)
├── run.bat                 # Gradio launcher
├── run_dashboard.bat       # Streamlit launcher (NEW)
├── requirements.txt        # Dependencies
├── README.md              # This file
├── STREAMLIT_GUIDE.md     # Dashboard guide (NEW)
│
├── src/                   # Source code
│   ├── app_scheduler_complete.py
│   ├── scheduler.py
│   ├── constraints.py
│   ├── data_handler.py
│   ├── validator.py
│   ├── config.py
│   ├── audit_export.py
│   ├── bottleneck_analyzer.py
│   ├── visual_timeline.py
│   └── translation_config.py  # Hebrew translation (NEW)
│
├── docs/                  # Documentation
│   ├── QUICKSTART.md
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT.md
│   └── PROJECT_SUMMARY.md
│
├── tests/                 # Tests
│   └── test_scheduler.py
│
├── scripts/               # Utility scripts
│   ├── run_scheduler.bat
│   └── run_tests.bat
│
└── data/                  # Data files
    └── (Excel files)
```

## Which UI Should I Use?

| Feature | Streamlit Dashboard | Gradio Interface |
|---------|-------------------|------------------|
| **Look & Feel** | ⭐⭐⭐ Modern, professional | ⭐⭐ Simple, functional |
| **Excel Editing** | ✅ Direct cell editing | ❌ View only |
| **Interactivity** | ⭐⭐⭐ High | ⭐⭐ Medium |
| **Mobile Friendly** | ✅ Yes | ⚠️ Limited |
| **Setup Time** | 2 min | 1 min |
| **Recommended For** | Production, demos | Testing, quick runs |

**TL;DR**: Use **Streamlit** for best experience, **Gradio** for quick testing.

## Usage

### 1. Load Data
- Upload Excel file with resident data
- Or download sample template

### 2. View Timeline
- God View Matrix shows 72-month visual grid
- Capacity heatmap displays future utilization

### 3. Check Bottlenecks
- 12-month forecast identifies capacity issues
- Critical and warning alerts with recommendations

### 4. Generate Schedule
- AI solver handles all constraints
- Download Excel + PDF audit report

### 5. Manage Residents (Streamlit Only)
- Add/delete residents manually
- View individual schedules
- Edit schedules directly in the grid

## Constraints Enforced

- Station durations (HRP: 6mo, Birth: 6mo, etc.)
- Capacity limits per station per month
- Sequential dependencies (Basic Sciences → Stage A)
- Stage A timing (June only, 3-4.5 years from start)
- Stage B timing (November/March, last year)
- Immutable past/current months
- Department assignments (A or B)

## Documentation

- **docs/QUICKSTART.md** - Detailed setup and usage guide
- **docs/ARCHITECTURE.md** - Technical implementation details
- **docs/DEPLOYMENT.md** - Production deployment guide
- **docs/PROJECT_SUMMARY.md** - Quick overview

## Requirements

- Python 3.8+
- Google Generative AI API key (optional, for AI suggestions)

## Success Metrics

- **<30 min** schedule generation
- **100%** constraint compliance
- **12 months** predictive capacity analysis
- **PDF** audit-ready reports

## License

MIT
