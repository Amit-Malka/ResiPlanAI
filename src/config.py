from dataclasses import dataclass, asdict
from typing import Tuple, Dict, Any
import copy

@dataclass
class Station:
    name: str
    duration_months: int
    min_interns: int
    max_interns: int
    color: str
    splittable: bool = False
    split_config: Tuple[int, int] = None

# Station definitions for Model A (72 months) - Hebrew keys
STATIONS_MODEL_A = {
    'אוריינטציה': Station('אוריינטציה', 1, 0, 999, '#FFE4E1', False),
    'יולדות': Station('יולדות', 1, 0, 999, '#FFD700', False),
    'הריון בסיכון א': Station('הריון בסיכון א', 6, 1, 2, '#87CEEB', True, (4, 2)),
    'הריון בסיכון ב': Station('הריון בסיכון ב', 6, 1, 2, '#87CEFA', True, (4, 2)),
    'חדר לידה': Station('חדר לידה', 6, 3, 4, '#98FB98', True, (4, 2)),
    'גינקולוגיה א': Station('גינקולוגיה א', 6, 1, 2, '#DDA0DD', True, (4, 2)),
    'גינקולוגיה ב': Station('גינקולוגיה ב', 6, 1, 2, '#DA70D6', True, (4, 2)),
    'מיון יולדות': Station('מיון יולדות', 6, 2, 4, '#FF6B6B', True),
    'מיון נשים': Station('מיון נשים', 3, 1, 3, '#FFA07A', False),
    'א.יום גינקולוגי': Station('א.יום גינקולוגי', 3, 1, 2, '#E6E6FA', False),
    'א.יום מיילדותי': Station('א.יום מיילדותי', 3, 1, 2, '#F0E68C', False),
    'מדעי היסוד': Station('מדעי היסוד', 5, 0, 999, '#D3D3D3', False),
    'רוטציה א': Station('רוטציה א', 3, 0, 999, '#FFDAB9', False),
    'שלב א': Station('שלב א', 0, 0, 999, '#FF4500', False),
    'רוטציה ב': Station('רוטציה ב', 3, 0, 999, '#FFDAB9', False),
    'שלב ב': Station('שלב ב', 0, 0, 999, '#FF8C00', False),
    'מחלקה': Station('מחלקה', 14, 0, 999, '#B0C4DE', False),
    'IVF': Station('IVF', 6, 2, 4, '#FFB6C1', False),
    'גינקואונקולוגיה': Station('גינקואונקולוגיה', 2, 0, 2, '#CD5C5C', False),
    'רוטציה': Station('רוטציה', 4, 0, 999, '#FFDAB9', False),
    'אחראי מיון יולדות': Station('אחראי מיון יולדות', 1, 0, 1, '#DC143C', False),
    'חל"ד': Station('חל"ד', 0, 0, 999, '#F5F5F5', False),
    'חל"ת': Station('חל"ת', 0, 0, 999, '#E0E0E0', False),
    'מחלה': Station('מחלה', 0, 0, 999, '#FFEBCD', False),
}

# Stations that must be completed before Stage A
BEFORE_STAGE_A = ['מיון נשים', 'חדר לידה']

# Stations that must be completed after Stage A
AFTER_STAGE_A = ['אחראי מיון יולדות']

# Stations preferably after Stage A
PREFER_AFTER_STAGE_A = ['IVF']

# Stations that cannot be split
NO_SPLIT_ALLOWED = ['IVF']

# Department-specific stations
DEPARTMENT_A_STATIONS = ['הריון בסיכון א', 'גינקולוגיה א']
DEPARTMENT_B_STATIONS = ['הריון בסיכון ב', 'גינקולוגיה ב']

# Maternity leave rules
MATERNITY_LEAVE_DEDUCTION_LIMIT = 6
DEPARTMENT_BASE_MONTHS = 14

# Station definitions for Model B (66 months) - no basic sciences
STATIONS_MODEL_B = {k: v for k, v in STATIONS_MODEL_A.items() if k != 'מדעי היסוד'}

# Required sequences (must happen in order)
REQUIRED_SEQUENCES = [
    ('מדעי היסוד', 'שלב א'),  # Basic sciences immediately before Stage A
    ('רוטציה א', 'שלב א'),      # Rotation A immediately before Stage A
    ('רוטציה ב', 'שלב ב'),      # Rotation B immediately before Stage B
]

# Stage timing rules
STAGE_A_MONTHS = [6]  # June only
STAGE_B_MONTHS = [11, 3]  # November and March

