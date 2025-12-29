from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment
import config
import re
from translation_config import HEBREW_MEDICAL_TERMS, get_hebrew_translation

# Translation support
try:
    from deep_translator import GoogleTranslator
    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False
    print("Warning: deep-translator not installed. Using precomputed translations only.")

@dataclass
class Intern:
    name: str
    start_date: datetime
    model: str  # 'A' or 'B'
    department: str  # 'A' or 'B'
    current_month_index: int  # Index of current month in internship
    assignments: Dict[int, str] = field(default_factory=dict)  # month_index -> station_key
    total_months: int = 72
    unpaid_leave_months: int = 0
    maternity_leave_months: int = 0
    
    def __post_init__(self):
        if self.model == 'B':
            self.total_months = 66


class ExcelParser:
    
    def __init__(self):
        """Initialize Excel parser with translation support."""
        self.translator = None
        if TRANSLATION_AVAILABLE:
            try:
                self.translator = GoogleTranslator(source='he', target='en')
            except Exception as e:
                print(f"Warning: Could not initialize translator: {e}")
    
    def _contains_hebrew(self, text: str) -> bool:
        """Check if text contains Hebrew characters."""
        if not text:
            return False
        # Hebrew Unicode range: \u0590-\u05FF
        return bool(re.search(r'[\u0590-\u05FF]', str(text)))
    
    def _translate_hebrew(self, text: str) -> str:
        """Translate Hebrew text to English."""
        if not text:
            return text
        
        text_str = str(text).strip()
        
        # Don't translate if no Hebrew
        if not self._contains_hebrew(text_str):
            return text_str
        
        # First try precomputed translations (fast and accurate)
        precomputed = get_hebrew_translation(text_str)
        if precomputed != text_str:
            print(f"Translated (precomputed): '{text_str}' -> '{precomputed}'")
            return precomputed
        
        # Fall back to online translation if available
        if self.translator:
            try:
                translated = self.translator.translate(text_str)
                print(f"Translated (online): '{text_str}' -> '{translated}'")
                return translated
            except Exception as e:
                print(f"Translation warning for '{text_str}': {e}")
        
        # If all else fails, return original
        print(f"No translation for: '{text_str}'")
        return text_str
    
    def parse_excel(self, file_path: str, current_date: datetime) -> List[Intern]:
        """Parse Excel file and extract intern information."""
        wb = openpyxl.load_workbook(file_path)
        ws = wb.active
        
        interns = []
        
        # Read header row to get intern names
        header_row = 1
        col_idx = 2  # Start from column B (index 2)
        max_columns_to_check = 50  # Safety limit
        
        while col_idx < max_columns_to_check:
            cell = ws.cell(row=header_row, column=col_idx)
            if cell.value is None:
                break
                
            intern_name = str(cell.value).strip()
            if not intern_name:
                break
            
            # Translate Hebrew names if needed
            intern_name = self._translate_hebrew(intern_name)
            
            # Try to get metadata from a separate sheet or use defaults
            start_date = self._get_intern_start_date(ws, col_idx, current_date)
            model = self._get_intern_model(ws, col_idx)
            department = self._get_intern_department(ws, col_idx)
            
            # Parse assignments
            assignments = {}
            current_month_index = 0
            row_idx = 2  # Start reading assignments from row 2
            
            while row_idx < 100:  # Max 100 rows
                cell = ws.cell(row=row_idx, column=col_idx)
                if cell.value:
                    station_value = str(cell.value).strip()
                    # Translate Hebrew station names
                    station_value = self._translate_hebrew(station_value)
                    station_key = self._normalize_station_name(station_value)
                    assignments[row_idx - 2] = station_key
                    
                    # Determine current month index
                    month_date = start_date + timedelta(days=30 * (row_idx - 2))
                    if month_date <= current_date:
                        current_month_index = row_idx - 2
                
                row_idx += 1
                if row_idx - 2 >= 80:  # Stop if we've read enough months
                    break
            
            total_months = 72 if model == 'A' else 66
            
            intern = Intern(
                name=intern_name,
                start_date=start_date,
                model=model,
                department=department,
                current_month_index=current_month_index,
                assignments=assignments,
                total_months=total_months
            )
            
            interns.append(intern)
            col_idx += 1
        
        wb.close()
        return interns
    
    def _get_intern_start_date(self, ws, col_idx: int, default_date: datetime) -> datetime:
        """Extract intern start date from metadata or use default."""
        # Try to find metadata sheet or use default
        # For MVP, we'll use a simple approach: check if there's a "Start Date" in the first column
        try:
            # Look for start date in the same column, further down
            for row in range(80, 90):
                label_cell = ws.cell(row=row, column=1)
                if label_cell.value and 'start' in str(label_cell.value).lower():
                    date_cell = ws.cell(row=row, column=col_idx)
                    if date_cell.value:
                        if isinstance(date_cell.value, datetime):
                            return date_cell.value
                        return datetime.strptime(str(date_cell.value), '%Y-%m-%d')
        except:
            pass
        
        # Default: assume started 12 months ago
        return default_date - timedelta(days=365)
    
    def _get_intern_model(self, ws, col_idx: int) -> str:
        """Extract intern model (A or B) from metadata."""
        try:
            for row in range(80, 90):
                label_cell = ws.cell(row=row, column=1)
                if label_cell.value and 'model' in str(label_cell.value).lower():
                    model_cell = ws.cell(row=row, column=col_idx)
                    if model_cell.value:
                        model_val = str(model_cell.value).strip().upper()
                        if 'B' in model_val:
                            return 'B'
                        return 'A'
        except:
            pass
        return 'A'  # Default to Model A
    
    def _get_intern_department(self, ws, col_idx: int) -> str:
        """Extract intern department (A or B) from metadata."""
        try:
            for row in range(80, 90):
                label_cell = ws.cell(row=row, column=1)
                if label_cell.value and 'department' in str(label_cell.value).lower():
                    dept_cell = ws.cell(row=row, column=col_idx)
                    if dept_cell.value:
                        dept_val = str(dept_cell.value).strip().upper()
                        if 'B' in dept_val:
                            return 'B'
                        return 'A'
        except:
            pass
        return 'A'  # Default to Department A
    
    def _normalize_station_name(self, station_value: str) -> str:
        """Normalize station name from Excel to config key."""
        station_lower = station_value.lower().strip()
        
        # Map common variations to config keys (English and translated Hebrew terms)
        mappings = {
            'orientation': 'orientation',
            'adjustment': 'orientation',  # Hebrew translation
            'maternity': 'maternity_intro',
            'motherhood': 'maternity_intro',  # Hebrew translation
            'hrp a': 'hrp_a',
            'hrp b': 'hrp_b',
            'hrp': 'hrp_a',
            'birth': 'birth',
            'delivery': 'birth',
            'labor': 'birth',  # Hebrew translation
            'gynecology a': 'gynecology_a',
            'gynecology b': 'gynecology_b',
            'gynecology': 'gynecology_a',
            'maternity er': 'maternity_er',
            'maternity emergency': 'maternity_er',
            'emergency room maternity': 'maternity_er',
            'womens er': 'womens_er',
            'women er': 'womens_er',
            'emergency room women': 'womens_er',
            'gynecology day': 'gynecology_day',
            'gyneco day': 'gynecology_day',
            'day gynecology': 'gynecology_day',
            'midwifery day': 'midwifery_day',
            'day midwifery': 'midwifery_day',
            'basic sciences': 'basic_sciences',
            'sciences': 'basic_sciences',
            'science': 'basic_sciences',
            'rotation a': 'rotation_a',
            'stage a': 'stage_a',
            'level a': 'stage_a',
            'rotation b': 'rotation_b',
            'stage b': 'stage_b',
            'level b': 'stage_b',
            'department': 'department',
            'ward': 'department',
            'ivf': 'ivf',
            'gyneco-oncology': 'gyneco_oncology',
            'gyneco oncology': 'gyneco_oncology',
            'oncology': 'gyneco_oncology',
            'rotation': 'rotation_general',
            'maternity er supervisor': 'maternity_er_supervisor',
            'er supervisor': 'maternity_er_supervisor',
            'supervisor': 'maternity_er_supervisor',
            'maternity leave': 'maternity_leave',
            'unpaid leave': 'unpaid_leave',
            'leave': 'unpaid_leave',
        }
        
        for key, value in mappings.items():
            if key in station_lower:
                return value
        
        return 'department'  # Default fallback


