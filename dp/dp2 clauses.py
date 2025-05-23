import time
import tracemalloc
from copy import deepcopy
import matplotlib.pyplot as plt

def negate_literal(lit):
    return lit[1:] if lit.startswith("-") else "-" + lit

def get_variable(lit):
    return lit[1:] if lit.startswith("-") else lit

def unit_prop(formula, assignments):
    formula = {frozenset(cl) for cl in formula}
    made_change = True
    while made_change:
        made_change = False
        unit = None
        for clause in formula:
            if len(clause) == 1:
                unit = next(iter(clause))
                break
        if unit:
            made_change = True
            var = get_variable(unit)
            assignments[var] = not unit.startswith("-")
            neg_unit = negate_literal(unit)
            new_formula = set()
            for clause in formula:
                if unit in clause:
                    continue
                new_clause = clause - {neg_unit}
                if not new_clause:
                    return {frozenset()}, assignments
                new_formula.add(new_clause)
            formula = new_formula
            if not formula:
                break
    return formula, assignments

def resolve(formula, var):
    pos_clauses = {cl for cl in formula if var in cl}
    neg_clauses = {cl for cl in formula if negate_literal(var) in cl}
    other_clauses = {cl for cl in formula if var not in cl and negate_literal(var) not in cl}
    new_formula_from_resolution = set()
    for p_clause in pos_clauses:
        for n_clause in neg_clauses:
            resolvent = (p_clause - {var}) | (n_clause - {negate_literal(var)})
            is_tautology_direct = any(negate_literal(l) in resolvent for l in resolvent)
            if not is_tautology_direct:
                new_formula_from_resolution.add(frozenset(resolvent))
    return new_formula_from_resolution | other_clauses

def solve_sat(formula, assignments=None):
    if assignments is None:
        assignments = {}
    current_formula = {frozenset(cl) for cl in formula}
    current_assignments = assignments
    current_formula, current_assignments = unit_prop(current_formula, current_assignments)
    if not current_formula:
        return True, current_assignments
    if any(not cl for cl in current_formula):
        return False, {}
    var_to_resolve = None
    for cl in current_formula:
        if cl:
            first_literal = next(iter(cl), None)
            if first_literal:
                var_to_resolve = get_variable(first_literal)
                break
    if not var_to_resolve:
        return True, current_assignments
    return solve_sat(resolve(current_formula, var_to_resolve), current_assignments)

def generate_formula_param(num_base_clauses):
    formula = []
    if num_base_clauses < 1:
        return [{"x1"}]
    for i in range(1, num_base_clauses + 1):
        formula.append({f"x{i}", f"-x{i+1}"})
    formula.append({f"x{num_base_clauses + 1}"})
    return [set(clause) for clause in formula]

def benchmark():
    base_clause_param_values = list(range(10, 300, 5))
    SOLVER_ITERATIONS_PER_FORMULA = 1
    cpu_times = []
    memory_peaks = []
    actual_clause_counts_plot = []

    for base_param in base_clause_param_values:
        print(f"\nGenerating formula with base parameter: {base_param}...")
        current_formula = generate_formula_param(base_param)
        actual_clauses = len(current_formula)
        actual_clause_counts_plot.append(actual_clauses)
        all_literals_current = set()
        for clause in current_formula:
            for literal in clause:
                all_literals_current.add(literal)
        actual_variables = len({get_variable(lit) for lit in all_literals_current})
        print(f"Formula generated: {actual_clauses} actual clauses, {actual_variables} variables.")
        print(f"Running solver {SOLVER_ITERATIONS_PER_FORMULA} time(s) for this formula...")
        tracemalloc.start()
        cpu0 = time.process_time()
        for i in range(SOLVER_ITERATIONS_PER_FORMULA):
            formula_to_solve = deepcopy(current_formula)
            satisfiable, _ = solve_sat(formula_to_solve)
            if i == 0:
                print(f"  Result: Satisfiable = {satisfiable}")
        cpu1 = time.process_time()
        _, peak_mem_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        total_cpu_time = cpu1 - cpu0
        peak_memory_kb = peak_mem_bytes / 1024
        cpu_times.append(total_cpu_time)
        memory_peaks.append(peak_memory_kb)
        print(f"✔️ Base Param: {base_param} (Actual Clauses: {actual_clauses}), CPU: {total_cpu_time:.6f}s, Peak Mem: {peak_memory_kb:.2f}KB")
        print("-" * 40)

    plt.figure(figsize=(10, 6))
    plt.plot(actual_clause_counts_plot, cpu_times, marker="o", color="blue", label=f"CPU Time (s) for {SOLVER_ITERATIONS_PER_FORMULA} solve(s)")
    plt.title("SAT Solver Benchmark: CPU Time vs Number of Clauses")
    plt.xlabel("Number of Actual Clauses in Formula")
    plt.ylabel(f"Total CPU Time (seconds)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

    plt.figure(figsize=(10, 6))
    plt.plot(actual_clause_counts_plot, memory_peaks, marker="^", color="purple", label=f"Peak Memory (KB) for {SOLVER_ITERATIONS_PER_FORMULA} solve(s)")
    plt.title("SAT Solver Benchmark: Memory Usage vs Number of Clauses")
    plt.xlabel("Number of Actual Clauses in Formula")
    plt.ylabel("Peak Memory (KB)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    benchmark()
