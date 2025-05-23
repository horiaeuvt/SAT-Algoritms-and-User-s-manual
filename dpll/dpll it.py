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
    return formula, assignments

def resolve(formula, var):
    pos = {cl for cl in formula if var in cl}
    neg = {cl for cl in formula if negate_literal(var) in cl}
    other = {cl for cl in formula if var not in cl and negate_literal(var) not in cl}
    new_formula = set()
    if not pos or not neg:
        return formula
    for p in pos:
        for n in neg:
            res = (p - {var}) | (n - {negate_literal(var)})
            if not any(negate_literal(l) in res for l in res if get_variable(l) == get_variable(negate_literal(l))):
                if not res and len(p) == 1 and len(n) == 1:
                    return {frozenset()}
                if res:
                    new_formula.add(res)
    return new_formula | other

def solve_sat(formula, assignments=None):
    if assignments is None:
        assignments = {}
    current_assignments = deepcopy(assignments)
    formula_copy = {frozenset(cl) for cl in formula}
    formula_copy, current_assignments = unit_prop(formula_copy, current_assignments)
    if not formula_copy:
        return True, current_assignments
    if any(len(clause) == 0 for clause in formula_copy):
        return False, {}
    var_to_assign = None
    for clause in formula_copy:
        for literal in clause:
            var_to_assign = get_variable(literal)
            break
        if var_to_assign:
            break
    if not var_to_assign:
        return True, current_assignments
    assignments_true = deepcopy(current_assignments)
    assignments_true[var_to_assign] = True
    formula_true = deepcopy(formula_copy)
    next_formula_true = set()
    conflict_true = False
    for cl in formula_true:
        if var_to_assign in cl:
            continue
        if negate_literal(var_to_assign) in cl:
            new_cl = cl - {negate_literal(var_to_assign)}
            if not new_cl:
                conflict_true = True
                break
            next_formula_true.add(new_cl)
        else:
            next_formula_true.add(cl)
    if not conflict_true:
        res, final_assignments = solve_sat(next_formula_true, assignments_true)
        if res:
            return True, final_assignments
    assignments_false = deepcopy(current_assignments)
    assignments_false[var_to_assign] = False
    formula_false = deepcopy(formula_copy)
    next_formula_false = set()
    conflict_false = False
    for cl in formula_false:
        if negate_literal(var_to_assign) in cl:
            continue
        if var_to_assign in cl:
            new_cl = cl - {var_to_assign}
            if not new_cl:
                conflict_false = True
                break
            next_formula_false.add(new_cl)
        else:
            next_formula_false.add(cl)
    if not conflict_false:
        res, final_assignments = solve_sat(next_formula_false, assignments_false)
        if res:
            return True, final_assignments
    return False, {}

def generate_formula(clause_count):
    formula = []
    for i in range(1, clause_count + 1):
        formula.append({f"x{i}", f"-x{i+1}"})
    formula.append({f"x{clause_count + 1}"})
    return [set(clause) for clause in formula]

def benchmark():
    FIXED_CLAUSE_COUNT = 30
    print(f"Generating formula with a fixed clause count: {FIXED_CLAUSE_COUNT}\n")
    formula = generate_formula(FIXED_CLAUSE_COUNT)
    iteration_values = list(range(1, 10001, 500))
    cpu_times = []
    memory_peaks = []
    for num_iterations in iteration_values:
        print(f"\nRunning with {num_iterations} iterations for a formula with {FIXED_CLAUSE_COUNT} clauses...")
        formula_to_solve = deepcopy(formula)
        tracemalloc.start()
        cpu0 = time.process_time()
        for i in range(num_iterations):
            result, _ = solve_sat(deepcopy(formula_to_solve))
            if i == 0:
                print(f"  Iteration 1 of {num_iterations}: Formula Satisfiable: {result}")
        cpu1 = time.process_time()
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        total_cpu_time = cpu1 - cpu0
        peak_memory_kb = peak_mem / 1024
        cpu_times.append(total_cpu_time)
        memory_peaks.append(peak_memory_kb)
        print(f"✔️  Target Iterations: {num_iterations}, Total CPU: {total_cpu_time:.6f}s, Peak Mem: {peak_memory_kb:.2f}KB")
    plt.figure(figsize=(10, 6))
    plt.plot(iteration_values, cpu_times, marker="o", color="blue", label="Total CPU Time (s)")
    plt.title(f"DPLL SAT Solver Benchmark: CPU Time vs Number of Iterations (Fixed Clauses: {FIXED_CLAUSE_COUNT})")
    plt.xlabel("Number of Solver Iterations")
    plt.ylabel("Total CPU Time (seconds)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()
    plt.figure(figsize=(10, 6))
    plt.plot(iteration_values, memory_peaks, marker="^", color="purple", label="Peak Memory (KB)")
    plt.title(f"DPLL SAT Solver Benchmark: Memory Usage vs Number of Iterations (Fixed Clauses: {FIXED_CLAUSE_COUNT})")
    plt.xlabel("Number of Solver Iterations")
    plt.ylabel("Peak Memory (KB)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    benchmark()
