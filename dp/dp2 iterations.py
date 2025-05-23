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
    first_clause = next(iter(current_formula), None)
    if first_clause:
        first_literal = next(iter(first_clause), None)
        if first_literal:
            var_to_resolve = get_variable(first_literal)
    if not var_to_resolve:
        return False, {}
    return solve_sat(resolve(current_formula, var_to_resolve), current_assignments)

def generate_large_formula():
    formula = []
    num_base_vars = 100
    for i in range(1, num_base_vars + 1):
        formula.append({f"x{i}", f"-x{i+1}"})
    formula.append({f"x{num_base_vars + 1}"})
    return [set(clause) for clause in formula]

def benchmark():
    print("Generating a fixed large formula for benchmarking...")
    original_formula = generate_large_formula()
    num_clauses = len(original_formula)
    all_literals = set()
    for clause in original_formula:
        for literal in clause:
            all_literals.add(literal)
    num_variables = len({get_variable(lit) for lit in all_literals})
    print(f"Formula generated with {num_clauses} clauses and approx. {num_variables} variables.\n")
    iteration_values = list(range(1, 30002, 30000))
    cpu_times = []
    memory_peaks = []
    for num_iterations in iteration_values:
        print(f"Running solver {num_iterations} times...")
        tracemalloc.start()
        cpu0 = time.process_time()
        for i in range(num_iterations):
            formula_copy = deepcopy(original_formula)
            satisfiable, _ = solve_sat(formula_copy)
            if i == 0 and num_iterations > 0:
                print(f"  Result of one solve instance: Satisfiable = {satisfiable}")
        cpu1 = time.process_time()
        _, peak_mem_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        total_cpu_time = cpu1 - cpu0
        peak_memory_kb = peak_mem_bytes / 1024
        cpu_times.append(total_cpu_time)
        memory_peaks.append(peak_memory_kb)
        print(f"✔️ Iterations: {num_iterations}, CPU: {total_cpu_time:.6f}s, Peak Mem: {peak_memory_kb:.2f}KB")
        print("-" * 30)
    plt.figure(figsize=(10, 6))
    plt.plot(iteration_values, cpu_times, marker="o", color="blue", label="Total CPU Time (s)")
    plt.title(f"SAT Solver Benchmark: CPU Time vs Iterations (Fixed Formula: {num_clauses} clauses, {num_variables} vars)")
    plt.xlabel("Number of Solver Iterations")
    plt.ylabel("Total CPU Time (seconds)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()
    plt.figure(figsize=(10, 6))
    plt.plot(iteration_values, memory_peaks, marker="^", color="purple", label="Peak Memory (KB)")
    plt.title(f"SAT Solver Benchmark: Memory Usage vs Iterations (Fixed Formula: {num_clauses} clauses, {num_variables} vars)")
    plt.xlabel("Number of Solver Iterations")
    plt.ylabel("Peak Memory (KB)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    benchmark()
