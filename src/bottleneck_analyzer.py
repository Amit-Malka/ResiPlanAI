"""
Bottleneck Analyzer Module
Identifies future capacity bottlenecks and staffing issues.
"""

from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from data_handler import Intern
import config


class BottleneckAnalyzer:
    """Analyzes future capacity issues in residency schedules."""
    
    def __init__(self, interns: List[Intern], lookahead_months: int = 12):
        self.interns = interns
        self.lookahead_months = lookahead_months
        self.warnings = []
        self.critical_issues = []
    
    def analyze(self) -> Dict:
        """Perform comprehensive bottleneck analysis."""
        
        # Find max month index across all interns
        max_month = 0
        for intern in self.interns:
            if intern.assignments:
                max_month = max(max_month, max(intern.assignments.keys()))
        
        # Analyze next N months from current
        start_month = max_month
        end_month = min(max_month + self.lookahead_months, 
                       max(intern.total_months for intern in self.interns))
        
        bottlenecks = []
        
        for month_idx in range(start_month, end_month):
            month_issues = self._analyze_month(month_idx)
            if month_issues:
                bottlenecks.append({
                    'month': month_idx,
                    'issues': month_issues
                })
        
        # Generate summary
        return {
            'analyzed_months': self.lookahead_months,
            'bottlenecks_found': len(bottlenecks),
            'critical_count': len([b for b in bottlenecks if any(i['severity'] == 'critical' for i in b['issues'])]),
            'warning_count': len([b for b in bottlenecks if any(i['severity'] == 'warning' for i in b['issues'])]),
            'bottlenecks': bottlenecks,
            'recommendations': self._generate_recommendations(bottlenecks)
        }
    
    def _analyze_month(self, month_idx: int) -> List[Dict]:
        """Analyze capacity for a specific month."""
        issues = []
        
        # Count interns per station this month
        station_counts = {}
        interns_at_station = {}
        
        for intern in self.interns:
            if month_idx < intern.total_months and month_idx in intern.assignments:
                station_key = intern.assignments[month_idx]
                
                if station_key not in station_counts:
                    station_counts[station_key] = 0
                    interns_at_station[station_key] = []
                
                station_counts[station_key] += 1
                interns_at_station[station_key].append(intern.name)
        
        # Check against capacity limits
        all_stations = config.STATIONS_MODEL_A
        
        for station_key, count in station_counts.items():
            if station_key not in all_stations:
                continue
            
            station = all_stations[station_key]
            
            # Check min capacity
            if count < station.min_interns:
                issues.append({
                    'type': 'understaffed',
                    'severity': 'critical' if count == 0 else 'warning',
                    'station': station.name,
                    'current': count,
                    'required': station.min_interns,
                    'deficit': station.min_interns - count,
                    'interns': interns_at_station[station_key]
                })
            
            # Check max capacity
            elif count > station.max_interns:
                issues.append({
                    'type': 'overstaffed',
                    'severity': 'warning',
                    'station': station.name,
                    'current': count,
                    'maximum': station.max_interns,
                    'excess': count - station.max_interns,
                    'interns': interns_at_station[station_key]
                })
        
        # Check for stations with zero coverage
        for station_key, station in all_stations.items():
            if station.min_interns > 0 and station_key not in station_counts:
                issues.append({
                    'type': 'no_coverage',
                    'severity': 'critical',
                    'station': station.name,
                    'current': 0,
                    'required': station.min_interns,
                    'deficit': station.min_interns
                })
        
        return issues
    
    def _generate_recommendations(self, bottlenecks: List[Dict]) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        if not bottlenecks:
            recommendations.append("✓ No capacity bottlenecks detected in the next {self.lookahead_months} months.")
            return recommendations
        
        # Count issue types
        understaffed_count = sum(1 for b in bottlenecks 
                                for i in b['issues'] 
                                if i['type'] in ['understaffed', 'no_coverage'])
        
        overstaffed_count = sum(1 for b in bottlenecks 
                               for i in b['issues'] 
                               if i['type'] == 'overstaffed')
        
        critical_count = sum(1 for b in bottlenecks 
                           for i in b['issues'] 
                           if i['severity'] == 'critical')
        
        if critical_count > 0:
            recommendations.append(
                f"⚠️ CRITICAL: {critical_count} critical capacity issues require immediate attention."
            )
        
        if understaffed_count > 0:
            recommendations.append(
                f"📉 {understaffed_count} instances of understaffing detected. "
                f"Consider adjusting rotation schedules or extending timelines."
            )
        
        if overstaffed_count > 0:
            recommendations.append(
                f"📈 {overstaffed_count} instances of overstaffing detected. "
                f"Redistribute residents to understaffed stations."
            )
        
        # Identify most problematic stations
        problem_stations = {}
        for b in bottlenecks:
            for issue in b['issues']:
                station = issue['station']
                if station not in problem_stations:
                    problem_stations[station] = 0
                problem_stations[station] += 1
        
        if problem_stations:
            top_problems = sorted(problem_stations.items(), key=lambda x: x[1], reverse=True)[:3]
            stations_text = ", ".join([f"{s} ({c} months)" for s, c in top_problems])
            recommendations.append(
                f"🎯 Focus on: {stations_text}"
            )
        
        recommendations.append(
            "💡 Run scheduler with relaxed constraints if issues persist."
        )
        
        return recommendations
    
    def get_monthly_summary(self) -> List[Dict]:
        """Get simplified monthly summary for display."""
        analysis = self.analyze()
        
        summary = []
        for bottleneck in analysis['bottlenecks']:
            month_idx = bottleneck['month']
            issues = bottleneck['issues']
            
            critical = sum(1 for i in issues if i['severity'] == 'critical')
            warnings = sum(1 for i in issues if i['severity'] == 'warning')
            
            status = '🔴 CRITICAL' if critical > 0 else '🟡 WARNING' if warnings > 0 else '🟢 OK'
            
            summary.append({
                'month': f'Month {month_idx + 1}',
                'status': status,
                'critical': critical,
                'warnings': warnings,
                'details': ', '.join([f"{i['station']}: {i['type']}" for i in issues[:3]])
            })
        
        return summary
    
    def get_station_forecast(self) -> Dict[str, List[int]]:
        """Get staffing forecast for each station."""
        forecast = {}
        
        max_month = max((max(intern.assignments.keys()) if intern.assignments else 0) 
                       for intern in self.interns)
        
        end_month = min(max_month + self.lookahead_months,
                       max(intern.total_months for intern in self.interns))
        
        # Initialize
        all_stations = config.STATIONS_MODEL_A
        for station_key, station in all_stations.items():
            forecast[station.name] = []
        
        # Count for each month
        for month_idx in range(max_month, end_month):
            station_counts = {}
            
            for intern in self.interns:
                if month_idx < intern.total_months and month_idx in intern.assignments:
                    station_key = intern.assignments[month_idx]
                    if station_key in all_stations:
                        station_name = all_stations[station_key].name
                        if station_name not in station_counts:
                            station_counts[station_name] = 0
                        station_counts[station_name] += 1
            
            # Add counts to forecast
            for station_name in forecast.keys():
                forecast[station_name].append(station_counts.get(station_name, 0))
        
        return forecast

