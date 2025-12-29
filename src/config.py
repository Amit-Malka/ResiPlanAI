from dataclasses import dataclass
from typing import Tuple

@dataclass
class Station:
    name: str
    duration_months: int
    min_interns: int
    max_interns: int
    color: str
    splittable: bool = False
    split_config: Tuple[int, int] = None

# Station definitions for Model A (72 months)
STATIONS_MODEL_A = {
    'orientation': Station('Orientation', 1, 0, 999, '#FFE4E1', False),
    'maternity_intro': Station('Maternity', 1, 0, 999, '#FFD700', False),
    'hrp_a': Station('HRP A', 6, 1, 2, '#87CEEB', True, (4, 2)),
    'hrp_b': Station('HRP B', 6, 1, 2, '#87CEFA', True, (4, 2)),
    'birth': Station('Birth', 6, 3, 4, '#98FB98', True, (4, 2)),
    'gynecology_a': Station('Gynecology A', 6, 1, 2, '#DDA0DD', True, (4, 2)),
    'gynecology_b': Station('Gynecology B', 6, 1, 2, '#DA70D6', True, (4, 2)),
    'maternity_er': Station('Maternity ER', 6, 2, 4, '#FF6B6B', True),
    'womens_er': Station('Womens ER', 3, 1, 3, '#FFA07A', False),
    'gynecology_day': Station('Gynecology Day', 3, 1, 2, '#E6E6FA', False),
    'midwifery_day': Station('Midwifery Day', 3, 1, 2, '#F0E68C', False),
    'basic_sciences': Station('Basic Sciences', 5, 0, 999, '#D3D3D3', False),
    'rotation_a': Station('Rotation A', 3, 0, 999, '#FFDAB9', False),
    'stage_a': Station('Stage A', 0, 0, 999, '#FF4500', False),
    'rotation_b': Station('Rotation B', 3, 0, 999, '#FFDAB9', False),
    'stage_b': Station('Stage B', 0, 0, 999, '#FF8C00', False),
    'department': Station('Department', 14, 0, 999, '#B0C4DE', False),
    'ivf': Station('IVF', 6, 2, 4, '#FFB6C1', False),
    'gyneco_oncology': Station('Gyneco-Oncology', 2, 0, 2, '#CD5C5C', False),
    'rotation_general': Station('Rotation', 4, 0, 999, '#FFDAB9', False),
    'maternity_er_supervisor': Station('Maternity ER Supervisor', 1, 0, 1, '#DC143C', False),
    'maternity_leave': Station('Maternity Leave', 0, 0, 999, '#F5F5F5', False),
    'unpaid_leave': Station('Unpaid Leave', 0, 0, 999, '#E0E0E0', False),
}

# Station definitions for Model B (66 months) - no basic sciences
STATIONS_MODEL_B = {k: v for k, v in STATIONS_MODEL_A.items() if k != 'basic_sciences'}

# Required sequences (must happen in order)
REQUIRED_SEQUENCES = [
    ('basic_sciences', 'stage_a'),  # Basic sciences immediately before Stage A
    ('rotation_a', 'stage_a'),      # Rotation A immediately before Stage A
    ('rotation_b', 'stage_b'),      # Rotation B immediately before Stage B
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

