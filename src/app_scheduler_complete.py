import gradio as gr
from datetime import datetime, timedelta
import os
import sys
import tempfile

# Add src to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from data_handler import ExcelParser, ExcelWriter, Intern
from scheduler import SchedulerWithRelaxation
from validator import ScheduleValidator
from audit_export import generate_quick_audit_report
from bottleneck_analyzer import BottleneckAnalyzer
from visual_timeline import TimelineVisualizer
import config

# Global state
interns_data = []
fixed_anchors = {}  # {intern_idx: {month_idx: station_key}}
capacity_tracking = {}

def load_interns_from_excel(excel_file, current_month_str):
    """Load interns from Excel file."""
    global interns_data
    
    if excel_file is None:
        return "Please upload an Excel file", None, None, None
    
    try:
        current_date = datetime.strptime(current_month_str, "%Y-%m")
        parser = ExcelParser()
        interns_data = parser.parse_excel(excel_file, current_date)
        
        intern_list = []
        for intern in interns_data:
            intern_list.append([
                intern.name,
                intern.model,
                intern.department,
                intern.start_date.strftime("%Y-%m"),
                len(intern.assignments),
                intern.total_months,
                "Active" if len(intern.assignments) < intern.total_months else "Completed"
            ])
        
        update_capacity_tracking()
        
        # Create visualizations
        try:
            visualizer = TimelineVisualizer(interns_data)
            timeline_fig = visualizer.create_god_view_matrix()
        except Exception as e:
            print(f"Warning: Could not create timeline visualization: {e}")
            timeline_fig = None
        
        # Run bottleneck analysis
        try:
            analyzer = BottleneckAnalyzer(interns_data, lookahead_months=12)
            analysis = analyzer.analyze()
            bottleneck_summary = _format_bottleneck_analysis(analysis)
        except Exception as e:
            print(f"Warning: Could not run bottleneck analysis: {e}")
            bottleneck_summary = "Bottleneck analysis unavailable"
        
        return (
            f"✓ Loaded {len(interns_data)} interns successfully",
            intern_list,
            get_capacity_display(),
            timeline_fig,
            bottleneck_summary
        )
        
    except Exception as e:
        import traceback
        error_msg = f"Error loading file: {str(e)}\n\n"
        error_msg += "Please check:\n"
        error_msg += "1. Excel file has intern names in row 1 (starting column B)\n"
        error_msg += "2. Monthly assignments are in rows below\n"
        error_msg += "3. File is not corrupted\n\n"
        error_msg += f"Details:\n{traceback.format_exc()}"
        return error_msg, None, None, None, ""


def _format_bottleneck_analysis(analysis):
    """Format bottleneck analysis for display."""
    lines = ["BOTTLENECK ANALYSIS", "="*60, ""]
    lines.append(f"Analyzed: Next {analysis['analyzed_months']} months")
    lines.append(f"Bottlenecks Found: {analysis['bottlenecks_found']}")
    lines.append(f"Critical Issues: {analysis['critical_count']}")
    lines.append(f"Warnings: {analysis['warning_count']}")
    lines.append("")
    
    if analysis['bottlenecks']:
        lines.append("IDENTIFIED BOTTLENECKS:")
        lines.append("")
        
        for bottleneck in analysis['bottlenecks'][:10]:  # Show first 10
            month = bottleneck['month']
            lines.append(f"Month {month + 1}:")
            for issue in bottleneck['issues']:
                severity_icon = "🔴" if issue['severity'] == 'critical' else "🟡"
                lines.append(f"  {severity_icon} {issue['station']}: {issue['type']}")
                if 'deficit' in issue:
                    lines.append(f"      Needs {issue['deficit']} more interns")
                elif 'excess' in issue:
                    lines.append(f"      {issue['excess']} interns over capacity")
            lines.append("")
    
    lines.append("RECOMMENDATIONS:")
    for rec in analysis['recommendations']:
        lines.append(f"  • {rec}")
    
    return "\n".join(lines)


def update_capacity_tracking():
    """Update capacity tracking for all stations."""
    global capacity_tracking
    capacity_tracking = {}
    
    if not interns_data:
        return
    
    max_months = max(intern.total_months for intern in interns_data)
    
    for month_idx in range(max_months):
        capacity_tracking[month_idx] = {}
        
        for intern in interns_data:
            if month_idx < intern.total_months and month_idx in intern.assignments:
                station_key = intern.assignments[month_idx]
                
                if station_key not in capacity_tracking[month_idx]:
                    capacity_tracking[month_idx][station_key] = 0
                capacity_tracking[month_idx][station_key] += 1


