# System Architecture

## Overview

ResiPlanAI is a constraint-based scheduling system using OR-Tools CP-SAT solver with Gradio interface.

## Architecture Diagram

```
User (Browser)
    ↓
Gradio Interface (6 tabs)
    ↓
┌────────────────────────────────┐
│ Data Layer                     │
│ - Excel Parser/Writer          │
│ - Intern Models                │
└────────────────────────────────┘
    ↓
┌────────────────────────────────┐
│ Analysis Layer                 │
│ - Bottleneck Analyzer          │
│ - Visual Timeline Generator    │
└────────────────────────────────┘
    ↓
┌────────────────────────────────┐
│ Constraint Engine              │
│ - OR-Tools CP-SAT Solver       │
│ - 6 Constraint Types           │
└────────────────────────────────┘
    ↓
┌────────────────────────────────┐
│ Validation & Export            │
│ - Rule Checker                 │
│ - AI Suggestions (Gemini)      │
│ - Excel + PDF Export           │
└────────────────────────────────┘
```

## Core Modules

### app_scheduler_complete.py
Main application with 6-tab Gradio interface:
1. Dashboard - Data loading
2. God View Matrix - Visual timeline
3. Bottleneck Warnings - Capacity forecast
4. AI Scheduler - Schedule generation
5. Intern Management - CRUD operations
6. Help - Documentation

### scheduler.py
- OR-Tools CP-SAT solver integration
- Constraint relaxation strategy
- Solution extraction
- Time limit management

### constraints.py
- Variable creation: `intern[i]` at `station[s]` in `month[m]`
- Hard constraints (must satisfy)
- Soft constraints (optimization objectives)
- 6 constraint types

### data_handler.py
- Excel parsing (openpyxl)
- Intern data models
- Excel writing with formatting
- Color-coded stations

### validator.py
- Comprehensive rule checking
- AI-powered suggestions (Google Gemini)
- Validation reports

### audit_export.py
- PDF report generation (ReportLab)
- Regulatory-compliant format
- Per-resident compliance checklist

### bottleneck_analyzer.py
- 12-month capacity forecasting
- Critical vs warning classification
- Actionable recommendations

### visual_timeline.py
- Plotly Gantt charts
- Interactive timeline visualization
- Capacity heatmaps

### config.py
- Station definitions (20+ stations)
- Business rules and constraints
- Constants and configuration

## Constraint Types

1. **Basic**: One station per intern per month, immutable past
2. **Duration**: Required months per station
3. **Capacity**: Min/max interns per station per month
4. **Sequence**: Required order (e.g., Basic Sciences → Stage A)
5. **Stage Timing**: Calendar-based (Stage A in June, etc.)
6. **Continuity**: Prefer consecutive assignments (soft)

## Data Flow

1. User uploads Excel → `ExcelParser`
2. Parse → `Intern` objects
3. Create variables → `ConstraintBuilder`
4. Solve → `OR-Tools CP-SAT`
5. Extract solution → Update `Intern.assignments`
6. Validate → `ScheduleValidator`
7. Export → Excel + PDF

## Technology Stack

- **Python 3.8+**: Core language
- **OR-Tools**: Constraint solver
- **Gradio**: Web interface
- **Plotly**: Interactive visualizations
- **ReportLab**: PDF generation
- **OpenPyXL**: Excel manipulation
- **Google Generative AI**: AI suggestions

## Performance

| Operation | Time |
|-----------|------|
| Load Excel | 1-2s |
| Generate God View | <1s |
| Bottleneck Analysis | <1s |
| Schedule Generation | 1-10min (solver) |
| PDF Export | 2-3s |

## Scalability

- **Tested**: Up to 20 interns
- **Recommended**: 5-15 interns
- **Theoretical Limit**: Solver dependent (time limit)

## Security

- API keys in `.env` (not in code)
- Input validation on uploads
- No sensitive data in logs
- HTTPS for production

## Future Enhancements

- Database backend (replace Excel)
- User authentication
- Real-time collaboration
- Mobile app integration (Phase 2)
