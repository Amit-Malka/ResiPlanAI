import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

# ==================== AI AGENT TOOLS ====================

def tool_get_intern_schedule(interns, intern_name):
    """Tool: Get full schedule for a specific intern."""
    if not interns:
        return "No interns loaded in the system."
    
    # Find intern by name (case-insensitive partial match)
    intern_name_lower = intern_name.lower()
    matching_interns = [i for i in interns if intern_name_lower in i.name.lower()]
    
    if not matching_interns:
        available_names = [i.name for i in interns]
        return f"No intern found matching '{intern_name}'. Available interns: {', '.join(available_names)}"
    
    results = []
    for intern in matching_interns:
        # Build schedule info
        schedule_lines = [
            f"**{intern.name}**",
            f"- Model: {intern.model} ({intern.total_months} months total)",
            f"- Department: {intern.department}",
            f"- Start Date: {intern.start_date.strftime('%B %Y')}",
            f"- Current Month Index: {intern.current_month_index}",
            "",
            "Schedule (month index -> station):"
        ]
        
        # Sort assignments by month index
        sorted_assignments = sorted(intern.assignments.items())
        for month_idx, station in sorted_assignments:
            # Calculate actual date for this month
            actual_date = intern.start_date + timedelta(days=month_idx * 30)
            month_str = actual_date.strftime('%b %Y')
            schedule_lines.append(f"  Month {month_idx} ({month_str}): {station}")
        
        results.append("\n".join(schedule_lines))
    
    return "\n\n".join(results)


def tool_get_station_assignments(interns, station_name, month_year=None):
    """Tool: Get all interns assigned to a station, optionally filtered by month."""
    if not interns:
        return "No interns loaded in the system."
    
    station_name_lower = station_name.lower()
    results = []
    
    for intern in interns:
        for month_idx, station in intern.assignments.items():
            # Check if station matches (case-insensitive partial match)
            if station_name_lower in station.lower():
                # Calculate actual date
                actual_date = intern.start_date + timedelta(days=month_idx * 30)
                month_str = actual_date.strftime('%B %Y')
                
                # Filter by month_year if provided
                if month_year:
                    month_year_lower = month_year.lower()
                    if month_year_lower not in month_str.lower():
                        continue
                
                results.append({
                    'intern': intern.name,
                    'station': station,
                    'month_idx': month_idx,
                    'month_str': month_str
                })
    
    if not results:
        filter_info = f" in {month_year}" if month_year else ""
        return f"No interns found assigned to '{station_name}'{filter_info}."
    
    # Group by month for better readability
    by_month = {}
    for r in results:
        if r['month_str'] not in by_month:
            by_month[r['month_str']] = []
        by_month[r['month_str']].append(f"{r['intern']} ({r['station']})")
    
    output_lines = [f"**Assignments for '{station_name}'**" + (f" in {month_year}" if month_year else "") + ":"]
    for month, interns_list in sorted(by_month.items()):
        output_lines.append(f"\n{month}:")
        for intern_info in interns_list:
            output_lines.append(f"  - {intern_info}")
    
    return "\n".join(output_lines)


def tool_get_month_summary(interns, month_year):
    """Tool: Get a summary of all intern assignments for a specific month across all stations."""
    if not interns:
        return "No interns loaded in the system."
    
    results = {}
    
    for intern in interns:
        for month_idx, station in intern.assignments.items():
            actual_date = intern.start_date + timedelta(days=month_idx * 30)
            month_str = actual_date.strftime('%B %Y')
            
            # Check if this month matches the query
            if month_year.lower() in month_str.lower():
                if station not in results:
                    results[station] = []
                results[station].append(intern.name)
    
    if not results:
        return f"No assignments found for {month_year}."
    
    output_lines = [f"**Schedule Summary for {month_year}:**\n"]
    for station, intern_list in sorted(results.items()):
        output_lines.append(f"**{station}** ({len(intern_list)} interns):")
        for name in sorted(intern_list):
            output_lines.append(f"  - {name}")
        output_lines.append("")
    
    output_lines.append(f"\n*Total: {sum(len(v) for v in results.values())} assignments across {len(results)} stations*")
    
    return "\n".join(output_lines)


def get_ai_response(user_input, context, message_history=None, interns=None):
    """Get AI response from Gemini API with function calling tools."""
    # Extract context information
    total_interns = context.get('total_interns', 0)
    critical_stations = context.get('critical_stations', [])
    bottleneck_count = context.get('bottleneck_count', 0)
    intern_names = context.get('intern_names', [])
    station_names = context.get('station_names', [])
    
    # Build the system prompt with context
    system_prompt = f"""You are ResiPlan Copilot, an AI scheduling assistant for an Obstetrics & Gynecology residency program.

CURRENT CONTEXT:
- Total interns in system: {total_interns}
- Number of bottlenecks detected: {bottleneck_count}
- Critical stations with issues: {', '.join(critical_stations) if critical_stations else 'None'}
- Intern names in system: {', '.join(intern_names) if intern_names else 'None loaded'}
- Available stations: {', '.join(station_names) if station_names else 'Standard stations'}

SYSTEM KNOWLEDGE:
- The system uses OR-Tools constraint solver to generate schedules
- Interns follow either Model A (72 months) or Model B (66 months) training paths
- Stage A exam: June only, 3-4.5 years from start
- Stage B exam: Nov/March, final year only
- Each station has min/max capacity limits

AVAILABLE TOOLS:
You have access to tools to query the schedule database. Use them when asked about:
- Specific intern schedules (use get_intern_schedule)
- Who is assigned to a station (use get_station_assignments)
- Summary of who is assigned to where in a specific month (use get_month_summary)

FEATURES YOU CAN HELP WITH:
1. "Interactive Editor" tab - Direct schedule editing
2. "God View" tab - Visual timeline of all residents
3. "Analytics & Bottlenecks" tab - Capacity analysis
4. "🚀 Run AI Scheduler" button - Automated optimization
5. PDF audit export for compliance

INSTRUCTIONS:
- Be helpful, concise, and specific to residency scheduling
- USE THE TOOLS when the user asks about specific interns or station assignments
- Reference the actual context data when relevant
- Suggest actionable steps using the dashboard features
- Use emojis sparingly for readability
"""

    try:
        # Configure the API
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            return "⚠️ GOOGLE_API_KEY not found. Please set up your API key in the .env file."
        
        genai.configure(api_key=api_key)
        
        # Define the tools for function calling
        tools = [
            {
                "function_declarations": [
                    {
                        "name": "get_intern_schedule",
                        "description": "Get the full schedule for a specific intern including their model, department, start date, and all monthly assignments. Use this when the user asks about a specific intern's schedule.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "intern_name": {
                                    "type": "string",
                                    "description": "The name (or partial name) of the intern to look up"
                                }
                            },
                            "required": ["intern_name"]
                        }
                    },
                    {
                        "name": "get_station_assignments",
                        "description": "Get all interns assigned to a specific station, optionally filtered by month. Use this when the user asks who is working at a station or about station staffing.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "station_name": {
                                    "type": "string",
                                    "description": "The name of the station (e.g., 'Birth', 'HRP A', 'Gynecology B', 'IVF')"
                                },
                                "month_year": {
                                    "type": "string",
                                    "description": "Optional: specific month to filter by (e.g., 'July 2025', 'January 2026')"
                                }
                            },
                            "required": ["station_name"]
                        }
                    },
                    {
                        "name": "get_month_summary",
                        "description": "Get a complete summary of all intern assignments for a specific month, showing who is at each station. Use this when the user asks about a whole month's schedule, 'who is where in [month]', or wants an overview of assignments for a specific month.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "month_year": {
                                    "type": "string",
                                    "description": "The month and year to summarize (e.g., 'December 2025', 'January 2026')"
                                }
                            },
                            "required": ["month_year"]
                        }
                    }
                ]
            }
        ]
        
        # Create model with tools
        model = genai.GenerativeModel('gemini-2.5-flash', tools=tools)
        
        # Build conversation history for the chat
        chat_history = []
        if message_history:
            for msg in message_history:
                role = "user" if msg["role"] == "user" else "model"
                chat_history.append({"role": role, "parts": [msg["content"]]})
        
        # Start chat with history
        chat = model.start_chat(history=chat_history)
        
        # Send the user message with system context
        full_message = f"{system_prompt}\n\nUser question: {user_input}"
        response = chat.send_message(full_message)
        
        # Check if the model wants to call a function
        max_iterations = 5  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Check for function calls in the response
            function_call = None
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    function_call = part.function_call
                    break
            
            if not function_call:
                # No function call, return the text response
                break
            
            # Execute the function
            func_name = function_call.name
            func_args = dict(function_call.args)
            
            if func_name == "get_intern_schedule":
                result = tool_get_intern_schedule(interns, func_args.get("intern_name", ""))
            elif func_name == "get_station_assignments":
                result = tool_get_station_assignments(
                    interns, 
                    func_args.get("station_name", ""),
                    func_args.get("month_year")
                )
            elif func_name == "get_month_summary":
                result = tool_get_month_summary(interns, func_args.get("month_year", ""))
            else:
                result = f"Unknown function: {func_name}"
            
            # Send the function result back to the model
            response = chat.send_message(
                genai.protos.Content(
                    parts=[genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=func_name,
                            response={"result": result}
                        )
                    )]
                )
            )
        
        # Extract final text response
        final_response = ""
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text') and part.text:
                final_response += part.text
        
        return final_response if final_response else "I processed your request but couldn't generate a response."
        
    except Exception as e:
        return f"⚠️ Error connecting to AI: {str(e)}\n\nPlease check your GOOGLE_API_KEY is valid."

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
            'critical_stations': [],
            'intern_names': [i.name for i in st.session_state.interns] if st.session_state.interns else [],
            'station_names': list(config.STATIONS_MODEL_A.keys())
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
        
        # Get AI response with conversation history and interns data
        response = get_ai_response(prompt, context, st.session_state.messages, st.session_state.interns)
        
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