def get_capacity_display():
    """Get capacity tracking display for current month."""
    if not capacity_tracking:
        return [["No data", "0", "0", "0", "OK"]]
    
    current_month_idx = max(capacity_tracking.keys()) if capacity_tracking else 0
    current_data = capacity_tracking.get(current_month_idx, {})
    
    display_data = []
    all_stations = config.STATIONS_MODEL_A
    
    for station_key, station in all_stations.items():
        current_count = current_data.get(station_key, 0)
        
        # Determine status
        if current_count < station.min_interns:
            status = "🔴 Under"
        elif current_count > station.max_interns:
            status = "🟠 Over"
        else:
            status = "🟢 OK"
        
        display_data.append([
            station.name,
            str(current_count),
            str(station.min_interns),
            str(station.max_interns),
            status
        ])
    
    return display_data


def generate_schedule(excel_file, current_month_str, time_limit):
    """Generate schedule using OR-Tools solver."""
    
    if not interns_data:
        return None, "Please load interns first", "", "", None, None, None, None
    
    try:
        current_date = datetime.strptime(current_month_str, "%Y-%m")
        start_month = min(intern.start_date for intern in interns_data)
        
        status_msg = f"Scheduling {len(interns_data)} interns...\n\n"
        
        scheduler = SchedulerWithRelaxation(
            interns=interns_data,
            current_date=current_date,
            start_month=start_month,
            time_limit_seconds=int(time_limit)
        )
        
        solution = scheduler.solve_with_relaxation()
        
        status_msg += f"Status: {solution.status}\n"
        status_msg += f"Time: {solution.solve_time:.2f}s\n\n"
        
        if not solution.is_feasible:
            return None, status_msg + "❌ No solution found", "", "", None, None, None, None
        
        # Validate
        validator = ScheduleValidator(interns_data, use_ai=True)
        validation_result = validator.validate()
        
        validation_summary = validation_result.get_summary()
        status_msg += validation_summary + "\n"
        
        ai_suggestions = ""
        if not validation_result.is_valid:
            ai_suggestions = validator.get_ai_suggestions(validation_result)
        
        # Write Excel
        excel_path = tempfile.NamedTemporaryFile(
            delete=False, 
            suffix='.xlsx', 
            prefix='schedule_'
        ).name
        
        writer = ExcelWriter()
        writer.write_schedule(interns_data, excel_path, start_month)
        
        # Generate PDF Audit Report
        pdf_path = tempfile.NamedTemporaryFile(
            delete=False,
            suffix='.pdf',
            prefix='audit_report_'
        ).name
        
        generate_quick_audit_report(interns_data, pdf_path)
        
        # Update visualizations
        update_capacity_tracking()
        
        visualizer = TimelineVisualizer(interns_data)
        timeline_fig = visualizer.create_god_view_matrix()
        heatmap_fig = visualizer.create_capacity_heatmap(lookahead_months=12)
        
        # Bottleneck analysis
        analyzer = BottleneckAnalyzer(interns_data, lookahead_months=12)
        analysis = analyzer.analyze()
        bottleneck_summary = _format_bottleneck_analysis(analysis)
        
        # Update intern list
        intern_list = []
        for intern in interns_data:
            intern_list.append([
                intern.name,
                intern.model,
                intern.department,
                intern.start_date.strftime("%Y-%m"),
                len(intern.assignments),
                intern.total_months,
                "Active" if len(intern.assignments) < intern.total_months else "Completed"
            ])
        
        summary = scheduler.get_solution_summary()
        summary_text = _format_summary(summary)
        
        return (
            excel_path,
            status_msg,
            summary_text,
            ai_suggestions,
            intern_list,
            get_capacity_display(),
            timeline_fig,
            pdf_path,
            heatmap_fig,
            bottleneck_summary
        )
        
    except Exception as e:
        import traceback
        error_msg = f"Error: {str(e)}\n\n{traceback.format_exc()}"
        return None, error_msg, "", "", None, None, None, None, None, ""


