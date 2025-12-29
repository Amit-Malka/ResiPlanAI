from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from data_handler import Intern
import config
import os
from dotenv import load_dotenv

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class ValidationResult:
    """Holds validation results."""
    
    def __init__(self):
        self.is_valid = True
        self.errors = []
        self.warnings = []
        self.info = []
    
    def add_error(self, message: str):
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        self.warnings.append(message)
    
    def add_info(self, message: str):
        self.info.append(message)
    
    def get_summary(self) -> str:
        """Get a readable summary of validation results."""
        lines = []
        
        if self.is_valid:
            lines.append("✓ Validation PASSED")
        else:
            lines.append("✗ Validation FAILED")
        
        if self.errors:
            lines.append(f"\nErrors ({len(self.errors)}):")
            for error in self.errors:
                lines.append(f"  - {error}")
        
        if self.warnings:
            lines.append(f"\nWarnings ({len(self.warnings)}):")
            for warning in self.warnings:
                lines.append(f"  - {warning}")
        
        if self.info:
            lines.append(f"\nInfo ({len(self.info)}):")
            for info in self.info:
                lines.append(f"  - {info}")
        
        return "\n".join(lines)


class ScheduleValidator:
    """Validates internship schedules against all constraints."""
    
    def __init__(self, interns: List[Intern], use_ai: bool = True):
        self.interns = interns
        self.use_ai = use_ai and GENAI_AVAILABLE
        self.ai_client = None
        
        if self.use_ai:
            self._setup_ai()
    
    def _setup_ai(self):
        """Setup Google Generative AI client."""
        load_dotenv()
        api_key = os.getenv('GOOGLE_API_KEY')
        
        if api_key:
            genai.configure(api_key=api_key)
            self.ai_client = genai.GenerativeModel('gemini-pro')
        else:
            print("Warning: GOOGLE_API_KEY not found. AI assistance disabled.")
            self.use_ai = False
    
    def validate(self) -> ValidationResult:
        """Perform comprehensive validation."""
        result = ValidationResult()
        
        result.add_info(f"Validating schedules for {len(self.interns)} interns")
        
        # Run all validation checks
        self._validate_completeness(result)
        self._validate_durations(result)
        self._validate_sequences(result)
        self._validate_stage_timing(result)
        self._validate_capacity(result)
        self._validate_continuity(result)
        
        return result
    
    def _validate_completeness(self, result: ValidationResult):
        """Check that all months are assigned."""
        
        for intern in self.interns:
            assigned_months = len(intern.assignments)
            
            if assigned_months < intern.total_months:
                result.add_error(
                    f"{intern.name}: Only {assigned_months}/{intern.total_months} months assigned"
                )
            elif assigned_months > intern.total_months:
                result.add_warning(
                    f"{intern.name}: {assigned_months} months assigned (expected {intern.total_months})"
                )
    
    def _validate_durations(self, result: ValidationResult):
        """Check that each intern completes required durations."""
        
        for intern in self.interns:
            stations = config.STATIONS_MODEL_A if intern.model == 'A' else config.STATIONS_MODEL_B
            station_counts = {}
            
            # Count months per station
            for month_idx, station_key in intern.assignments.items():
                if station_key not in station_counts:
                    station_counts[station_key] = 0
                station_counts[station_key] += 1
            
            # Validate against requirements
            for station_key, station in stations.items():
                if station.duration_months == 0:
                    continue
                
                actual_months = station_counts.get(station_key, 0)
                required_months = station.duration_months
                
                # Handle department-specific stations
                skip_station = False
                if station_key == 'hrp_a' and intern.department != 'A':
                    skip_station = True
                elif station_key == 'hrp_b' and intern.department != 'B':
                    skip_station = True
                elif station_key == 'gynecology_a' and intern.department != 'A':
                    skip_station = True
                elif station_key == 'gynecology_b' and intern.department != 'B':
                    skip_station = True
                
                if skip_station:
                    if actual_months > 0:
                        result.add_error(
                            f"{intern.name}: Assigned to {station.name} but belongs to department {intern.department}"
                        )
                    continue
                
                if actual_months != required_months:
                    result.add_error(
                        f"{intern.name}: {station.name} has {actual_months} months (expected {required_months})"
                    )
    
    def _validate_sequences(self, result: ValidationResult):
        """Validate required sequences."""
        
        for intern in self.interns:
            stations = config.STATIONS_MODEL_A if intern.model == 'A' else config.STATIONS_MODEL_B
            
            for before_key, after_key in config.REQUIRED_SEQUENCES:
                if before_key not in stations or after_key not in stations:
                    continue
                
                # Find last month of 'before' and first month of 'after'
                before_months = [m for m, s in intern.assignments.items() if s == before_key]
                after_months = [m for m, s in intern.assignments.items() if s == after_key]
                
                if before_months and after_months:
                    last_before = max(before_months)
                    first_after = min(after_months)
                    
                    if first_after != last_before + 1:
                        before_station = stations[before_key]
                        after_station = stations[after_key]
                        result.add_error(
                            f"{intern.name}: {before_station.name} must immediately precede {after_station.name}"
                        )
    
    def _validate_stage_timing(self, result: ValidationResult):
        """Validate Stage A and Stage B timing."""
        
        for intern in self.interns:
            stations = config.STATIONS_MODEL_A if intern.model == 'A' else config.STATIONS_MODEL_B
            
            # Validate Stage A
            if 'stage_a' in stations:
                stage_a_months = [m for m, s in intern.assignments.items() if s == 'stage_a']
                
                for month_idx in stage_a_months:
                    # Check calendar month
                    month_date = intern.start_date + timedelta(days=30 * month_idx)
                    if month_date.month != 6:
                        result.add_error(
                            f"{intern.name}: Stage A must be in June (found in month {month_date.month})"
                        )
                    
                    # Check timing from start
                    if month_idx < config.STAGE_A_MIN_MONTHS or month_idx > config.STAGE_A_MAX_MONTHS:
                        result.add_error(
                            f"{intern.name}: Stage A at month {month_idx} (should be between {config.STAGE_A_MIN_MONTHS}-{config.STAGE_A_MAX_MONTHS})"
                        )
            
            # Validate Stage B
            if 'stage_b' in stations:
                stage_b_months = [m for m, s in intern.assignments.items() if s == 'stage_b']
                
                for month_idx in stage_b_months:
                    # Check calendar month
                    month_date = intern.start_date + timedelta(days=30 * month_idx)
                    if month_date.month not in config.STAGE_B_MONTHS:
                        result.add_error(
                            f"{intern.name}: Stage B must be in Nov or March (found in month {month_date.month})"
                        )
                    
                    # Check timing from end
                    months_from_end = intern.total_months - month_idx
                    if months_from_end < config.STAGE_B_MIN_MONTHS_FROM_END or \
                       months_from_end > config.STAGE_B_MAX_MONTHS_FROM_END:
                        result.add_error(
                            f"{intern.name}: Stage B timing incorrect (months from end: {months_from_end})"
                        )
    
    def _validate_capacity(self, result: ValidationResult):
        """Validate station capacity constraints."""
        
        max_months = max(intern.total_months for intern in self.interns)
        
        for month_idx in range(max_months):
            # Count interns per station this month
            station_counts = {}
            
            for intern in self.interns:
                if month_idx < intern.total_months and month_idx in intern.assignments:
                    station_key = intern.assignments[month_idx]
                    if station_key not in station_counts:
                        station_counts[station_key] = 0
                    station_counts[station_key] += 1
            
            # Check against limits
            all_stations = set()
            for intern in self.interns:
                stations = config.STATIONS_MODEL_A if intern.model == 'A' else config.STATIONS_MODEL_B
                all_stations.update(stations.keys())
            
            for station_key in station_counts.keys():
                if station_key in config.STATIONS_MODEL_A:
                    station = config.STATIONS_MODEL_A[station_key]
                    count = station_counts[station_key]
                    
                    if count < station.min_interns:
                        result.add_warning(
                            f"Month {month_idx}: {station.name} has {count} interns (min: {station.min_interns})"
                        )
                    elif count > station.max_interns:
                        result.add_error(
                            f"Month {month_idx}: {station.name} has {count} interns (max: {station.max_interns})"
                        )
    
    def _validate_continuity(self, result: ValidationResult):
        """Check for split stations (non-consecutive assignments)."""
        
        for intern in self.interns:
            stations = config.STATIONS_MODEL_A if intern.model == 'A' else config.STATIONS_MODEL_B
            
            for station_key, station in stations.items():
                if station.duration_months == 0:
                    continue
                
                # Find all months at this station
                months_at_station = sorted([m for m, s in intern.assignments.items() if s == station_key])
                
                if not months_at_station:
                    continue
                
                # Check if consecutive
                is_consecutive = True
                for i in range(len(months_at_station) - 1):
                    if months_at_station[i+1] != months_at_station[i] + 1:
                        is_consecutive = False
                        break
                
                if not is_consecutive:
                    if station.splittable:
                        result.add_warning(
                            f"{intern.name}: {station.name} is split (allowed but not preferred)"
                        )
                    else:
                        result.add_error(
                            f"{intern.name}: {station.name} is split (must be consecutive)"
                        )
    
    def get_ai_suggestions(self, validation_result: ValidationResult) -> str:
        """Get AI-powered suggestions for fixing issues."""
        
        if not self.use_ai or not self.ai_client:
            return "AI suggestions not available (Google API key not configured)"
        
        if validation_result.is_valid:
            return "Schedule is valid. No suggestions needed."
        
        # Create prompt for AI
        prompt = f"""You are an expert in medical internship scheduling. 
        
Review the following validation errors and provide concise, actionable suggestions to fix them:

Errors:
{chr(10).join(validation_result.errors)}

Provide 3-5 specific suggestions to resolve these issues. Be brief and practical."""
        
        try:
            response = self.ai_client.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error getting AI suggestions: {str(e)}"

