"""
Visual Timeline Module
Creates God View Matrix visualization for residency schedules.
"""

import plotly.figure_factory as ff
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict
from data_handler import Intern
import config


class TimelineVisualizer:
    """Create visual timeline/Gantt chart for residency schedules."""
    
    def __init__(self, interns: List[Intern]):
        self.interns = interns
        self.color_map = self._create_color_map()
    
    def _create_color_map(self):
        """Create color mapping for stations."""
        color_map = {}
        for station_key, station in config.STATIONS_MODEL_A.items():
            color_map[station_key] = station.color
        return color_map
    
    def create_god_view_matrix(self) -> go.Figure:
        """Create comprehensive God View Matrix visualization."""
        
        tasks = []
        
        for intern in self.interns:
            # Group consecutive months at same station
            station_blocks = self._group_consecutive_stations(intern)
            
            for block in station_blocks:
                station_key = block['station']
                start_month = block['start']
                end_month = block['end']
                
                # Get station info
                stations = config.STATIONS_MODEL_A if intern.model == 'A' else config.STATIONS_MODEL_B
                station = stations.get(station_key)
                station_name = station.name if station else station_key
                
                # Calculate actual dates
                start_date = intern.start_date + timedelta(days=30 * start_month)
                end_date = intern.start_date + timedelta(days=30 * (end_month + 1))
                
                tasks.append({
                    'Task': intern.name,
                    'Start': start_date,
                    'Finish': end_date,
                    'Resource': station_name,
                    'Station': station_key
                })
        
        # Create figure
        if not tasks:
            # Empty figure
            fig = go.Figure()
            fig.add_annotation(
                text="No schedule data available",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False
            )
            return fig
        
        # Create Gantt chart
        fig = ff.create_gantt(
            tasks,
            index_col='Resource',
            show_colorbar=True,
            group_tasks=True,
            showgrid_x=True,
            showgrid_y=True,
            title='Residency Program - God View Matrix',
            height=max(600, len(self.interns) * 40)
        )
        
        # Customize layout
        fig.update_layout(
            xaxis_title="Timeline",
            yaxis_title="Residents",
            font=dict(size=10),
            hovermode='closest',
            plot_bgcolor='white'
        )
        
        # Color by station (if data structure allows)
        try:
            for i, task in enumerate(tasks):
                if i < len(fig.data):
                    station_key = task['Station']
                    color = self.color_map.get(station_key, '#CCCCCC')
                    if hasattr(fig.data[i], 'marker'):
                        fig.data[i].marker.color = color
        except (IndexError, AttributeError):
            # Skip coloring if structure doesn't match
            pass
        
        return fig
    
    def create_capacity_heatmap(self, lookahead_months: int = 12) -> go.Figure:
        """Create capacity heatmap showing utilization."""
        
        # Get all stations
        all_stations = list(config.STATIONS_MODEL_A.keys())
        station_names = [config.STATIONS_MODEL_A[k].name for k in all_stations]
        
        # Calculate capacity for next N months
        max_month = max((max(intern.assignments.keys()) if intern.assignments else 0) 
                       for intern in self.interns)
        
        z_data = []  # Capacity data
        x_labels = []  # Month labels
        
        for month_idx in range(max_month, min(max_month + lookahead_months, 80)):
            x_labels.append(f'M{month_idx + 1}')
            month_counts = []
            
            for station_key in all_stations:
                # Count interns at this station this month
                count = sum(1 for intern in self.interns 
                          if month_idx < intern.total_months 
                          and month_idx in intern.assignments 
                          and intern.assignments[month_idx] == station_key)
                
                # Get capacity
                station = config.STATIONS_MODEL_A[station_key]
                
                # Normalize: 0 = understaffed, 0.5 = optimal, 1 = overstaffed
                if station.max_interns == 999:  # Unlimited
                    normalized = 0.5
                elif count < station.min_interns:
                    normalized = count / station.min_interns * 0.5 if station.min_interns > 0 else 0
                elif count > station.max_interns:
                    normalized = 1.0
                else:
                    normalized = 0.5 + (count - station.min_interns) / (station.max_interns - station.min_interns) * 0.5
                
                month_counts.append(count)
            
            z_data.append(month_counts)
        
        # Transpose for proper orientation
        z_data = list(map(list, zip(*z_data)))
        
        fig = go.Figure(data=go.Heatmap(
            z=z_data,
            x=x_labels,
            y=station_names,
            colorscale=[
                [0, 'red'],      # Understaffed
                [0.5, 'green'],  # Optimal
                [1, 'orange']    # Overstaffed
            ],
            text=z_data,
            texttemplate='%{text}',
            textfont={"size": 8},
            colorbar=dict(
                title="Staffing",
                tickvals=[0, 0.5, 1],
                ticktext=['Under', 'Optimal', 'Over']
            )
        ))
        
        fig.update_layout(
            title='Station Capacity Heatmap (Future Months)',
            xaxis_title='Month',
            yaxis_title='Station',
            height=max(400, len(all_stations) * 25)
        )
        
        return fig
    
    def _group_consecutive_stations(self, intern: Intern) -> List[Dict]:
        """Group consecutive months at the same station into blocks."""
        if not intern.assignments:
            return []
        
        blocks = []
        current_station = None
        block_start = None
        
        for month_idx in sorted(intern.assignments.keys()):
            station = intern.assignments[month_idx]
            
            if station != current_station:
                # Save previous block
                if current_station is not None:
                    blocks.append({
                        'station': current_station,
                        'start': block_start,
                        'end': month_idx - 1
                    })
                
                # Start new block
                current_station = station
                block_start = month_idx
        
        # Save last block
        if current_station is not None:
            last_month = max(intern.assignments.keys())
            blocks.append({
                'station': current_station,
                'start': block_start,
                'end': last_month
            })
        
        return blocks
    
    def create_station_timeline(self, station_key: str) -> go.Figure:
        """Create timeline for a specific station showing all residents."""
        
        station = config.STATIONS_MODEL_A.get(station_key)
        if not station:
            return go.Figure()
        
        # Find all interns at this station
        intern_periods = []
        
        for intern in self.interns:
            for month_idx, assigned_station in intern.assignments.items():
                if assigned_station == station_key:
                    date = intern.start_date + timedelta(days=30 * month_idx)
                    intern_periods.append({
                        'intern': intern.name,
                        'month': month_idx,
                        'date': date
                    })
        
        if not intern_periods:
            fig = go.Figure()
            fig.add_annotation(
                text=f"No residents assigned to {station.name}",
                x=0.5,
                y=0.5,
                showarrow=False
            )
            return fig
        
        # Create scatter plot
        fig = go.Figure()
        
        for intern_name in set(p['intern'] for p in intern_periods):
            intern_data = [p for p in intern_periods if p['intern'] == intern_name]
            dates = [p['date'] for p in intern_data]
            months = [p['month'] for p in intern_data]
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=[intern_name] * len(dates),
                mode='markers',
                name=intern_name,
                marker=dict(size=10, color=station.color)
            ))
        
        fig.update_layout(
            title=f'{station.name} - Resident Assignment Timeline',
            xaxis_title='Date',
            yaxis_title='Resident',
            hovermode='closest'
        )
        
        return fig