def _format_summary(summary):
    """Format solution summary."""
    lines = [
        "SOLUTION SUMMARY",
        "="*50,
        f"Status: {summary['status']}",
        f"Time: {summary['solve_time']:.2f}s",
        f"Interns: {summary['num_interns']}",
        ""
    ]
    
    for intern_summary in summary['intern_summaries']:
        lines.append(f"\n{intern_summary['name']}")
        lines.append(f"  Model: {intern_summary['model']}")
        lines.append(f"  Department: {intern_summary['department']}")
        lines.append(f"  Assigned: {intern_summary['assigned_months']}/{intern_summary['total_months']}")
        lines.append("  Stations:")
        
        for station_name, months in sorted(intern_summary['stations'].items()):
            lines.append(f"    - {station_name}: {months} mo")
    
    return "\n".join(lines)


def add_intern(name, model, department, start_date_str):
    """Add a new intern manually."""
    global interns_data
    
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m")
        
        new_intern = Intern(
            name=name,
            start_date=start_date,
            model=model,
            department=department,
            current_month_index=0,
            total_months=72 if model == "A" else 66
        )
        
        interns_data.append(new_intern)
        
        intern_list = []
        for intern in interns_data:
            intern_list.append([
                intern.name,
                intern.model,
                intern.department,
                intern.start_date.strftime("%Y-%m"),
                len(intern.assignments),
                intern.total_months,
                "Active" if len(intern.assignments) < intern.total_months else "Completed"
            ])
        
        return f"✓ Added {name} successfully", intern_list
        
    except Exception as e:
        return f"Error adding intern: {str(e)}", None


def delete_intern(intern_name):
    """Delete an intern."""
    global interns_data
    
    interns_data = [i for i in interns_data if i.name != intern_name]
    
    intern_list = []
    for intern in interns_data:
        intern_list.append([
            intern.name,
            intern.model,
            intern.department,
            intern.start_date.strftime("%Y-%m"),
            len(intern.assignments),
            intern.total_months,
            "Active" if len(intern.assignments) < intern.total_months else "Completed"
        ])
    
    return f"✓ Deleted {intern_name}", intern_list


def get_intern_details(intern_name):
    """Get detailed schedule for an intern."""
    intern = next((i for i in interns_data if i.name == intern_name), None)
    
    if not intern:
        return "Intern not found", []
    
    stations = config.STATIONS_MODEL_A if intern.model == 'A' else config.STATIONS_MODEL_B
    
    schedule_data = []
    for month_idx in sorted(intern.assignments.keys()):
        station_key = intern.assignments[month_idx]
        station_name = stations[station_key].name if station_key in stations else station_key
        month_date = intern.start_date + timedelta(days=30 * month_idx)
        
        schedule_data.append([
            month_date.strftime("%Y-%m"),
            station_name,
            "✓" if month_idx <= intern.current_month_index else "Pending"
        ])
    
    info = f"""
**Intern**: {intern.name}
**Model**: {intern.model} ({intern.total_months} months)
**Department**: {intern.department}
**Start Date**: {intern.start_date.strftime("%Y-%m")}
**Progress**: {len(intern.assignments)}/{intern.total_months} months assigned
"""
    
    return info, schedule_data


def create_sample_file():
    """Create sample Excel template."""
    output_path = tempfile.NamedTemporaryFile(
        delete=False, 
        suffix='.xlsx', 
        prefix='sample_internship_'
    ).name
    
    writer = ExcelWriter()
    writer.create_sample_excel(output_path)
    
    return output_path


# Custom CSS
custom_css = """
.gradio-container {
    font-family: 'Inter', sans-serif;
}

.header-section {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 2rem;
    border-radius: 10px;
    margin-bottom: 2rem;
    text-align: center;
}

.stat-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
"""

