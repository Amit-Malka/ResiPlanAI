"""
Test script for the internship scheduler.
Creates sample data and tests the scheduling pipeline.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from datetime import datetime, timedelta
from data_handler import Intern, ExcelWriter, ExcelParser
from scheduler import SchedulerWithRelaxation
from validator import ScheduleValidator
import config


def create_test_interns():
    """Create test intern data."""
    
    start_date = datetime(2023, 1, 1)
    current_date = datetime(2024, 12, 1)
    
    interns = []
    
    # Intern 1: Model A, Department A
    intern1 = Intern(
        name="Intern 1",
        start_date=start_date,
        model='A',
        department='A',
        current_month_index=23,  # 23 months completed
        total_months=72
    )
    
    # Fill in some initial assignments (first 24 months)
    assignments = [
        ('orientation', 1),
        ('maternity_intro', 1),
        ('hrp_a', 6),
        ('birth', 6),
        ('gynecology_a', 6),
        ('maternity_er', 3),  # Will complete later
    ]
    
    month_idx = 0
    for station_key, duration in assignments:
        for _ in range(duration):
            intern1.assignments[month_idx] = station_key
            month_idx += 1
    
    interns.append(intern1)
    
    # Intern 2: Model A, Department B
    intern2 = Intern(
        name="Intern 2",
        start_date=start_date,
        model='A',
        department='B',
        current_month_index=23,
        total_months=72
    )
    
    assignments2 = [
        ('orientation', 1),
        ('maternity_intro', 1),
        ('hrp_b', 6),
        ('birth', 6),
        ('gynecology_b', 6),
        ('maternity_er', 3),
    ]
    
    month_idx = 0
    for station_key, duration in assignments2:
        for _ in range(duration):
            intern2.assignments[month_idx] = station_key
            month_idx += 1
    
    interns.append(intern2)
    
    # Intern 3: Model B, Department A (starting later)
    intern3 = Intern(
        name="Intern 3",
        start_date=datetime(2023, 7, 1),
        model='B',
        department='A',
        current_month_index=17,
        total_months=66
    )
    
    assignments3 = [
        ('orientation', 1),
        ('maternity_intro', 1),
        ('hrp_a', 6),
        ('birth', 6),
        ('gynecology_a', 3),
    ]
    
    month_idx = 0
    for station_key, duration in assignments3:
        for _ in range(duration):
            intern3.assignments[month_idx] = station_key
            month_idx += 1
    
    interns.append(intern3)
    
    return interns, current_date


def test_scheduling():
    """Test the complete scheduling pipeline."""
    
    print("="*60)
    print("INTERNSHIP SCHEDULER TEST")
    print("="*60)
    print()
    
    # Create test data
    print("Creating test interns...")
    interns, current_date = create_test_interns()
    print(f"Created {len(interns)} test interns")
    print()
    
    # Show initial state
    print("Initial state:")
    for intern in interns:
        print(f"  - {intern.name}: {len(intern.assignments)} months assigned, "
              f"Model {intern.model}, Department {intern.department}")
    print()
    
    # Create scheduler
    start_month = min(intern.start_date for intern in interns)
    
    print("Creating scheduler...")
    scheduler = SchedulerWithRelaxation(
        interns=interns,
        current_date=current_date,
        start_month=start_month,
        time_limit_seconds=120
    )
    print()
    
    # Solve
    print("="*60)
    print("SOLVING")
    print("="*60)
    solution = scheduler.solve_with_relaxation()
    print()
    
    # Check results
    if solution.is_feasible:
        print("✓ Solution found!")
        print(f"  Status: {solution.status}")
        print(f"  Time: {solution.solve_time:.2f} seconds")
        print()
        
        # Validate
        print("="*60)
        print("VALIDATION")
        print("="*60)
        validator = ScheduleValidator(interns, use_ai=False)
        validation_result = validator.validate()
        print(validation_result.get_summary())
        print()
        
        # Save to Excel
        print("="*60)
        print("SAVING OUTPUT")
        print("="*60)
        output_path = "test_schedule_output.xlsx"
        writer = ExcelWriter()
        writer.write_schedule(interns, output_path, start_month)
        print(f"✓ Schedule saved to: {output_path}")
        print()
        
        # Show summary
        summary = scheduler.get_solution_summary()
        print("="*60)
        print("SUMMARY")
        print("="*60)
        for intern_summary in summary['intern_summaries']:
            print(f"\n{intern_summary['name']}:")
            print(f"  Total months: {intern_summary['total_months']}")
            print(f"  Assigned: {intern_summary['assigned_months']}")
            print("  Stations:")
            for station, months in sorted(intern_summary['stations'].items()):
                print(f"    - {station}: {months} months")
        
        return True
    else:
        print("✗ No solution found")
        print(f"  Status: {solution.status}")
        print(f"  Time: {solution.solve_time:.2f} seconds")
        print()
        print("This might be because:")
        print("  - Constraints are too restrictive")
        print("  - Not enough time given to solver")
        print("  - Initial assignments conflict with requirements")
        return False


def test_excel_io():
    """Test Excel reading and writing."""
    
    print("="*60)
    print("TESTING EXCEL I/O")
    print("="*60)
    print()
    
    # Create sample file
    print("Creating sample Excel file...")
    writer = ExcelWriter()
    writer.create_sample_excel("test_sample.xlsx")
    print("✓ Sample file created: test_sample.xlsx")
    print()
    
    # Try to read it back
    print("Reading sample file...")
    parser = ExcelParser()
    current_date = datetime.now()
    interns = parser.parse_excel("test_sample.xlsx", current_date)
    
    print(f"✓ Read {len(interns)} interns:")
    for intern in interns:
        print(f"  - {intern.name}: {len(intern.assignments)} assignments, "
              f"Model {intern.model}, Department {intern.department}")
    print()


if __name__ == "__main__":
    # Test Excel I/O
    test_excel_io()
    print()
    
    # Test scheduling
    success = test_scheduling()
    
    if success:
        print()
        print("="*60)
        print("ALL TESTS PASSED ✓")
        print("="*60)
    else:
        print()
        print("="*60)
        print("TESTS FAILED ✗")
        print("="*60)

