from typing import List, Dict, Set, Tuple
from ortools.sat.python import cp_model
from datetime import datetime, timedelta
from data_handler import Intern
import config


class ConstraintBuilder:
    """Builds and manages constraints for the internship scheduling problem."""
    
    def __init__(self, interns: List[Intern], current_date: datetime, 
                 start_month: datetime):
        self.interns = interns
        self.current_date = current_date
        self.start_month = start_month
        self.model = cp_model.CpModel()
        
        # Decision variables: intern_station_month[intern_idx][station_key][month_idx]
        self.assignments = {}
        
        # Precompute some useful data
        self.station_keys = {}
        for intern in interns:
            stations = config.STATIONS_MODEL_A if intern.model == 'A' else config.STATIONS_MODEL_B
            self.station_keys[intern.name] = list(stations.keys())
        
        self._create_variables()
    
    def _create_variables(self):
        """Create decision variables for all possible assignments."""
        for i, intern in enumerate(self.interns):
            self.assignments[i] = {}
            stations = config.STATIONS_MODEL_A if intern.model == 'A' else config.STATIONS_MODEL_B
            
            for station_key in stations.keys():
                self.assignments[i][station_key] = {}
                
                for month_idx in range(intern.total_months):
                    # Create boolean variable: is intern i at station s in month m?
                    var_name = f'intern_{i}_{station_key}_{month_idx}'
                    self.assignments[i][station_key][month_idx] = self.model.NewBoolVar(var_name)
    
    def add_basic_constraints(self):
        """Add fundamental constraints that must be satisfied."""
        
        # Constraint 1: Each intern must be at exactly one station per month
        for i, intern in enumerate(self.interns):
            stations = config.STATIONS_MODEL_A if intern.model == 'A' else config.STATIONS_MODEL_B
            
            for month_idx in range(intern.total_months):
                self.model.Add(
                    sum(self.assignments[i][station_key][month_idx] 
                        for station_key in stations.keys()) == 1
                )
        
        # Constraint 2: No changes to past/current month assignments
        for i, intern in enumerate(self.interns):
            for month_idx in range(intern.current_month_index + 1):
                if month_idx in intern.assignments:
                    assigned_station = intern.assignments[month_idx]
                    # Force this assignment
                    self.model.Add(
                        self.assignments[i][assigned_station][month_idx] == 1
                    )
    
    def add_duration_constraints(self):
        """Ensure each intern completes the required duration at each station."""
        
        for i, intern in enumerate(self.interns):
            stations = config.STATIONS_MODEL_A if intern.model == 'A' else config.STATIONS_MODEL_B
            
            for station_key, station in stations.items():
                if station.duration_months > 0:
                    # Skip leave stations (duration = 0)
                    total_months_at_station = sum(
                        self.assignments[i][station_key][month_idx]
                        for month_idx in range(intern.total_months)
                    )
                    
                    # Determine required duration
                    required_duration = station.duration_months
                    
                    # Handle department-specific stations
                    if station_key == 'hrp_a':
                        if intern.department == 'A':
                            self.model.Add(total_months_at_station == required_duration)
                        else:
                            self.model.Add(total_months_at_station == 0)
                    elif station_key == 'hrp_b':
                        if intern.department == 'B':
                            self.model.Add(total_months_at_station == required_duration)
                        else:
                            self.model.Add(total_months_at_station == 0)
                    elif station_key == 'gynecology_a':
                        if intern.department == 'A':
                            self.model.Add(total_months_at_station == required_duration)
                        else:
                            self.model.Add(total_months_at_station == 0)
                    elif station_key == 'gynecology_b':
                        if intern.department == 'B':
                            self.model.Add(total_months_at_station == required_duration)
                        else:
                            self.model.Add(total_months_at_station == 0)
                    else:
                        # All other stations required
                        self.model.Add(total_months_at_station == required_duration)
    
    def add_capacity_constraints(self):
        """Ensure station capacity limits are respected each month."""
        
        # For each month and each station, count interns
        max_months = max(intern.total_months for intern in self.interns)
        
        for month_idx in range(max_months):
            # Get all unique station keys across all models
            all_stations = set()
            for intern in self.interns:
                stations = config.STATIONS_MODEL_A if intern.model == 'A' else config.STATIONS_MODEL_B
                all_stations.update(stations.keys())
            
            for station_key in all_stations:
                # Get station definition (use Model A as reference for shared stations)
                if station_key in config.STATIONS_MODEL_A:
                    station = config.STATIONS_MODEL_A[station_key]
                else:
                    continue
                
                # Count how many interns are at this station this month
                interns_at_station = []
                
                for i, intern in enumerate(self.interns):
                    if month_idx < intern.total_months:
                        stations = config.STATIONS_MODEL_A if intern.model == 'A' else config.STATIONS_MODEL_B
                        if station_key in stations:
                            interns_at_station.append(
                                self.assignments[i][station_key][month_idx]
                            )
                
                if interns_at_station:
                    total_at_station = sum(interns_at_station)
                    
                    # Apply capacity constraints
                    self.model.Add(total_at_station >= station.min_interns)
                    self.model.Add(total_at_station <= station.max_interns)
    
    def add_sequence_constraints(self):
        """Enforce required sequences between stations."""
        
        for i, intern in enumerate(self.interns):
            stations = config.STATIONS_MODEL_A if intern.model == 'A' else config.STATIONS_MODEL_B
            
            for before_key, after_key in config.REQUIRED_SEQUENCES:
                # Skip if station not in this model
                if before_key not in stations or after_key not in stations:
                    continue
                
                # Find last month of 'before' station
                for month_idx in range(intern.total_months - 1):
                    is_last_month_of_before = self.model.NewBoolVar(
                        f'intern_{i}_last_{before_key}_{month_idx}'
                    )
                    
                    # is_last_month_of_before is true if:
                    # - current month is 'before' station
                    # - next month is NOT 'before' station
                    self.model.Add(
                        self.assignments[i][before_key][month_idx] == 1
                    ).OnlyEnforceIf(is_last_month_of_before)
                    
                    self.model.Add(
                        self.assignments[i][before_key][month_idx + 1] == 0
                    ).OnlyEnforceIf(is_last_month_of_before)
                    
                    # If is_last_month_of_before is true, next month must be 'after'
                    self.model.Add(
                        self.assignments[i][after_key][month_idx + 1] == 1
                    ).OnlyEnforceIf(is_last_month_of_before)
    
    def add_stage_timing_constraints(self):
        """Enforce Stage A and Stage B timing rules."""
        
        for i, intern in enumerate(self.interns):
            stations = config.STATIONS_MODEL_A if intern.model == 'A' else config.STATIONS_MODEL_B
            
            if 'stage_a' not in stations:
                continue
            
            # Stage A constraints
            for month_idx in range(intern.total_months):
                # Calculate calendar month for this month_idx
                month_date = intern.start_date + timedelta(days=30 * month_idx)
                calendar_month = month_date.month
                
                # Stage A can only happen in June
                if calendar_month != 6:
                    self.model.Add(self.assignments[i]['stage_a'][month_idx] == 0)
                
                # Stage A must be between 36-54 months from start
                if month_idx < config.STAGE_A_MIN_MONTHS or month_idx > config.STAGE_A_MAX_MONTHS:
                    self.model.Add(self.assignments[i]['stage_a'][month_idx] == 0)
            
            # Stage B constraints
            if 'stage_b' not in stations:
                continue
                
            for month_idx in range(intern.total_months):
                month_date = intern.start_date + timedelta(days=30 * month_idx)
                calendar_month = month_date.month
                
                # Stage B can only happen in November or March
                if calendar_month not in config.STAGE_B_MONTHS:
                    self.model.Add(self.assignments[i]['stage_b'][month_idx] == 0)
                
                # Stage B must be in last year, but not too close to end
                months_from_end = intern.total_months - month_idx
                if months_from_end < config.STAGE_B_MIN_MONTHS_FROM_END or \
                   months_from_end > config.STAGE_B_MAX_MONTHS_FROM_END:
                    self.model.Add(self.assignments[i]['stage_b'][month_idx] == 0)
    
    def add_continuity_preferences(self):
        """Add soft constraints for consecutive station assignments."""
        
        penalties = []
        
        for i, intern in enumerate(self.interns):
            stations = config.STATIONS_MODEL_A if intern.model == 'A' else config.STATIONS_MODEL_B
            
            for station_key, station in stations.items():
                if station.duration_months == 0:
                    continue
                
                # Penalize splits (non-consecutive assignments)
                for month_idx in range(intern.total_months - 1):
                    # If at station in month_idx but not in month_idx+1, and later return
                    is_at_station_now = self.assignments[i][station_key][month_idx]
                    is_at_station_next = self.assignments[i][station_key][month_idx + 1]
                    
                    # Create penalty variable for leaving and returning
                    left_station = self.model.NewBoolVar(f'left_{i}_{station_key}_{month_idx}')
                    
                    # left_station = is_at_station_now AND NOT is_at_station_next
                    self.model.AddBoolAnd([is_at_station_now, is_at_station_next.Not()]).OnlyEnforceIf(left_station)
                    self.model.AddBoolOr([is_at_station_now.Not(), is_at_station_next]).OnlyEnforceIf(left_station.Not())
                    
                    # Check if we return to this station later
                    for future_month in range(month_idx + 2, intern.total_months):
                        returned = self.model.NewBoolVar(f'return_{i}_{station_key}_{month_idx}_{future_month}')
                        
                        # returned = left_station AND is_at_station in future
                        self.model.AddBoolAnd([left_station, self.assignments[i][station_key][future_month]]).OnlyEnforceIf(returned)
                        
                        penalties.append(returned * 10)  # High penalty for non-consecutive
        
        # Add to objective (minimize penalties)
        if penalties:
            self.model.Minimize(sum(penalties))
    
    def get_model(self) -> cp_model.CpModel:
        """Return the constructed CP model."""
        return self.model
    
    def get_assignments(self) -> Dict:
        """Return the assignment variables."""
        return self.assignments