# Build application
with gr.Blocks(css=custom_css, title="Residency Program Agent - Complete") as app:
    
    gr.Markdown("""
    <div class="header-section">
        <h1>🏥 Residency Program Agent</h1>
        <p>Complete Scheduler with God View, Bottleneck Analysis & Audit Export</p>
    </div>
    """)
    
    with gr.Tabs() as tabs:
        
        # Dashboard Tab
        with gr.Tab("📊 Dashboard & Data Loading"):
            gr.Markdown("### Load Residency Data")
            
            with gr.Row():
                with gr.Column():
                    excel_input = gr.File(
                        label="Upload Excel File",
                        file_types=[".xlsx", ".xls"],
                        type="filepath"
                    )
                    current_month = gr.Textbox(
                        label="Current Month (YYYY-MM)",
                        value=datetime.now().strftime("%Y-%m")
                    )
                    load_btn = gr.Button("📂 Load Data", variant="primary")
                    sample_btn = gr.Button("📄 Download Sample Template")
                    sample_output = gr.File(label="Sample Template", visible=False)
                
                with gr.Column():
                    load_status = gr.Textbox(label="Status", lines=3)
            
            gr.Markdown("### Current Interns")
            intern_table = gr.Dataframe(
                headers=["Name", "Model", "Dept", "Start Date", "Assigned", "Total", "Status"],
                datatype=["str", "str", "str", "str", "number", "number", "str"],
                label="Interns Overview"
            )
            
            gr.Markdown("### Station Capacity (Current Month)")
            capacity_table = gr.Dataframe(
                headers=["Station", "Current", "Min", "Max", "Status"],
                datatype=["str", "number", "number", "number", "str"],
                label="Capacity Tracking"
            )
        
        # God View Matrix Tab
        with gr.Tab("📅 God View Matrix"):
            gr.Markdown("""
            ### Visual Timeline - 72-Month Overview
            Color-coded Gantt chart showing all resident schedules.
            """)
            
            god_view_plot = gr.Plot(label="God View Matrix")
            
            gr.Markdown("### Capacity Heatmap")
            capacity_heatmap = gr.Plot(label="Future Capacity Heatmap")
        
        # Bottleneck Analysis Tab
        with gr.Tab("⚠️ Bottleneck Warnings"):
            gr.Markdown("""
            ### Future Bottleneck Analysis
            Identifies capacity issues in the next 12 months.
            """)
            
            bottleneck_output = gr.Textbox(
                label="Bottleneck Analysis",
                lines=25,
                max_lines=40
            )
            
            gr.Markdown("""
            **Legend:**
            - 🔴 Critical: Requires immediate attention
            - 🟡 Warning: Should be addressed
            - 🟢 OK: Within capacity limits
            """)
        
        # AI Scheduler Tab
        with gr.Tab("🤖 AI Scheduler"):
            gr.Markdown("""
            ### Automated Schedule Generation
            Use OR-Tools constraint solver to generate optimized schedules.
            """)
            
            with gr.Row():
                with gr.Column():
                    time_limit = gr.Slider(
                        label="Time Limit (seconds)",
                        minimum=60,
                        maximum=600,
                        value=300,
                        step=30
                    )
                    generate_btn = gr.Button("🚀 Generate Schedule", variant="primary", size="lg")
                
                with gr.Column():
                    output_excel = gr.File(label="Download Excel Schedule")
                    output_pdf = gr.File(label="Download PDF Audit Report")
            
            status_output = gr.Textbox(label="Scheduling Log", lines=12, max_lines=20)
            
            with gr.Row():
                summary_output = gr.Textbox(label="Solution Summary", lines=15)
                ai_suggestions = gr.Textbox(label="AI Suggestions", lines=15)
        
        # Intern Management Tab
        with gr.Tab("👥 Intern Management"):
            gr.Markdown("### Manage Interns")
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown("#### Add New Intern")
                    new_name = gr.Textbox(label="Name")
                    new_model = gr.Radio(["A", "B"], label="Model", value="A")
                    new_dept = gr.Radio(["A", "B"], label="Department", value="A")
                    new_start = gr.Textbox(
                        label="Start Date (YYYY-MM)",
                        value=datetime.now().strftime("%Y-%m")
                    )
                    add_btn = gr.Button("➕ Add Intern", variant="primary")
                    add_status = gr.Textbox(label="Status", lines=2)
                
                with gr.Column():
                    gr.Markdown("#### Delete Intern")
                    del_name = gr.Textbox(label="Intern Name")
                    del_btn = gr.Button("🗑️ Delete Intern", variant="stop")
                    del_status = gr.Textbox(label="Status", lines=2)
            
            gr.Markdown("### Intern Details")
            with gr.Row():
                view_name = gr.Textbox(label="Enter Intern Name to View")
                view_btn = gr.Button("🔍 View Details")
            
            intern_info = gr.Markdown()
            intern_schedule = gr.Dataframe(
                headers=["Month", "Station", "Status"],
                label="Schedule"
            )
        
        # Help Tab
        with gr.Tab("❓ Help & Documentation"):
            gr.Markdown("""
            ## Complete Residency Program Agent
            
            ### Features
            
            **✅ Phase 1 Complete - All Features Implemented:**
            
            1. **Dashboard**: Load data, view overview, monitor capacity
            2. **God View Matrix**: Visual timeline of all 72-month schedules
            3. **Bottleneck Warnings**: Predictive capacity analysis (12 months ahead)
            4. **AI Scheduler**: Automated constraint-based optimization
            5. **Audit Export**: PDF reports for regulatory compliance
            6. **Intern Management**: Add, delete, view individual residents
            
            ### How to Use
            
            #### 1. Load Data
            - Go to "Dashboard & Data Loading"
            - Upload Excel or download sample template
            - Click "Load Data"
            
            #### 2. Review God View
            - Go to "God View Matrix"
            - See visual timeline of all schedules
            - Review capacity heatmap
            
            #### 3. Check Bottlenecks
            - Go to "Bottleneck Warnings"
            - Review future capacity issues
            - Follow recommendations
            
            #### 4. Generate Schedule
            - Go to "AI Scheduler"
            - Set time limit
            - Click "Generate Schedule"
            - Download Excel + PDF audit report
            
            #### 5. Manage Interns
            - Go to "Intern Management"
            - Add/delete residents as needed
            - View individual schedules
            
            ### Constraints Enforced
            
            - ✅ Station durations (HRP: 6mo, Birth: 6mo, etc.)
            - ✅ Capacity limits per station per month
            - ✅ Sequential dependencies (Basic Sciences → Stage A)
            - ✅ Stage A timing (June only, 3-4.5 years from start)
            - ✅ Stage B timing (November/March, last year)
            - ✅ No changes to past/current months
            - ✅ Department assignments (A or B)
            - ✅ Prefer consecutive assignments
            
            ### PDF Audit Report
            
            Includes:
            - Executive summary
            - Per-resident compliance checklist
            - Station duration verification
            - Regulatory certification
            - Signature blocks
            
            Ready for submission to Scientific Council!
            
            ### Success Metrics
            
            - **<5% Manual Override**: Goal for AI-generated schedules
            - **100% Audit Acceptance**: Regulatory compliance guaranteed
            - **<30 min Generation**: Fast schedule creation
            - **0 Bottlenecks**: Proactive capacity management
            
            ### Support
            
            - Review validation reports
            - Check AI suggestions
            - Monitor bottleneck warnings
            - Consult PDF audit reports
            """)
    
    # Event handlers
    load_btn.click(
        fn=load_interns_from_excel,
        inputs=[excel_input, current_month],
        outputs=[load_status, intern_table, capacity_table, god_view_plot, bottleneck_output]
    )
    
    sample_btn.click(
        fn=create_sample_file,
        inputs=[],
        outputs=[sample_output]
    ).then(
        lambda: gr.update(visible=True),
        outputs=[sample_output]
    )
    
    generate_btn.click(
        fn=generate_schedule,
        inputs=[excel_input, current_month, time_limit],
        outputs=[
            output_excel,
            status_output,
            summary_output,
            ai_suggestions,
            intern_table,
            capacity_table,
            god_view_plot,
            output_pdf,
            capacity_heatmap,
            bottleneck_output
        ]
    )
    
    add_btn.click(
        fn=add_intern,
        inputs=[new_name, new_model, new_dept, new_start],
        outputs=[add_status, intern_table]
    )
    
    del_btn.click(
        fn=delete_intern,
        inputs=[del_name],
        outputs=[del_status, intern_table]
    )
    
    view_btn.click(
        fn=get_intern_details,
        inputs=[view_name],
        outputs=[intern_info, intern_schedule]
    )


if __name__ == "__main__":
    print("="*60)
    print("Residency Program Agent - COMPLETE")
    print("="*60)
    print("Phase 1a Features:")
    print("  ✓ Dashboard & Data Loading")
    print("  ✓ God View Matrix (Visual Timeline)")
    print("  ✓ Bottleneck Warnings (12-month forecast)")
    print("  ✓ AI Scheduler (OR-Tools)")
    print("  ✓ PDF Audit Export")
    print("  ✓ Intern Management (CRUD)")
    print("  ✓ Capacity Tracking")
    print("="*60)
    print()
    
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )

