# ResiPlanAI Streamlit Dashboard Guide

## 🚀 Quick Start

### Installation

1. **Install Streamlit** (if not already installed):
```bash
pip install streamlit
```

Or update all dependencies:
```bash
pip install -r requirements.txt
```

### Running the Dashboard

**Option 1: Using the launcher script (Windows)**
```bash
run_dashboard.bat
```

**Option 2: Direct command**
```bash
streamlit run dashboard.py
```

The dashboard will open automatically in your default browser at `http://localhost:8501`

---

## 📊 Dashboard Features

### Sidebar Configuration
- **📂 File Upload**: Upload your Excel file with intern schedules
- **📅 Current Date**: Set the simulation date
- **⏱️ Max Runtime**: Adjust AI scheduler timeout (60-600 seconds)
- **📥 Load Data**: Parse and load the Excel file
- **🚀 Run AI Scheduler**: Generate optimized schedules
- **🤖 ResiPlan Copilot**: AI chat assistant for scheduling advice (NEW!)

### Tab 1: God View (Timeline)
**Visual 72-Month Overview**
- Interactive Gantt chart showing all resident schedules
- Color-coded by station/department
- Zoom, pan, and hover for details
- Capacity usage bar chart

### Tab 2: Interactive Editor
**Manual Schedule Editing**
- Excel-like grid view of all schedules
- Click any cell to edit assignments
- Changes are applied when you click "Apply Edits"
- Perfect for quick manual adjustments

### Tab 3: Analytics & Bottlenecks
**Predictive Analysis**
- Future bottleneck detection (12 months ahead)
- Critical issues highlighted in red
- Capacity usage metrics
- Actionable recommendations
- Detailed bottleneck report table

---

## 🎯 Typical Workflow

### 1. Load Your Data
1. Click "Browse files" in the sidebar
2. Select your Excel file
3. Adjust the current date if needed
4. Click "Load Data"
5. Check the metrics in the sidebar (Total Interns, Model A/B counts)

### 2. View Current Schedule
- Go to **Tab 1 (God View)** to see the visual timeline
- Or go to **Tab 2 (Interactive Editor)** to see the grid view

### 3. Generate AI Schedule
1. Set the max runtime (default 300 seconds is good)
2. Click "🚀 Run AI Scheduler"
3. Wait for the optimizer to run
4. Success message + balloons animation when complete

### 4. Review Results
- **Tab 1**: See the updated Gantt chart
- **Tab 3**: Check for bottlenecks and warnings
- **Tab 2**: Make manual adjustments if needed

### 5. Manual Edits (Optional)
1. Go to **Tab 2 (Interactive Editor)**
2. Click on any cell to change the station assignment
3. Click "💾 Apply Edits" to save your changes
4. The visualizations will update automatically

### 6. Use AI Copilot (NEW!)
1. Scroll to bottom of sidebar
2. Find **"🤖 ResiPlan Copilot"** section
3. Type questions like:
   - "What bottlenecks do I have?"
   - "How can I optimize my schedule?"
   - "Explain Stage A constraints"
4. Get instant context-aware advice
5. Clear chat with 🗑️ button if needed

---

## 🔧 Technical Details

### Excel File Format
The dashboard expects the same format as the Gradio version:
- **Row 1**: Intern names (starting from column B)
- **Rows 2+**: Monthly assignments
- **Rows 82-84** (optional): Metadata (Start Date, Model, Department)

### Hebrew Translation
The dashboard automatically translates Hebrew text in Excel files:
- Intern names
- Station names
- Department names

Supported via:
1. Precomputed medical terms (fast, offline)
2. Google Translate API (fallback, requires internet)

### Session State
The dashboard uses Streamlit's session state to persist data:
- `st.session_state.interns`: List of Intern objects
- `st.session_state.current_date`: Simulation date
- `st.session_state.schedule_generated`: Whether scheduler has run

### Performance
- File upload: Instant
- Data parsing: 1-2 seconds
- AI scheduler: 60-600 seconds (depending on complexity)
- Visualizations: 2-5 seconds

---

## 🎨 UI Customization

### Color Scheme
The dashboard uses a purple gradient header (`#667eea` to `#764ba2`). To change:
- Edit the CSS in `dashboard.py` under `st.markdown("""<style>...`

### Layout
The dashboard uses `layout="wide"` for maximum screen usage. To change:
- Modify `st.set_page_config(layout="wide")` to `layout="centered"`

---

## ⚠️ Troubleshooting

### "Module not found" errors
```bash
pip install streamlit plotly pandas openpyxl
```

### Dashboard won't start
- Check that you're in the correct directory
- Ensure Python 3.8+ is installed
- Try: `python -m streamlit run dashboard.py`

### Excel file won't load
- Verify the file format matches the expected structure
- Check that intern names are in row 1, column B onwards
- Ensure the file is not corrupted

### Scheduler takes too long
- Reduce the number of interns (for testing)
- Lower the time limit slider
- Check that constraints are not over-constrained

### Edits not saving
- Make sure you click "💾 Apply Edits" after changing cells
- Check that station names match the config exactly
- Refresh the page if the UI becomes unresponsive

---

## 📝 Comparison: Streamlit vs Gradio

| Feature | Streamlit | Gradio |
|---------|-----------|--------|
| **UI Style** | Modern dashboard | Simple tabs |
| **Interactivity** | High (widgets, charts) | Medium |
| **Excel Editing** | ✅ `st.data_editor` | ❌ View only |
| **Visualizations** | ✅ Native Plotly | ✅ Plotly support |
| **Real-time Updates** | ✅ Instant | ✅ Instant |
| **Mobile Friendly** | ✅ Yes | ⚠️ Limited |
| **Learning Curve** | Medium | Easy |

---

## 🔮 Future Enhancements

Potential additions to the dashboard:
- [ ] Export to PDF directly from UI
- [ ] Comparison mode (before/after scheduling)
- [ ] Undo/Redo for manual edits
- [ ] Dark mode toggle
- [ ] Multi-language support (Hebrew UI labels)
- [ ] Real-time constraint validation

---

## 📞 Support

For issues or questions:
1. Check this guide first
2. Review the error messages in the console
3. Verify your Excel file format
4. Check that all dependencies are installed

---

**Enjoy your new professional dashboard! 🎉**