# Stage A timing: 3-4.5 years (36-54 months) from start, prefer closer to 3 years
STAGE_A_MIN_MONTHS = 36
STAGE_A_MAX_MONTHS = 54
STAGE_A_TARGET_MONTHS = 36

# Stage B timing: last year of internship, preferably not at the very end
STAGE_B_MIN_MONTHS_FROM_END = 1
STAGE_B_MAX_MONTHS_FROM_END = 12

# Leave rules
MAX_UNPAID_LEAVE_BEFORE_EXTENSION = 6  # Up to 6 months deducted from department
DEPARTMENT_MONTHS_BASE = 14

# Preferences
PREFER_CONSECUTIVE = True  # Prefer stations to be consecutive
PREFER_EARLY_NON_ROTATION = True  # Complete non-rotation/non-department stations early
MATERNITY_ER_AFTER_STAGE_A = True  # ER supervisor should be after Stage A

# Department types
DEPARTMENT_A = 'A'
DEPARTMENT_B = 'B'

# Model types
MODEL_A_DURATION = 72
MODEL_B_DURATION = 66


class ProgramConfiguration:
    """Dynamic configuration for residency program rules and constraints."""
    
    def __init__(self):
        """Initialize with default configuration."""
        self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration dictionary."""
        return {
            'stations_model_a': copy.deepcopy(STATIONS_MODEL_A),
            'stations_model_b': copy.deepcopy(STATIONS_MODEL_B),
            'required_sequences': copy.deepcopy(REQUIRED_SEQUENCES),
            'stage_a_months': copy.deepcopy(STAGE_A_MONTHS),
            'stage_b_months': copy.deepcopy(STAGE_B_MONTHS),
            'stage_a_min_months': STAGE_A_MIN_MONTHS,
            'stage_a_max_months': STAGE_A_MAX_MONTHS,
            'stage_a_target_months': STAGE_A_TARGET_MONTHS,
            'stage_b_min_months_from_end': STAGE_B_MIN_MONTHS_FROM_END,
            'stage_b_max_months_from_end': STAGE_B_MAX_MONTHS_FROM_END,
            'max_unpaid_leave_before_extension': MAX_UNPAID_LEAVE_BEFORE_EXTENSION,
            'department_months_base': DEPARTMENT_MONTHS_BASE,
            'prefer_consecutive': PREFER_CONSECUTIVE,
            'prefer_early_non_rotation': PREFER_EARLY_NON_ROTATION,
            'maternity_er_after_stage_a': MATERNITY_ER_AFTER_STAGE_A,
            'model_a_duration': MODEL_A_DURATION,
            'model_b_duration': MODEL_B_DURATION,
            'before_stage_a': copy.deepcopy(BEFORE_STAGE_A),
            'after_stage_a': copy.deepcopy(AFTER_STAGE_A),
            'prefer_after_stage_a': copy.deepcopy(PREFER_AFTER_STAGE_A),
            'no_split_allowed': copy.deepcopy(NO_SPLIT_ALLOWED),
            'department_a_stations': copy.deepcopy(DEPARTMENT_A_STATIONS),
            'department_b_stations': copy.deepcopy(DEPARTMENT_B_STATIONS),
            'maternity_leave_deduction_limit': MATERNITY_LEAVE_DEDUCTION_LIMIT,
            'department_base_months': DEPARTMENT_BASE_MONTHS,
            'allow_split_rotations': True,
            'enforce_department_split': True,
        }
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return self.config
    
    def update_config(self, new_values: Dict[str, Any]):
        """Update configuration with new values."""
        self.config.update(new_values)
    
    def update_station(self, station_key: str, **kwargs):
        """Update specific station attributes."""
        if station_key in self.config['stations_model_a']:
            station = self.config['stations_model_a'][station_key]
            for key, value in kwargs.items():
                if hasattr(station, key):
                    setattr(station, key, value)
        
        if station_key in self.config['stations_model_b']:
            station = self.config['stations_model_b'][station_key]
            for key, value in kwargs.items():
                if hasattr(station, key):
                    setattr(station, key, value)
    
    def reset_to_defaults(self):
        """Reset configuration to default values."""
        self.config = self._get_default_config()
    
    def get_station_list(self, model='A'):
        """Get list of stations for UI display."""
        stations_dict = self.config['stations_model_a'] if model == 'A' else self.config['stations_model_b']
        
        station_list = []
        for key, station in stations_dict.items():
            station_list.append({
                'key': key,
                'name': station.name,
                'duration': station.duration_months,
                'min_interns': station.min_interns,
                'max_interns': station.max_interns,
                'splittable': station.splittable
            })
        
        return station_list

