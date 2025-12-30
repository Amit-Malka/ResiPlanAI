import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data_handler import ExcelParser, ExcelWriter, Intern
from src.scheduler import SchedulerWithRelaxation
from src.validator import ScheduleValidator
from src.bottleneck_analyzer import BottleneckAnalyzer
from src.visual_timeline import TimelineVisualizer
from src.audit_export import generate_quick_audit_report
import src.config as config

# Page configuration
st.set_page_config(
    page_title="ResiPlanAI - Residency Scheduler",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern look
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'interns' not in st.session_state:
    st.session_state.interns = []
if 'current_date' not in st.session_state:
    st.session_state.current_date = datetime.now()
if 'schedule_generated' not in st.session_state:
    st.session_state.schedule_generated = False
if 'edited_df' not in st.session_state:
    st.session_state.edited_df = None

# Helper Functions
def parse_uploaded_file(uploaded_file, current_date):
    """Parse uploaded Excel file and return list of Intern objects."""
    try:
        # Save uploaded file temporarily
        temp_path = f"temp_{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        parser = ExcelParser()
        interns = parser.parse_excel(temp_path, current_date)
        
        # Clean up temp file
        os.remove(temp_path)
        
        return interns, None
    except Exception as e:
        return None, str(e)

def interns_to_dataframe(interns):
    """Convert list of Intern objects to DataFrame for display/editing."""
    if not interns:
        return pd.DataFrame()
    
    # Find max months
    max_months = max(intern.total_months for intern in interns)
    
    # Build DataFrame
    data = {}
    data['Month'] = [(interns[0].start_date + timedelta(days=30*i)).strftime("%Y-%m") 
                     for i in range(max_months)]
    
    for intern in interns:
        stations = config.STATIONS_MODEL_A if intern.model == 'A' else config.STATIONS_MODEL_B
        intern_schedule = []
        
        for month_idx in range(max_months):
            if month_idx in intern.assignments:
                station_key = intern.assignments[month_idx]
                station_name = stations.get(station_key, {'name': station_key})
                if isinstance(station_name, dict):
                    station_name = station_name.get('name', station_key)
                else:
                    station_name = station_name.name if hasattr(station_name, 'name') else str(station_name)
                intern_schedule.append(station_name)
            else:
                intern_schedule.append("")
        
        data[intern.name] = intern_schedule
    
    return pd.DataFrame(data)

def create_gantt_chart(interns):
    """Create interactive Gantt chart for God View."""
    if not interns:
        return go.Figure()
    
    df_data = []
    
    for intern in interns:
        stations = config.STATIONS_MODEL_A if intern.model == 'A' else config.STATIONS_MODEL_B
        
        # Group consecutive months with same station
        if not intern.assignments:
            continue
        
        current_station = None
        start_month = None
        
        for month_idx in sorted(intern.assignments.keys()):
            station_key = intern.assignments[month_idx]
            
            if station_key != current_station:
                # Save previous block
                if current_station is not None:
                    station_obj = stations.get(current_station)
                    station_name = station_obj.name if station_obj else current_station
                    
                    start_date = intern.start_date + timedelta(days=30 * start_month)
                    end_date = intern.start_date + timedelta(days=30 * month_idx)
                    
                    df_data.append({
                        'Intern': intern.name,
                        'Station': station_name,
                        'Start': start_date,
                        'End': end_date,
                        'Department': intern.department
                    })
                
                # Start new block
                current_station = station_key
                start_month = month_idx
        
        # Add final block
        if current_station is not None:
            station_obj = stations.get(current_station)
            station_name = station_obj.name if station_obj else current_station
            
            start_date = intern.start_date + timedelta(days=30 * start_month)
            end_date = intern.start_date + timedelta(days=30 * (month_idx + 1))
            
            df_data.append({
                'Intern': intern.name,
                'Station': station_name,
                'Start': start_date,
                'End': end_date,
                'Department': intern.department
            })
    
    if not df_data:
        fig = go.Figure()
        fig.add_annotation(text="No schedule data available",
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False,
                          font=dict(size=20, color="gray"))
        return fig
    
    df = pd.DataFrame(df_data)
    
    fig = px.timeline(df, x_start="Start", x_end="End", y="Intern", color="Station",
                      title="God View Matrix - 72-Month Timeline")
    
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_layout(
        height=max(400, len(interns) * 40),
        xaxis_title="Timeline",
        yaxis_title="Residents",
        showlegend=True,
        hovermode='closest'
    )
    
    return fig

def create_capacity_chart(interns):
    """Create capacity usage chart."""
    if not interns:
        return go.Figure()
    
    max_months = max(intern.total_months for intern in interns)
    capacity_data = []
    
    for month_idx in range(min(max_months, 24)):  # Show first 24 months
        month_date = interns[0].start_date + timedelta(days=30 * month_idx)
        month_label = month_date.strftime("%Y-%m")
        
        # Count interns per station
        station_counts = {}
        for intern in interns:
            if month_idx in intern.assignments:
                station_key = intern.assignments[month_idx]
                station_counts[station_key] = station_counts.get(station_key, 0) + 1
        
        # Calculate capacity usage
        for station_key, count in station_counts.items():
            station = config.STATIONS_MODEL_A.get(station_key)
            if station:
                usage_pct = (count / station.max_interns * 100) if station.max_interns > 0 else 0
                capacity_data.append({
                    'Month': month_label,
                    'Station': station.name,
                    'Usage %': usage_pct,
                    'Count': count,
                    'Max': station.max_interns
                })
    
    if not capacity_data:
        return go.Figure()
    
    df = pd.DataFrame(capacity_data)
    
    fig = px.bar(df, x='Month', y='Usage %', color='Station',
                 title="Station Capacity Usage (%)",
                 barmode='group',
                 hover_data=['Count', 'Max'])
    
    fig.add_hline(y=100, line_dash="dash", line_color="red", 
                  annotation_text="Max Capacity")
    fig.update_layout(height=400)
    
    return fig

def run_scheduler(interns, current_date, time_limit):
    """Run the AI scheduler."""
    try:
        start_month = min(intern.start_date for intern in interns)
        
        scheduler = SchedulerWithRelaxation(
            interns=interns,
            current_date=current_date,
            start_month=start_month,
            time_limit_seconds=time_limit
        )
        
        solution = scheduler.solve_with_relaxation()
        
        return solution, None
    except Exception as e:
        return None, str(e)

def apply_dataframe_edits(interns, edited_df):
    """Apply manual edits from data editor back to Intern objects."""
    try:
        station_name_to_key = {}
        for station_key, station in config.STATIONS_MODEL_A.items():
            station_name_to_key[station.name] = station_key
        
        for intern in interns:
            if intern.name in edited_df.columns:
                stations = config.STATIONS_MODEL_A if intern.model == 'A' else config.STATIONS_MODEL_B
                
                for month_idx, station_name in enumerate(edited_df[intern.name]):
                    if pd.notna(station_name) and station_name.strip():
                        # Find matching station key
                        station_key = None
                        for key, station in stations.items():
                            if station.name == station_name.strip():
                                station_key = key
                                break
                        
                        if station_key:
                            intern.assignments[month_idx] = station_key
        
        return True, "Edits applied successfully"
    except Exception as e:
        return False, f"Error applying edits: {str(e)}"

# ==================== MAIN DASHBOARD ====================

# Header
st.markdown("""
<div class="main-header">
    <h1>🏥 ResiPlanAI</h1>
    <p>AI-Powered Residency Program Scheduler</p>
</div>
""", unsafe_allow_html=True)

# ==================== SIDEBAR ====================
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # File upload
    uploaded_file = st.file_uploader(
        "📂 Upload Interns Excel File",
        type=['xlsx', 'xls'],
        help="Upload Excel file with intern schedules"
    )
    
    # Date input
    simulation_date = st.date_input(
        "📅 Current Date",
        value=datetime.now(),
        help="Set the current date for simulation"
    )
    
    # Time limit slider
    time_limit = st.slider(
        "⏱️ Max Runtime (seconds)",
        min_value=60,
        max_value=600,
        value=300,
        step=30,
        help="Maximum time for AI scheduler to run"
    )
    
    st.divider()
    
    # Load data button
    if uploaded_file is not None:
        if st.button("📥 Load Data", type="secondary", use_container_width=True):
            with st.spinner("Loading interns..."):
                current_date = datetime.combine(simulation_date, datetime.min.time())
                interns, error = parse_uploaded_file(uploaded_file, current_date)
                
                if error:
                    st.error(f"Error: {error}")
                else:
                    st.session_state.interns = interns
                    st.session_state.current_date = current_date
                    st.session_state.schedule_generated = False
                    st.success(f"✅ Loaded {len(interns)} interns!")
    
    # Run scheduler button
    if st.session_state.interns:
        st.divider()
        if st.button("🚀 Run AI Scheduler", type="primary", use_container_width=True):
            with st.spinner("Running AI scheduler... This may take a few minutes."):
                solution, error = run_scheduler(
                    st.session_state.interns,
                    st.session_state.current_date,
                    time_limit
                )
                
                if error:
                    st.error(f"Scheduler error: {error}")
                elif solution and solution.is_feasible:
                    st.session_state.schedule_generated = True
                    st.success(f"✅ Schedule generated! ({solution.solve_time:.1f}s)")
                    st.balloons()
                else:
                    st.error("❌ Could not find valid solution")
    
    # Stats
    if st.session_state.interns:
        st.divider()
        st.metric("👥 Total Interns", len(st.session_state.interns))
        
        model_a = sum(1 for i in st.session_state.interns if i.model == 'A')
        model_b = len(st.session_state.interns) - model_a
        
        col1, col2 = st.columns(2)
        col1.metric("Model A", model_a)
        col2.metric("Model B", model_b)

# ==================== MAIN CONTENT ====================

if not st.session_state.interns:
    st.info("👈 Upload an Excel file from the sidebar to begin")
    st.stop()

# Create tabs
tab1, tab2, tab3 = st.tabs(["📅 God View (Timeline)", "📝 Interactive Editor", "📊 Analytics & Bottlenecks"])

# ==================== TAB 1: GOD VIEW ====================
with tab1:
    st.subheader("Visual Timeline - 72-Month Overview")
    
    if st.session_state.interns:
        with st.spinner("Generating Gantt chart..."):
            fig = create_gantt_chart(st.session_state.interns)
            st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        st.subheader("Capacity Usage Over Time")
        fig_capacity = create_capacity_chart(st.session_state.interns)
        st.plotly_chart(fig_capacity, use_container_width=True)
    else:
        st.warning("No intern data loaded")

# ==================== TAB 2: INTERACTIVE EDITOR ====================
with tab2:
    st.subheader("Manual Schedule Editor")
    st.caption("Edit cells directly to modify assignments. Changes are applied when you click 'Apply Edits'.")
    
    if st.session_state.interns:
        # Convert to DataFrame
        df = interns_to_dataframe(st.session_state.interns)
        
        if not df.empty:
            # Display editable dataframe
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                height=600,
                num_rows="fixed",
                key="schedule_editor"
            )
            
            # Apply edits button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("💾 Apply Edits", type="primary", use_container_width=True):
                    success, message = apply_dataframe_edits(st.session_state.interns, edited_df)
                    if success:
                        st.success(message)
                        st.session_state.edited_df = edited_df
                        st.rerun()
                    else:
                        st.error(message)
        else:
            st.warning("No schedule data to display")
    else:
        st.warning("No intern data loaded")