class ExcelWriter:
    
    def write_schedule(self, interns: List[Intern], output_path: str, start_month: datetime):
        """Write intern schedules to Excel with formatting."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Internship Schedule"
        
        # Write header row with intern names
        ws.cell(row=1, column=1, value="Month")
        for col_idx, intern in enumerate(interns, start=2):
            cell = ws.cell(row=1, column=col_idx, value=intern.name)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
        
        # Write month labels and assignments
        max_months = max(intern.total_months for intern in interns)
        
        for month_idx in range(max_months):
            month_date = start_month + timedelta(days=30 * month_idx)
            month_label = month_date.strftime("%Y-%m")
            
            ws.cell(row=month_idx + 2, column=1, value=month_label)
            
            for col_idx, intern in enumerate(interns, start=2):
                if month_idx < intern.total_months and month_idx in intern.assignments:
                    station_key = intern.assignments[month_idx]
                    
                    # Get station info
                    stations = config.STATIONS_MODEL_A if intern.model == 'A' else config.STATIONS_MODEL_B
                    station = stations.get(station_key)
                    
                    if station:
                        cell = ws.cell(row=month_idx + 2, column=col_idx, value=station.name)
                        
                        # Apply color
                        fill = PatternFill(start_color=station.color.lstrip('#'), 
                                         end_color=station.color.lstrip('#'), 
                                         fill_type='solid')
                        cell.fill = fill
                        cell.alignment = Alignment(horizontal='center')
        
        # Auto-adjust column widths
        for col in range(1, len(interns) + 2):
            ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 15
        
        # Add metadata section
        metadata_row = max_months + 5
        ws.cell(row=metadata_row, column=1, value="Start Date")
        ws.cell(row=metadata_row + 1, column=1, value="Model")
        ws.cell(row=metadata_row + 2, column=1, value="Department")
        
        for col_idx, intern in enumerate(interns, start=2):
            ws.cell(row=metadata_row, column=col_idx, value=intern.start_date.strftime("%Y-%m-%d"))
            ws.cell(row=metadata_row + 1, column=col_idx, value=intern.model)
            ws.cell(row=metadata_row + 2, column=col_idx, value=intern.department)
        
        wb.save(output_path)
        wb.close()
    
    def create_sample_excel(self, output_path: str):
        """Create a sample Excel file for testing."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Sample Schedule"
        
        # Sample interns
        ws.cell(row=1, column=1, value="Month")
        ws.cell(row=1, column=2, value="Intern 1")
        ws.cell(row=1, column=3, value="Intern 2")
        
        # Sample assignments (first few months)
        assignments = [
            "Orientation",
            "Maternity",
            "HRP A",
            "HRP A",
            "HRP A",
            "HRP A",
        ]
        
        for i, assignment in enumerate(assignments, start=2):
            ws.cell(row=i, column=2, value=assignment)
            ws.cell(row=i, column=3, value=assignment)
        
        # Metadata
        ws.cell(row=82, column=1, value="Start Date")
        ws.cell(row=82, column=2, value="2023-01-01")
        ws.cell(row=82, column=3, value="2023-01-01")
        
        ws.cell(row=83, column=1, value="Model")
        ws.cell(row=83, column=2, value="A")
        ws.cell(row=83, column=3, value="A")
        
        ws.cell(row=84, column=1, value="Department")
        ws.cell(row=84, column=2, value="A")
        ws.cell(row=84, column=3, value="B")
        
        wb.save(output_path)
        wb.close()

