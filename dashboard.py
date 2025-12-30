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
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'bottleneck_summary' not in st.session_state:
    st.session_state.bottleneck_summary = None

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

def sync_editor_changes(edited_df):
    """
    Sync changes from data editor back to Intern objects in session state.
    Returns (success, message, updated_count).
    """
    try:
        updated_count = 0
        errors = []
        
        # Build station name to key mappings for both models
        station_name_to_key_a = {}
        station_name_to_key_b = {}
        
        for station_key, station in config.STATIONS_MODEL_A.items():
            station_name_to_key_a[station.name.strip().lower()] = station_key
        
        for station_key, station in config.STATIONS_MODEL_B.items():
            station_name_to_key_b[station.name.strip().lower()] = station_key
        
        # Iterate through each intern in session state
        for intern in st.session_state.interns:
            if intern.name not in edited_df.columns:
                continue
            
            # Get appropriate station mapping for this intern's model
            station_mapping = station_name_to_key_a if intern.model == 'A' else station_name_to_key_b
            stations_config = config.STATIONS_MODEL_A if intern.model == 'A' else config.STATIONS_MODEL_B
            
            # Update assignments for each month
            changes_made = False
            for month_idx, station_name in enumerate(edited_df[intern.name]):
                # Skip empty cells
                if pd.isna(station_name) or not str(station_name).strip():
                    # Remove assignment if it exists
                    if month_idx in intern.assignments:
                        del intern.assignments[month_idx]
                        changes_made = True
                    continue
                
                # Normalize station name
                station_name_normalized = str(station_name).strip().lower()
                
                # Find matching station key
                station_key = None
                
                # First try direct mapping
                if station_name_normalized in station_mapping:
                    station_key = station_mapping[station_name_normalized]
                else:
                    # Try partial match
                    for key, station in stations_config.items():
                        if station_name_normalized in station.name.lower() or station.name.lower() in station_name_normalized:
                            station_key = key
                            break
                
                if station_key:
                    # Check if this is a change
                    if month_idx not in intern.assignments or intern.assignments[month_idx] != station_key:
                        intern.assignments[month_idx] = station_key
                        changes_made = True
                else:
                    errors.append(f"{intern.name}, Month {month_idx}: Unknown station '{station_name}'")
            
            if changes_made:
                updated_count += 1
        
        if errors:
            error_msg = "\n".join(errors[:5])  # Show first 5 errors
            if len(errors) > 5:
                error_msg += f"\n... and {len(errors) - 5} more errors"
            return False, f"Partial sync completed with errors:\n{error_msg}", updated_count
        
        return True, f"✓ Successfully updated {updated_count} intern schedules", updated_count
    
    except Exception as e:
        import traceback
        return False, f"Error syncing changes: {str(e)}\n{traceback.format_exc()}", 0