# ==================== TAB 3: ANALYTICS ====================
with tab3:
    st.subheader("Future Bottleneck Analysis")
    
    if st.session_state.interns:
        try:
            analyzer = BottleneckAnalyzer(st.session_state.interns, lookahead_months=12)
            analysis = analyzer.analyze()
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Months Analyzed",
                    analysis['analyzed_months'],
                    help="Number of future months analyzed"
                )
            
            with col2:
                st.metric(
                    "Bottlenecks Found",
                    analysis['bottlenecks_found'],
                    delta=f"-{analysis['bottlenecks_found']}" if analysis['bottlenecks_found'] > 0 else None,
                    delta_color="inverse"
                )
            
            with col3:
                st.metric(
                    "Critical Issues",
                    analysis['critical_count'],
                    delta=f"-{analysis['critical_count']}" if analysis['critical_count'] > 0 else None,
                    delta_color="inverse"
                )
            
            with col4:
                st.metric(
                    "Warnings",
                    analysis['warning_count'],
                    delta=f"-{analysis['warning_count']}" if analysis['warning_count'] > 0 else None,
                    delta_color="inverse"
                )
            
            st.divider()
            
            # Display critical issues
            if analysis['critical_count'] > 0:
                st.error("🔴 Critical Issues Detected")
                
                for bottleneck in analysis['bottlenecks']:
                    critical_issues = [i for i in bottleneck['issues'] if i['severity'] == 'critical']
                    if critical_issues:
                        month = bottleneck['month']
                        st.warning(f"**Month {month + 1}:**")
                        for issue in critical_issues:
                            st.write(f"- {issue['station']}: {issue['type']}")
                            if 'deficit' in issue:
                                st.write(f"  → Needs **{issue['deficit']}** more interns")
            
            st.divider()
            
            # Recommendations
            if analysis['recommendations']:
                st.subheader("📋 Recommendations")
                for rec in analysis['recommendations']:
                    st.info(rec)
            
            # Detailed bottleneck table
            if analysis['bottlenecks']:
                st.divider()
                st.subheader("Detailed Bottleneck Report")
                
                bottleneck_data = []
                for bottleneck in analysis['bottlenecks']:
                    for issue in bottleneck['issues']:
                        bottleneck_data.append({
                            'Month': bottleneck['month'] + 1,
                            'Station': issue['station'],
                            'Type': issue['type'],
                            'Severity': issue['severity'],
                            'Details': f"Deficit: {issue.get('deficit', 'N/A')}, Excess: {issue.get('excess', 'N/A')}"
                        })
                
                if bottleneck_data:
                    df_bottlenecks = pd.DataFrame(bottleneck_data)
                    st.dataframe(df_bottlenecks, use_container_width=True, height=400)
        
        except Exception as e:
            st.error(f"Error running bottleneck analysis: {str(e)}")
    else:
        st.warning("No intern data loaded")

# ==================== FOOTER ====================
st.divider()
st.caption("ResiPlanAI v2.0 - Streamlit Dashboard | Powered by OR-Tools & Google Generative AI")

