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
    
    def __init__(self, interns: List[Intern], use_ai: bool = True, program_config=None):
        self.interns = interns
        self.use_ai = use_ai and GENAI_AVAILABLE
        self.ai_client = None
        
        # Use provided config or fall back to static imports
        if program_config:
            self.config = program_config.get_config()
        else:
            self.config = {
                'stations_model_a': config.STATIONS_MODEL_A,
                'stations_model_b': config.STATIONS_MODEL_B,
                'before_stage_a': config.BEFORE_STAGE_A,
                'after_stage_a': config.AFTER_STAGE_A,
                'prefer_after_stage_a': config.PREFER_AFTER_STAGE_A,
                'no_split_allowed': config.NO_SPLIT_ALLOWED,
                'department_a_stations': config.DEPARTMENT_A_STATIONS,
                'department_b_stations': config.DEPARTMENT_B_STATIONS,
                'maternity_leave_deduction_limit': config.MATERNITY_LEAVE_DEDUCTION_LIMIT,
                'department_base_months': config.DEPARTMENT_BASE_MONTHS,
                'stage_a_months': config.STAGE_A_MONTHS,
                'stage_b_months': config.STAGE_B_MONTHS,
                'stage_a_min_months': config.STAGE_A_MIN_MONTHS,
                'stage_a_max_months': config.STAGE_A_MAX_MONTHS,
            }
        
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
    
    def validate(self, current_date: datetime = None) -> ValidationResult:
        """Perform comprehensive validation."""
        result = ValidationResult()
        
        result.add_info(f"Validating schedules for {len(self.interns)} interns")
        
        # Calculate leave counts first
        for intern in self.interns:
            intern.calculate_leave_counts()
        
        # Run all validation checks
        self._validate_completeness(result)
        self._validate_durations(result)
        self._validate_sequences(result)
        self._validate_stage_timing(result)
        self._validate_capacity(result)
        self._validate_continuity(result)
        self._validate_prerequisites(result)
        self._validate_department_assignment(result)
        self._validate_maternity_leave(result)
        self._validate_program_duration(result)
        self._validate_department_quota(result)
        if current_date:
            self._validate_past_locked(result, current_date)
        
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
            stations = self.config['stations_model_a'] if intern.model == 'A' else self.config['stations_model_b']
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
                if station_key == 'הריון בסיכון א' and intern.department != 'A':
                    skip_station = True
                elif station_key == 'הריון בסיכון ב' and intern.department != 'B':
                    skip_station = True
                elif station_key == 'גינקולוגיה א' and intern.department != 'A':
                    skip_station = True
                elif station_key == 'גינקולוגיה ב' and intern.department != 'B':
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
            stations = self.config['stations_model_a'] if intern.model == 'A' else self.config['stations_model_b']
            
            for before_key, after_key in self.config.get('required_sequences', []):
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
        """Validate Stage A and Stage B timing relative to INDIVIDUAL intern start dates."""
        
        for intern in self.interns:
            stations = self.config['stations_model_a'] if intern.model == 'A' else self.config['stations_model_b']
            
            # Validate Stage A
            if 'שלב א' in stations:
                stage_a_months = [m for m, s in intern.assignments.items() if s == 'שלב א']
                
                for month_idx in stage_a_months:
                    # Check calendar month (relative to THIS intern's start_date)
                    month_date = intern.get_month_date(month_idx)
                    if month_date.month not in self.config.get('stage_a_months', [6]):
                        result.add_error(
                            f"{intern.name}: שלב א must be in June (found in {month_date.strftime('%B %Y')})"
                        )
                    
                    # Check timing from THIS intern's start_date (3-4.5 years = 36-54 months)
                    min_months = self.config.get('stage_a_min_months', 36)
                    max_months = self.config.get('stage_a_max_months', 54)
                    if month_idx < min_months or month_idx > max_months:
                        years = month_idx / 12
                        result.add_error(
                            f"{intern.name}: שלב א at month {month_idx} ({years:.1f} years from start). "
                            f"Should be between {min_months}-{max_months} months (3-4.5 years)"
                        )
            
            # Validate Stage B
            if 'שלב ב' in stations:
                stage_b_months = [m for m, s in intern.assignments.items() if s == 'שלב ב']
                
                for month_idx in stage_b_months:
                    # Check calendar month (relative to THIS intern's start_date)
                    month_date = intern.get_month_date(month_idx)
                    allowed_months = self.config.get('stage_b_months', [11, 3])
                    if month_date.month not in allowed_months:
                        result.add_error(
                            f"{intern.name}: שלב ב must be in Nov or March (found in {month_date.strftime('%B %Y')})"
                        )
                    
                    # Check timing from end (relative to THIS intern's expected total)
                    expected_total = intern.get_expected_total_months()
                    months_from_end = expected_total - month_idx
                    min_from_end = self.config.get('stage_b_min_months_from_end', 1)
                    max_from_end = self.config.get('stage_b_max_months_from_end', 12)
                    if months_from_end < min_from_end or months_from_end > max_from_end:
                        result.add_error(
                            f"{intern.name}: שלב ב timing incorrect. "
                            f"{months_from_end} months before expected end (should be {min_from_end}-{max_from_end})"
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
                stations = self.config['stations_model_a'] if intern.model == 'A' else self.config['stations_model_b']
                all_stations.update(stations.keys())
            
            for station_key in station_counts.keys():
                if station_key in self.config['stations_model_a']:
                    station = self.config['stations_model_a'][station_key]
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
            stations = self.config['stations_model_a'] if intern.model == 'A' else self.config['stations_model_b']
            
            for station_key, station in stations.items():
                if station.duration_months == 0:
                    continue
                
                # Find all months at this station
                months_at_station = sorted([m for m, s in intern.assignments.items() if s == station_key])
                
                if not months_at_station:
                    continue
                
                # Check if consecutive
                is_consecutive = True
                split_segments = []
                current_segment = [months_at_station[0]]
                
                for i in range(len(months_at_station) - 1):
                    if months_at_station[i+1] != months_at_station[i] + 1:
                        is_consecutive = False
                        split_segments.append(len(current_segment))
                        current_segment = [months_at_station[i+1]]
                    else:
                        current_segment.append(months_at_station[i+1])
                
                if current_segment:
                    split_segments.append(len(current_segment))
                
                if not is_consecutive:
                    # Check if station is in NO_SPLIT_ALLOWED list
                    if station_key in self.config.get('no_split_allowed', []):
                        result.add_error(
                            f"{intern.name}: {station.name} is split (must be continuous). Segments: {split_segments}"
                        )
                    elif station.splittable:
                        # Check if split is 4+2 pattern
                        if station.split_config and split_segments == list(station.split_config):
                            result.add_warning(
                                f"{intern.name}: {station.name} is split {split_segments} (allowed pattern)"
                            )
                        else:
                            result.add_warning(
                                f"{intern.name}: {station.name} is split {split_segments} (not preferred pattern {station.split_config})"
                            )
                    else:
                        result.add_error(
                            f"{intern.name}: {station.name} is split (must be consecutive)"
                        )
    
    def _validate_prerequisites(self, result: ValidationResult):
        """Validate prerequisite ordering (e.g., Birth before Stage A, ER Supervisor after Stage A)."""
        
        for intern in self.interns:
            stage_a_months = [m for m, s in intern.assignments.items() if s == 'שלב א']
            
            if not stage_a_months:
                continue
            
            first_stage_a = min(stage_a_months)
            
            # Check stations that must be BEFORE Stage A
            for station_key in self.config.get('before_stage_a', []):
                station_months = [m for m, s in intern.assignments.items() if s == station_key]
                if station_months:
                    last_station_month = max(station_months)
                    if last_station_month >= first_stage_a:
                        stations = self.config['stations_model_a'] if intern.model == 'A' else self.config['stations_model_b']
                        station = stations.get(station_key)
                        station_name = station.name if station else station_key
                        result.add_error(
                            f"{intern.name}: {station_name} must be completed before Stage A"
                        )
            
            # Check stations that must be AFTER Stage A
            for station_key in self.config.get('after_stage_a', []):
                station_months = [m for m, s in intern.assignments.items() if s == station_key]
                if station_months:
                    first_station_month = min(station_months)
                    if first_station_month <= first_stage_a:
                        stations = self.config['stations_model_a'] if intern.model == 'A' else self.config['stations_model_b']
                        station = stations.get(station_key)
                        station_name = station.name if station else station_key
                        result.add_error(
                            f"{intern.name}: {station_name} must be after Stage A"
                        )
            
            # Check stations that are PREFERRED after Stage A
            for station_key in self.config.get('prefer_after_stage_a', []):
                station_months = [m for m, s in intern.assignments.items() if s == station_key]
                if station_months:
                    first_station_month = min(station_months)
                    if first_station_month <= first_stage_a:
                        stations = self.config['stations_model_a'] if intern.model == 'A' else self.config['stations_model_b']
                        station = stations.get(station_key)
                        station_name = station.name if station else station_key
                        result.add_warning(
                            f"{intern.name}: {station_name} is preferably done after Stage A"
                        )
    
    def _validate_department_assignment(self, result: ValidationResult):
        """Validate department-specific station assignments."""
        
        if not self.config.get('enforce_department_split', True):
            return
        
        for intern in self.interns:
            # Check that intern does stations from their department
            if intern.department == 'A':
                required_stations = self.config.get('department_a_stations', [])
                forbidden_stations = self.config.get('department_b_stations', [])
            else:
                required_stations = self.config.get('department_b_stations', [])
                forbidden_stations = self.config.get('department_a_stations', [])
            
            # Check for forbidden station assignments
            for station_key in forbidden_stations:
                if any(s == station_key for s in intern.assignments.values()):
                    stations = self.config['stations_model_a'] if intern.model == 'A' else self.config['stations_model_b']
                    station = stations.get(station_key)
                    station_name = station.name if station else station_key
                    result.add_error(
                        f"{intern.name}: Assigned to {station_name} but belongs to Department {intern.department}"
                    )
            
            # Check that required stations are present
            for station_key in required_stations:
                if not any(s == station_key for s in intern.assignments.values()):
                    stations = self.config['stations_model_a'] if intern.model == 'A' else self.config['stations_model_b']
                    station = stations.get(station_key)
                    if station and station.duration_months > 0:
                        station_name = station.name if station else station_key
                        result.add_error(
                            f"{intern.name}: Missing required {station_name} for Department {intern.department}"
                        )
    
    def _validate_maternity_leave(self, result: ValidationResult):
        """Validate maternity leave calculations."""
        
        for intern in self.interns:
            maternity_months = sum(1 for s in intern.assignments.values() if s == 'חל"ד')
            
            if maternity_months == 0:
                continue
            
            # Calculate department months
            department_months = sum(1 for s in intern.assignments.values() if s == 'מחלקה')
            base_dept_months = self.config.get('department_base_months', 14)
            deduction_limit = self.config.get('maternity_leave_deduction_limit', 6)
            
            if maternity_months <= deduction_limit:
                # Deduct from department
                expected_department_months = base_dept_months - maternity_months
                if department_months != expected_department_months:
                    result.add_warning(
                        f"{intern.name}: Has {maternity_months}mo maternity leave. "
                        f"Department should be {expected_department_months}mo (found {department_months}mo)"
                    )
            else:
                # Extension required
                extension_months = maternity_months - deduction_limit
                expected_total = intern.total_months + extension_months
                actual_total = len(intern.assignments)
                
                if actual_total != expected_total:
                    result.add_error(
                        f"{intern.name}: Has {maternity_months}mo maternity leave (>{deduction_limit}mo). "
                        f"Total program should extend to {expected_total}mo (found {actual_total}mo)"
                    )
    
    def _validate_past_locked(self, result: ValidationResult, current_date: datetime):
        """Validate that past months are not modified (relative to each intern's timeline)."""
        
        for intern in self.interns:
            for month_idx in intern.assignments.keys():
                # Use intern's individual timeline
                month_date = intern.get_month_date(month_idx)
                
                if month_date < current_date:
                    # This is a past month - check if it matches expected
                    # For now, we just flag if past months exist (can't validate against original)
                    # In production, you'd compare against saved original state
                    pass
    
    def _validate_program_duration(self, result: ValidationResult):
        """
        Validate program duration including leave extensions.
        - Base: 72 (Model A) or 66 (Model B)
        - Maternity: If > 6 months, extend by (total - 6)
        - Sick Leave: Extend by any excess beyond 1 month/year
        - Unpaid: STRICTLY extend by total unpaid months
        """
        
        for intern in self.interns:
            expected_total = intern.get_expected_total_months()
            actual_total = len(intern.assignments)
            
            if actual_total != expected_total:
                # Build detailed explanation
                base = 72 if intern.model == 'A' else 66
                extensions = []
                
                if intern.maternity_leave_months > 6:
                    mat_ext = intern.maternity_leave_months - 6
                    extensions.append(f"{mat_ext}mo maternity extension")
                
                if intern.sick_leave_months_by_year:
                    sick_ext = sum(max(0, count - 1) for count in intern.sick_leave_months_by_year.values())
                    if sick_ext > 0:
                        extensions.append(f"{sick_ext}mo sick leave extension")
                
                if intern.unpaid_leave_months > 0:
                    extensions.append(f"{intern.unpaid_leave_months}mo unpaid extension")
                
                extension_text = " + ".join(extensions) if extensions else "no extensions"
                
                result.add_error(
                    f"{intern.name}: Program duration incorrect. "
                    f"Expected {expected_total}mo ({base}mo base + {extension_text}), found {actual_total}mo"
                )
    
    def _validate_department_quota(self, result: ValidationResult):
        """
        Validate department quota (14 months) including leave credits.
        - Maternity: Counts as dept time, capped at 6 months total
        - Sick Leave: Counts as dept time, capped at 1 month per calendar year
        - Unpaid: Does NOT count as dept time
        """
        
        for intern in self.interns:
            effective_dept = intern.get_effective_department_months()
            required_dept = 14  # Base requirement
            
            if effective_dept < required_dept:
                # Build explanation
                actual_dept = sum(1 for s in intern.assignments.values() if s == 'מחלקה')
                maternity_credit = min(intern.maternity_leave_months, 6)
                sick_credit = sum(min(count, 1) for count in intern.sick_leave_months_by_year.values())
                
                credits_text = []
                if maternity_credit > 0:
                    credits_text.append(f"{maternity_credit}mo maternity credit")
                if sick_credit > 0:
                    credits_text.append(f"{sick_credit}mo sick leave credit")
                
                credits_str = " + ".join(credits_text) if credits_text else "no credits"
                
                result.add_error(
                    f"{intern.name}: Department quota insufficient. "
                    f"Required 14mo, effective {effective_dept}mo "
                    f"({actual_dept}mo actual dept + {credits_str})"
                )
            elif effective_dept > required_dept:
                result.add_warning(
                    f"{intern.name}: Department quota exceeds requirement "
                    f"({effective_dept}mo effective vs 14mo required)"
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