def get_ai_response(user_input, context):
    """Mock AI response function for hackathon demo."""
    user_input_lower = user_input.lower()
    
    # Extract context information
    total_interns = context.get('total_interns', 0)
    critical_stations = context.get('critical_stations', [])
    bottleneck_count = context.get('bottleneck_count', 0)
    
    # Keyword-based smart responses
    if any(word in user_input_lower for word in ['help', 'what can you do', 'capabilities', 'how']):
        return f"""I'm ResiPlan Copilot, your AI scheduling assistant! 🤖

I can help you with:
- **Analyzing bottlenecks** in your {total_interns}-intern schedule
- **Suggesting solutions** for capacity issues
- **Explaining constraints** and rotation requirements
- **Optimizing assignments** to balance workload

Currently tracking: {bottleneck_count} potential bottlenecks
Just ask me about any scheduling issue!"""

    elif any(word in user_input_lower for word in ['bottleneck', 'problem', 'issue', 'warning']):
        if critical_stations:
            stations_text = ", ".join(critical_stations[:3])
            return f"""🔴 **Critical Capacity Issues Detected**

Based on current analysis, I see bottlenecks in:
- {stations_text}

**Recommended Actions:**
1. Run the AI Scheduler to automatically rebalance assignments
2. Check the "Analytics & Bottlenecks" tab for detailed month-by-month breakdown
3. Consider extending rotation durations or adjusting start dates

Would you like specific suggestions for any station?"""
        else:
            return f"✅ Good news! No critical bottlenecks detected in your schedule. Your {total_interns} interns are well-distributed across stations."

    elif any(word in user_input_lower for word in ['july', 'june', 'month', 'when']):
        months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 
                  'September', 'October', 'November', 'December']
        mentioned_month = next((m for m in months if m.lower() in user_input_lower), 'the mentioned month')
        
        return f"""📅 **{mentioned_month} Analysis**

Common issues in {mentioned_month}:
- Stage A exams (June only) - ensure Basic Sciences completed
- Vacation conflicts - verify leave schedules
- Capacity crunches - check staffing minimums

**Quick Fix:**
1. Go to "Interactive Editor" tab
2. Review {mentioned_month} column
3. Manually adjust assignments if needed
4. Click "Apply Edits" to save

Check the "God View" tab for visual timeline!"""

    elif any(word in user_input_lower for word in ['intern', 'resident', 'who', 'assign']):
        return f"""👥 **Intern Management**

Currently managing {total_interns} residents in the system.

**To view individual schedules:**
- Go to "Interactive Editor" tab
- Each column shows one intern's full schedule
- Edit cells directly to reassign rotations

**To optimize assignments:**
- Click "🚀 Run AI Scheduler" in sidebar
- The solver will automatically balance {total_interns} residents across all stations
- Respects all constraints (duration, capacity, sequencing)"""

    elif any(word in user_input_lower for word in ['capacity', 'staff', 'shortage', 'understaffed']):
        if critical_stations:
            return f"""⚠️ **Capacity Issues Identified**

Understaffed stations: {", ".join(critical_stations)}

**Solutions:**
1. **Automated**: Run AI Scheduler to rebalance
2. **Manual**: Go to Interactive Editor, move residents from overstaffed to understaffed stations
3. **Relaxed Mode**: If solver fails, it will automatically try relaxed constraints

The system enforces:
- Min/Max capacity per station
- Required rotation durations
- Sequential dependencies"""
        else:
            return f"✅ All stations are adequately staffed! Your {total_interns} interns meet capacity requirements across all rotations."

    elif any(word in user_input_lower for word in ['constraint', 'rule', 'requirement', 'must']):
        return """📋 **Scheduling Constraints**

The system enforces these hard rules:
1. **Duration**: HRP (6mo), Birth (6mo), Gyn (6mo), IVF (6mo)
2. **Capacity**: Each station has min/max intern limits
3. **Sequencing**: Basic Sciences → Stage A → Stage B
4. **Stage A Timing**: June only, 3-4.5 years from start
5. **Stage B Timing**: Nov/March, final year only
6. **Immutable Past**: Cannot change past/current months
7. **Department**: Respect A/B assignments

**Soft preferences:**
- Consecutive months for same station (continuity)
- Balance workload across residents"""

    elif any(word in user_input_lower for word in ['optimize', 'improve', 'better', 'solution']):
        return f"""💡 **Optimization Strategies**

For your {total_interns}-intern program:

**Immediate Actions:**
1. Run "🚀 AI Scheduler" (uses OR-Tools constraint solver)
2. Set time limit 300+ seconds for better solutions
3. Check "Analytics & Bottlenecks" tab for red flags

**Manual Tuning:**
- Use "Interactive Editor" to fine-tune AI results
- Focus on months with critical issues first
- Verify Stage A/B timing compliance

**Advanced:**
- If solver fails, it automatically relaxes capacity constraints
- Export PDF audit report for documentation
- Review bottleneck forecast to prevent future issues"""

    elif any(word in user_input_lower for word in ['error', 'fail', 'not working', 'problem']):
        return """🔧 **Troubleshooting Guide**

Common issues and fixes:

**Solver fails:**
- Increase time limit (try 600 seconds)
- Check if constraints are achievable
- System will auto-try relaxed mode

**Excel won't load:**
- Verify format: Names in row 1, column B+
- Metadata in rows 82-84
- File not corrupted

**Edits not saving:**
- Click "💾 Apply Edits" button
- Station names must match exactly
- Refresh page if UI freezes

**Visual errors:**
- Reload page
- Check browser console (F12)
- Try different browser"""

    elif any(word in user_input_lower for word in ['thank', 'thanks', 'great', 'good']):
        return "You're welcome! Happy to help optimize your residency program. Feel free to ask anything else! 😊"

    else:
        # Default intelligent response
        return f"""I understand you're asking about: "{user_input}"

**Quick Context:**
- Managing {total_interns} residents
- {bottleneck_count} potential bottlenecks detected
{f"- Critical stations: {', '.join(critical_stations)}" if critical_stations else "- All stations adequately staffed"}

**I can help with:**
- Analyzing specific months or stations
- Explaining constraints and rules
- Suggesting optimization strategies
- Troubleshooting scheduling issues

Could you be more specific about what you'd like to know?"""

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
    
    # AI Advisory Chat
    st.divider()
    col_header1, col_header2 = st.columns([3, 1])
    with col_header1:
        st.header("🤖 ResiPlan Copilot")
    with col_header2:
        if st.button("🗑️", help="Clear chat", key="clear_chat"):
            st.session_state.messages = []
            st.rerun()
    
    st.caption("Ask me anything about your schedule!")
    
    # Display chat history
    chat_container = st.container(height=300)
    with chat_container:
        # Show welcome message if no messages
        if not st.session_state.messages:
            with st.chat_message("assistant"):
                st.write("""👋 Hi! I'm your AI scheduling assistant.

I can help you:
- Analyze bottlenecks
- Explain constraints
- Suggest optimizations
- Troubleshoot issues

Try asking: *"What bottlenecks do I have?"* or *"How can I optimize my schedule?"*""")
        
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about bottlenecks, constraints, or optimization..."):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Build context for AI
        context = {
            'total_interns': len(st.session_state.interns),
            'bottleneck_count': 0,
            'critical_stations': []
        }
        
        # Get bottleneck info if available
        if st.session_state.interns:
            try:
                analyzer = BottleneckAnalyzer(st.session_state.interns, lookahead_months=12)
                analysis = analyzer.analyze()
                context['bottleneck_count'] = analysis['bottlenecks_found']
                
                # Extract critical stations
                for bottleneck in analysis.get('bottlenecks', []):
                    for issue in bottleneck.get('issues', []):
                        if issue.get('severity') == 'critical':
                            context['critical_stations'].append(issue.get('station', 'Unknown'))
                
                # Remove duplicates
                context['critical_stations'] = list(set(context['critical_stations']))
            except:
                pass
        
        # Get AI response
        response = get_ai_response(prompt, context)
        
        # Add assistant response to history
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Rerun to display new messages
        st.rerun()

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
    st.caption("Edit cells directly to modify assignments. Changes are applied when you click 'Save & Re-validate'.")
    
    if st.session_state.interns:
        # Convert to DataFrame
        df = interns_to_dataframe(st.session_state.interns)
        
        if not df.empty:
            # Info box with instructions
            with st.expander("📖 How to Edit", expanded=False):
                st.markdown("""
                **Instructions:**
                1. Click any cell to edit the station assignment
                2. Enter station name (e.g., "HRP A", "Birth", "Gynecology A")
                3. Leave cell empty to remove assignment
                4. Click "💾 Save & Re-validate" when done
                
                **Available Stations:**
                - Orientation, Maternity, HRP A/B, Birth, Gynecology A/B
                - Maternity ER, Women's ER, Gynecology Day, Midwifery Day
                - Basic Sciences, Stage A, Stage B, IVF, Gyneco-Oncology
                """)
            
            # Display editable dataframe
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                height=600,
                num_rows="fixed",
                key="schedule_editor"
            )
            
            # Save & Re-validate button
            st.divider()
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                save_button = st.button("💾 Save & Re-validate", type="primary", use_container_width=True,
                                       help="Apply changes and re-run bottleneck analysis")
            
            if save_button:
                with st.spinner("🔄 Syncing changes to intern schedules..."):
                    # Sync changes to intern objects
                    success, message, updated_count = sync_editor_changes(edited_df)
                    
                    if success:
                        st.toast(f"✓ Updated {updated_count} schedules! Validating...", icon="✅")
                        
                        # Show sync summary
                        st.success(message)
                        
                        # Re-run bottleneck analysis
                        with st.spinner("🔍 Running bottleneck analysis..."):
                            try:
                                analyzer = BottleneckAnalyzer(st.session_state.interns, lookahead_months=12)
                                analysis = analyzer.analyze()
                                st.session_state.bottleneck_summary = analysis
                                
                                # Show detailed validation results
                                col_v1, col_v2, col_v3 = st.columns(3)
                                with col_v1:
                                    st.metric("Bottlenecks", analysis['bottlenecks_found'])
                                with col_v2:
                                    st.metric("Critical", analysis['critical_count'], 
                                             delta=f"-{analysis['critical_count']}" if analysis['critical_count'] > 0 else None,
                                             delta_color="inverse")
                                with col_v3:
                                    st.metric("Warnings", analysis['warning_count'],
                                             delta=f"-{analysis['warning_count']}" if analysis['warning_count'] > 0 else None,
                                             delta_color="inverse")
                                
                                # Show status message
                                if analysis['critical_count'] > 0:
                                    st.warning(f"⚠️ {analysis['critical_count']} critical capacity issues detected. Review Tab 3 (Analytics) for details.")
                                    st.toast(f"⚠️ {analysis['critical_count']} critical issues", icon="⚠️")
                                elif analysis['warning_count'] > 0:
                                    st.info(f"🟡 {analysis['warning_count']} warnings detected. Schedule is mostly valid.")
                                    st.toast(f"🟡 {analysis['warning_count']} warnings", icon="🟡")
                                else:
                                    st.success("✅ No bottlenecks detected! Schedule looks great.")
                                    st.toast("✅ Perfect schedule - no conflicts!", icon="✅")
                                    st.balloons()
                                
                            except Exception as e:
                                st.error(f"Validation error: {str(e)}")
                                st.toast("⚠️ Saved but validation failed", icon="⚠️")
                        
                        # Force rerun to refresh all visualizations
                        st.session_state.edited_df = edited_df.copy()
                        
                        # Wait a moment before rerun
                        import time
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(message)
                        st.toast("❌ Sync failed - check error details above", icon="❌")
            
            # Show last sync info and change detection
            if st.session_state.edited_df is not None:
                st.divider()
                col_info1, col_info2 = st.columns([3, 1])
                with col_info1:
                    st.caption("💡 **Tip:** After saving, check Tab 1 (God View) and Tab 3 (Analytics) for updated visualizations.")
                with col_info2:
                    # Check if dataframe has unsaved changes
                    try:
                        if not edited_df.equals(st.session_state.edited_df):
                            st.warning("⚠️ Unsaved changes")
                        else:
                            st.success("✓ All saved")
                    except:
                        pass
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
            
            # Store in session state for AI chat
            st.session_state.bottleneck_summary = analysis
            
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

