from typing import List, Optional, Dict
from datetime import datetime
from ortools.sat.python import cp_model
from data_handler import Intern
from constraints import ConstraintBuilder
import config


class ScheduleSolution:
    """Holds the solution from the scheduler."""
    
    def __init__(self, interns: List[Intern], status: str, solve_time: float):
        self.interns = interns
        self.status = status
        self.solve_time = solve_time
        self.is_optimal = status == 'OPTIMAL'
        self.is_feasible = status in ['OPTIMAL', 'FEASIBLE']


class InternshipScheduler:
    """Main scheduler class that uses OR-Tools to generate schedules."""
    
    def __init__(self, interns: List[Intern], current_date: datetime, 
                 start_month: datetime, time_limit_seconds: int = 300):
        self.interns = interns
        self.current_date = current_date
        self.start_month = start_month
        self.time_limit_seconds = time_limit_seconds
        self.constraint_builder = None
        self.solver = None
        
    def build_model(self) -> cp_model.CpModel:
        """Build the constraint programming model."""
        print("Building constraint model...")
        
        self.constraint_builder = ConstraintBuilder(
            self.interns, 
            self.current_date, 
            self.start_month
        )
        
        # Add all constraints
        print("Adding basic constraints...")
        self.constraint_builder.add_basic_constraints()
        
        print("Adding duration constraints...")
        self.constraint_builder.add_duration_constraints()
        
        print("Adding capacity constraints...")
        self.constraint_builder.add_capacity_constraints()
        
        print("Adding sequence constraints...")
        self.constraint_builder.add_sequence_constraints()
        
        print("Adding stage timing constraints...")
        self.constraint_builder.add_stage_timing_constraints()
        
        print("Adding continuity preferences...")
        self.constraint_builder.add_continuity_preferences()
        
        return self.constraint_builder.get_model()
    
    def solve(self) -> ScheduleSolution:
        """Solve the scheduling problem and return solution."""
        
        # Build the model
        model = self.build_model()
        
        # Create solver
        self.solver = cp_model.CpSolver()
        self.solver.parameters.max_time_in_seconds = self.time_limit_seconds
        self.solver.parameters.log_search_progress = True
        
        print(f"\nSolving with time limit of {self.time_limit_seconds} seconds...")
        status = self.solver.Solve(model)
        
        # Map status to string
        status_name = self.solver.StatusName(status)
        solve_time = self.solver.WallTime()
        
        print(f"\nSolver finished with status: {status_name}")
        print(f"Solve time: {solve_time:.2f} seconds")
        
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            print("Solution found! Extracting assignments...")
            self._extract_solution()
            return ScheduleSolution(self.interns, status_name, solve_time)
        else:
            print("No solution found.")
            return ScheduleSolution(self.interns, status_name, solve_time)
    
    def _extract_solution(self):
        """Extract the solution and update intern assignments."""
        
        assignments_vars = self.constraint_builder.get_assignments()
        
        for i, intern in enumerate(self.interns):
            stations = config.STATIONS_MODEL_A if intern.model == 'A' else config.STATIONS_MODEL_B
            
            # Clear future assignments (keep protected past assignments)
            new_assignments = {}
            
            for month_idx in range(intern.total_months):
                # Find which station this intern is assigned to this month
                for station_key in stations.keys():
                    if self.solver.Value(assignments_vars[i][station_key][month_idx]) == 1:
                        new_assignments[month_idx] = station_key
                        break
            
            # Update intern's assignments
            intern.assignments = new_assignments
    
    def get_solution_summary(self) -> Dict:
        """Get a summary of the solution for display."""
        
        if not self.solver:
            return {"error": "No solution computed yet"}
        
        summary = {
            "status": self.solver.StatusName(self.solver.status()),
            "solve_time": self.solver.WallTime(),
            "num_interns": len(self.interns),
            "intern_summaries": []
        }
        
        for intern in self.interns:
            intern_summary = {
                "name": intern.name,
                "model": intern.model,
                "department": intern.department,
                "total_months": intern.total_months,
                "assigned_months": len(intern.assignments),
                "stations": self._get_intern_station_summary(intern)
            }
            summary["intern_summaries"].append(intern_summary)
        
        return summary
    
    def _get_intern_station_summary(self, intern: Intern) -> Dict[str, int]:
        """Get count of months per station for an intern."""
        
        station_counts = {}
        
        for month_idx, station_key in intern.assignments.items():
            if station_key not in station_counts:
                station_counts[station_key] = 0
            station_counts[station_key] += 1
        
        # Convert to readable names
        stations = config.STATIONS_MODEL_A if intern.model == 'A' else config.STATIONS_MODEL_B
        readable_counts = {}
        
        for station_key, count in station_counts.items():
            if station_key in stations:
                readable_counts[stations[station_key].name] = count
            else:
                readable_counts[station_key] = count
        
        return readable_counts


class SchedulerWithRelaxation(InternshipScheduler):
    """Extended scheduler that can relax constraints if no solution found."""
    
    def __init__(self, interns: List[Intern], current_date: datetime, 
                 start_month: datetime, time_limit_seconds: int = 300):
        super().__init__(interns, current_date, start_month, time_limit_seconds)
        self.relaxation_level = 0
    
    def solve_with_relaxation(self) -> ScheduleSolution:
        """Try to solve, relaxing constraints if needed."""
        
        # First attempt: full constraints
        solution = self.solve()
        
        if solution.is_feasible:
            return solution
        
        print("\n" + "="*50)
        print("No solution found with full constraints.")
        print("Attempting with relaxed constraints...")
        print("="*50 + "\n")
        
        # Try relaxing capacity constraints slightly
        self.relaxation_level = 1
        solution = self._solve_with_relaxed_capacity()
        
        if solution.is_feasible:
            print("Solution found with relaxed capacity constraints.")
            return solution
        
        print("\nCould not find solution even with relaxation.")
        print("Suggestions:")
        print("- Check if total station months match program duration")
        print("- Verify Stage A/B timing is achievable for all interns")
        print("- Review capacity constraints for feasibility")
        
        return solution
    
    def _solve_with_relaxed_capacity(self) -> ScheduleSolution:
        """Solve with slightly relaxed capacity constraints."""
        
        # Rebuild model with relaxed constraints
        self.constraint_builder = ConstraintBuilder(
            self.interns, 
            self.current_date, 
            self.start_month
        )
        
        self.constraint_builder.add_basic_constraints()
        self.constraint_builder.add_duration_constraints()
        
        # Skip capacity constraints or make them soft
        # For MVP, we'll skip them in relaxed mode
        
        self.constraint_builder.add_sequence_constraints()
        self.constraint_builder.add_stage_timing_constraints()
        self.constraint_builder.add_continuity_preferences()
        
        model = self.constraint_builder.get_model()
        
        # Solve
        self.solver = cp_model.CpSolver()
        self.solver.parameters.max_time_in_seconds = self.time_limit_seconds
        
        status = self.solver.Solve(model)
        status_name = self.solver.StatusName(status)
        solve_time = self.solver.WallTime()
        
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            self._extract_solution()
            return ScheduleSolution(self.interns, status_name, solve_time)
        
        return ScheduleSolution(self.interns, status_name, solve_time)

